import argparse
import difflib
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import numpy

from video_script import SENTENCE_PATTERN, readCleanSpokenText
from whisper_tools import DEFAULT_MODEL, decodeAudio, findFfmpeg, transcribeWords, wordKeys

SAMPLE_RATE = 48000
OUTPUT_CODEC = "pcm_f32le"
FRAME_SECONDS = 0.01
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_SECONDS)
# Very short sentences ("Mais 1 quoi ?") match anywhere: they are merged with a neighbour before matching
MIN_UNIT_KEYS = 6
MATCH_SCORE = 2
NEAR_MATCH_SCORE = 1
MISMATCH_SCORE = -1
GAP_SCORE = -1
NEAR_MATCH_RATIO = 0.8
# A take must reach this share of a perfect match. The last complete take wins: a low score usually means Whisper
# misheard a word, while an abandoned take stops before the end of the sentence
TAKE_THRESHOLD = 0.55
MIN_TAKE_COVERAGE = 0.85
# Misheard words at the edge of a take ("La série" for "L'astérisque") are kept if they touch it in time
EDGE_MAX_GAP_SECONDS = 0.8
DOUBTFUL_SCORE = 0.8
RESTART_OVERLAP = 0.6
RESTART_LOOKAHEAD_KEYS = 3
FILLERS = {"euh", "heu", "hum", "bah", "ben", "hein"}
# Silence detection on 10 ms frames: anything close to the room tone is silence
NOISE_FLOOR_PERCENTILE = 10
SPEECH_LEVEL_PERCENTILE = 70
SILENCE_ABOVE_FLOOR_DB = 10.0
SILENCE_BELOW_SPEECH_DB = 20.0
MIN_SILENT_FRAMES = 4
ONSET_SEARCH_BEFORE = 0.35
ONSET_SEARCH_AFTER = 0.05
OFFSET_SEARCH_BEFORE = 0.05
OFFSET_SEARCH_AFTER = 0.35
ONSET_PAD = 0.05
OFFSET_PAD = 0.08
LEAD_ROOM_TONE_SECONDS = 2.5
MIN_LEAD_ROOM_TONE_SECONDS = 0.8
TRAILING_PAUSE_SECONDS = 0.6
INNER_PAUSE_SECONDS = 0.3
DEFAULT_SENTENCE_PAUSE = 0.6
DEFAULT_ROW_PAUSE = 0.9
FADE_SECONDS = 0.008
# Speech the transcript does not account for inside a kept take: Whisper tends to swallow repeated words
HIDDEN_MIN_GAP_SECONDS = 0.5
HIDDEN_MIN_SPEECH_SECONDS = 0.35
LABEL_TEXT_WORDS = 8
ENCODE_TIMEOUT_SECONDS = 600

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("editVoice")


def formatTime(seconds):
	minutes, rest = divmod(max(0.0, seconds), 60)
	return f"{int(minutes)}:{rest:05.2f}"


def buildUnits(scriptPath):
	sentences = []
	for rowIndex, rowText in enumerate(readCleanSpokenText(scriptPath), start=1):
		for match in SENTENCE_PATTERN.finditer(rowText):
			text = match.group().strip()
			if text:
				sentences.append({"row": rowIndex, "text": text, "keys": wordKeys(text)})
	units = []
	for sentence in sentences:
		previous = units[-1] if units else None
		# A short sentence joins the previous one of the same row, or opens a unit that the next sentence completes
		if previous is not None and previous["row"] == sentence["row"] and (len(sentence["keys"]) < MIN_UNIT_KEYS or len(previous["keys"]) < MIN_UNIT_KEYS):
			previous["text"] += " " + sentence["text"]
			previous["keys"] += sentence["keys"]
		else:
			units.append(dict(sentence))
	for index, unit in enumerate(units):
		unit["index"] = index + 1
	return units


def buildTranscriptKeys(words):
	keys = []
	owners = []
	for wordIndex, word in enumerate(words):
		for key in wordKeys(word["text"]):
			keys.append(key)
			owners.append(wordIndex)
	return keys, owners


class KeyScorer:
	def __init__(self):
		self.cache = {}

	def score(self, scriptKey, spokenKey):
		if scriptKey == spokenKey:
			return MATCH_SCORE
		pair = (scriptKey, spokenKey)
		cached = self.cache.get(pair)
		if cached is None:
			near = scriptKey.rstrip("s") == spokenKey.rstrip("s") or (min(len(scriptKey), len(spokenKey)) >= 4 and difflib.SequenceMatcher(None, scriptKey, spokenKey).ratio() >= NEAR_MATCH_RATIO)
			cached = NEAR_MATCH_SCORE if near else MISMATCH_SCORE
			self.cache[pair] = cached
		return cached


def alignmentTable(unitKeys, spokenKeys, limit, scorer):
	# Semi-global alignment: the whole sentence against any stretch of the transcript before `limit`
	rows = [[0] * (limit + 1)]
	substitutions = []
	for scriptKey in unitKeys:
		scores = [scorer.score(scriptKey, spokenKeys[j]) for j in range(limit)]
		substitutions.append(scores)
		previous = rows[-1]
		current = [previous[0] + GAP_SCORE] + [0] * limit
		for j in range(1, limit + 1):
			best = previous[j - 1] + scores[j - 1]
			skipScript = previous[j] + GAP_SCORE
			if skipScript > best:
				best = skipScript
			skipSpoken = current[j - 1] + GAP_SCORE
			if skipSpoken > best:
				best = skipSpoken
			current[j] = best
		rows.append(current)
	return rows, substitutions


def traceback(rows, substitutions, end):
	# Diagonal moves are preferred, so a repeated passage aligns on its latest copy and the earlier one shows up as inserted words
	i = len(rows) - 1
	j = end
	pairs = []
	while i > 0:
		if j > 0 and rows[i][j] == rows[i - 1][j - 1] + substitutions[i - 1][j - 1]:
			pairs.append((i - 1, j - 1, substitutions[i - 1][j - 1]))
			i -= 1
			j -= 1
		elif rows[i][j] == rows[i - 1][j] + GAP_SCORE:
			i -= 1
		else:
			j -= 1
	pairs.reverse()
	# Mismatched words at either end are not part of the take
	while pairs and pairs[0][2] < 0:
		pairs.pop(0)
	while pairs and pairs[-1][2] < 0:
		pairs.pop()
	return pairs


def findTakes(unit, spokenKeys, limit, scorer):
	if limit <= 0:
		return []
	rows, substitutions = alignmentTable(unit["keys"], spokenKeys, limit, scorer)
	finalRow = rows[-1]
	perfect = MATCH_SCORE * len(unit["keys"])
	threshold = TAKE_THRESHOLD * perfect
	candidates = []
	for j in range(1, limit + 1):
		score = finalRow[j]
		if score < threshold:
			continue
		# Local maxima only: trailing inserted words lower the score one step at a time
		if j < limit and finalRow[j + 1] > score:
			continue
		if finalRow[j - 1] > score:
			continue
		pairs = traceback(rows, substitutions, j)
		if pairs:
			coverage = (pairs[-1][0] - pairs[0][0] + 1) / len(unit["keys"])
			candidates.append({"score": score, "ratio": score / perfect, "coverage": coverage, "pairs": pairs, "start": pairs[0][1], "end": pairs[-1][1]})
	takes = []
	for candidate in sorted(candidates, key=lambda item: (item["end"], item["start"])):
		if takes and candidate["start"] <= takes[-1]["end"]:
			if candidate["score"] > takes[-1]["score"]:
				takes[-1] = candidate
			continue
		takes.append(candidate)
	return takes


def selectTakes(units, spokenKeys):
	scorer = KeyScorer()
	limit = len(spokenKeys)
	# Backwards: each sentence keeps its last good take that ends before the take kept for the next sentence
	for unit in reversed(units):
		takes = findTakes(unit, spokenKeys, limit, scorer)
		unit["takeCount"] = len(takes)
		unit["take"] = None
		if takes:
			complete = [take for take in takes if take["coverage"] >= MIN_TAKE_COVERAGE]
			unit["take"] = complete[-1] if complete else max(takes, key=lambda take: take["ratio"])
			limit = unit["take"]["start"]


def extendEdges(units, spokenKeys, owners, words):
	# Script words left unaligned at either end of a take are usually misheard: take as many transcript keys back
	# (or forward) as there are missing script keys, without crossing a neighbouring take or a pause
	kept = [unit for unit in units if unit["take"] is not None]
	for position, unit in enumerate(kept):
		take = unit["take"]
		lowerBound = kept[position - 1]["take"]["end"] + 1 if position > 0 else 0
		upperBound = kept[position + 1]["take"]["start"] - 1 if position + 1 < len(kept) else len(spokenKeys) - 1
		for _ in range(take["pairs"][0][0]):
			candidate = take["start"] - 1
			if candidate < lowerBound or words[owners[take["start"]]]["start"] - words[owners[candidate]]["end"] > EDGE_MAX_GAP_SECONDS:
				break
			take["start"] = candidate
		for _ in range(len(unit["keys"]) - 1 - take["pairs"][-1][0]):
			candidate = take["end"] + 1
			if candidate > upperBound or words[owners[candidate]]["start"] - words[owners[take["end"]]]["end"] > EDGE_MAX_GAP_SECONDS:
				break
			take["end"] = candidate


def classifyInsertions(unit, spokenKeys, owners, words):
	take = unit["take"]
	pairs = take["pairs"]
	alignedSpoken = {j for _, j, _ in pairs}
	cuts = []
	adLibs = []
	run = []
	for j in range(pairs[0][1], pairs[-1][1] + 1):
		if j not in alignedSpoken:
			run.append(j)
			continue
		if run:
			nextScript = next(i for i, spoken, _ in pairs if spoken == j)
			window = set(unit["keys"][max(0, nextScript - 1):nextScript + len(run) + RESTART_LOOKAHEAD_KEYS])
			runKeys = [spokenKeys[k] for k in run]
			fillerOnly = all(key in FILLERS for key in runKeys)
			restart = sum(key in window for key in runKeys) >= RESTART_OVERLAP * len(runKeys)
			firstWord = owners[run[0]]
			lastWord = owners[run[-1]]
			# A word shared with aligned keys (e.g. "44%" -> 44, pour, cent) is never cut
			sharedWord = any(owners[k] == firstWord or owners[k] == lastWord for k in alignedSpoken)
			text = " ".join(words[index]["text"] for index in range(firstWord, lastWord + 1))
			if (fillerOnly or restart) and not sharedWord:
				cuts.append((firstWord, lastWord, text))
			else:
				adLibs.append(text)
			run = []
	return cuts, adLibs


class Envelope:
	def __init__(self, samples):
		frameCount = len(samples) // FRAME_SAMPLES
		frames = samples[:frameCount * FRAME_SAMPLES].reshape(frameCount, FRAME_SAMPLES).astype(numpy.float64)
		self.levels = 10 * numpy.log10(numpy.mean(frames * frames, axis=1) + 1e-12)
		self.floor = float(numpy.percentile(self.levels, NOISE_FLOOR_PERCENTILE))
		speech = float(numpy.percentile(self.levels, SPEECH_LEVEL_PERCENTILE))
		self.threshold = min(self.floor + SILENCE_ABOVE_FLOOR_DB, speech - SILENCE_BELOW_SPEECH_DB)
		self.silent = self.levels < self.threshold
		self.duration = len(samples) / SAMPLE_RATE

	def frame(self, seconds):
		return int(min(max(seconds, 0.0), self.duration) / FRAME_SECONDS)

	def time(self, frame):
		return min(frame * FRAME_SECONDS, self.duration)

	def isSilentRun(self, first, last):
		return first >= 0 and last <= len(self.silent) and last > first and bool(self.silent[first:last].all())

	def quietest(self, start, end):
		first, last = self.frame(start), max(self.frame(end), self.frame(start) + 1)
		return self.time(first + int(numpy.argmin(self.levels[first:last])))

	def onset(self, wordStart, lowerBound):
		# Latest silence of at least MIN_SILENT_FRAMES before the word: speech starts right after it
		first = self.frame(max(lowerBound, wordStart - ONSET_SEARCH_BEFORE))
		for frame in range(self.frame(wordStart + ONSET_SEARCH_AFTER), first + MIN_SILENT_FRAMES - 1, -1):
			if self.isSilentRun(frame - MIN_SILENT_FRAMES, frame):
				return max(lowerBound, self.time(frame) - ONSET_PAD)
		return max(lowerBound, self.quietest(max(lowerBound, wordStart - ONSET_SEARCH_BEFORE), wordStart + ONSET_SEARCH_AFTER))

	def offset(self, wordEnd, upperBound):
		last = self.frame(min(upperBound, wordEnd + OFFSET_SEARCH_AFTER))
		for frame in range(self.frame(wordEnd - OFFSET_SEARCH_BEFORE), last - MIN_SILENT_FRAMES + 1):
			if self.isSilentRun(frame, frame + MIN_SILENT_FRAMES):
				return min(upperBound, self.time(frame) + OFFSET_PAD)
		return min(upperBound, self.quietest(wordEnd - OFFSET_SEARCH_BEFORE, min(upperBound, wordEnd + OFFSET_SEARCH_AFTER)))

	def speechSeconds(self, start, end):
		return float(numpy.count_nonzero(~self.silent[self.frame(start):self.frame(end)])) * FRAME_SECONDS

	def silenceAfter(self, seconds):
		frame = self.frame(seconds)
		end = frame
		while end < len(self.silent) and self.silent[end]:
			end += 1
		return self.time(end) - self.time(frame)

	def silenceBefore(self, seconds):
		frame = self.frame(seconds)
		start = frame
		while start > 0 and self.silent[start - 1]:
			start -= 1
		return self.time(frame) - self.time(start)


def buildSpans(units, words, owners, spokenKeys):
	# A span is a run of transcript words kept together; spans are joined with a shortened pause
	spans = []
	for unit in units:
		take = unit["take"]
		if take is None:
			continue
		cuts, adLibs = classifyInsertions(unit, spokenKeys, owners, words)
		unit["innerCuts"] = [text for _, _, text in cuts]
		unit["adLibs"] = adLibs
		first, last = owners[take["start"]], owners[take["end"]]
		pieceStart = first
		for cutFirst, cutLast, _ in cuts:
			if cutFirst > pieceStart:
				spans.append({"unit": unit, "first": pieceStart, "last": cutFirst - 1, "joinAfter": "inner"})
			pieceStart = cutLast + 1
		spans.append({"unit": unit, "first": pieceStart, "last": last, "joinAfter": "unit"})
	# A sentence with no take keeps whatever was said between its neighbours, so nothing is lost
	for index, unit in enumerate(units):
		if unit["take"] is not None:
			continue
		previousLast = max((span["last"] for span in spans if span["unit"]["index"] < unit["index"]), default=-1)
		nextFirst = min((span["first"] for span in spans if span["unit"]["index"] > unit["index"]), default=len(words))
		if nextFirst - previousLast > 1:
			spans.append({"unit": unit, "first": previousLast + 1, "last": nextFirst - 1, "joinAfter": "unit", "fallback": True})
			unit["fallbackText"] = " ".join(word["text"] for word in words[previousLast + 1:nextFirst])
	spans.sort(key=lambda span: span["first"])
	return spans


def pauseTarget(span, following, settings):
	if span["joinAfter"] == "inner":
		return INNER_PAUSE_SECONDS
	if following is not None and following["unit"]["row"] != span["unit"]["row"]:
		return settings["rowPause"]
	return settings["sentencePause"]


def buildPieces(spans, words, envelope, settings):
	# Word boundaries are snapped to silences, then each join keeps at most the target pause of real room tone
	bounds = []
	for index, span in enumerate(spans):
		lower = bounds[-1][1] if bounds else 0.0
		upper = words[spans[index + 1]["first"]]["start"] if index + 1 < len(spans) else envelope.duration
		start = envelope.onset(words[span["first"]]["start"], lower)
		end = envelope.offset(words[span["last"]]["end"], max(start, upper))
		bounds.append([start, max(start, end)])
	pieces = []
	leadEnd = min(LEAD_ROOM_TONE_SECONDS, envelope.silenceAfter(0.0))
	if leadEnd >= MIN_LEAD_ROOM_TONE_SECONDS:
		pieces.append({"start": 0.0, "end": leadEnd, "label": "room tone"})
	else:
		logger.warning("Only %.2f s of silence at the start of the rush: clean_voice.py may not learn the noise profile", leadEnd)
	for index, span in enumerate(spans):
		start, end = bounds[index]
		following = spans[index + 1] if index + 1 < len(spans) else None
		if index == 0:
			start -= min(envelope.silenceBefore(start), settings["sentencePause"])
			if pieces:
				start = max(start, pieces[-1]["end"])
		if following is None:
			end += min(envelope.silenceAfter(end), TRAILING_PAUSE_SECONDS)
		else:
			nextStart = bounds[index + 1][0]
			target = pauseTarget(span, following, settings)
			contiguous = following["first"] == span["last"] + 1 and not span.get("fallback") and not following.get("fallback")
			if contiguous and nextStart - end <= target:
				end = nextStart
			else:
				# Both pads stay inside the gap, so no audio is ever played twice
				gap = max(0.0, nextStart - end)
				tail = min(envelope.silenceAfter(end), target / 2, gap / 2)
				head = min(envelope.silenceBefore(nextStart), target - tail, gap - tail)
				tail = min(envelope.silenceAfter(end), target - head, gap - head)
				end += tail
				bounds[index + 1][0] = nextStart - head
		text = " ".join(word["text"] for word in words[span["first"]:span["last"] + 1])
		label = f"keep {span['unit']['index']}: {' '.join(text.split()[:LABEL_TEXT_WORDS])}"
		if pieces:
			start = max(start, pieces[-1]["end"])
		if pieces and abs(pieces[-1]["end"] - start) < FRAME_SECONDS / 2 and pieces[-1]["label"] != "room tone":
			pieces[-1]["end"] = end
		else:
			pieces.append({"start": start, "end": end, "label": label})
	for piece in pieces:
		piece["start"] = round(piece["start"], 3)
		piece["end"] = round(piece["end"], 3)
	return pieces


def findHiddenSpeech(spans, words, envelope):
	findings = []
	for span in spans:
		for index in range(span["first"], span["last"]):
			gapStart, gapEnd = words[index]["end"], words[index + 1]["start"]
			if gapEnd - gapStart < HIDDEN_MIN_GAP_SECONDS:
				continue
			speech = envelope.speechSeconds(gapStart, gapEnd)
			if speech >= HIDDEN_MIN_SPEECH_SECONDS:
				findings.append({"unit": span["unit"]["index"], "start": gapStart, "end": gapEnd, "speech": speech, "before": words[index]["text"], "after": words[index + 1]["text"]})
	return findings


def editedTime(seconds, pieces):
	# Position of a rush time in the edited audio, for listening checks
	elapsed = 0.0
	for piece in pieces:
		if seconds < piece["start"]:
			return elapsed
		if seconds <= piece["end"]:
			return elapsed + seconds - piece["start"]
		elapsed += piece["end"] - piece["start"]
	return elapsed


def findCutRegions(pieces, words):
	regions = []
	for previous, following in zip(pieces, pieces[1:]):
		if following["start"] - previous["end"] <= FRAME_SECONDS:
			continue
		text = " ".join(word["text"] for word in words if word["start"] < following["start"] and word["end"] > previous["end"])
		regions.append({"start": previous["end"], "end": following["start"], "text": text})
	return regions


def readLabels(labelsPath):
	pieces = []
	for lineNumber, line in enumerate(labelsPath.read_text(encoding="utf-8-sig").splitlines(), start=1):
		parts = line.split("\t")
		if len(parts) < 3 or not parts[2].startswith(("keep", "room tone")):
			continue
		try:
			start, end = float(parts[0]), float(parts[1])
		except ValueError:
			raise ValueError(f"{labelsPath}:{lineNumber}: invalid label times")
		if end <= start:
			raise ValueError(f"{labelsPath}:{lineNumber}: label ends before it starts")
		pieces.append({"start": start, "end": end, "label": parts[2]})
	if not pieces:
		raise ValueError(f"{labelsPath}: no 'keep' label found")
	pieces.sort(key=lambda piece: piece["start"])
	for previous, following in zip(pieces, pieces[1:]):
		if following["start"] < previous["end"] - FRAME_SECONDS:
			raise ValueError(f"{labelsPath}: labels '{previous['label']}' and '{following['label']}' overlap")
	return pieces


def writeLabels(labelsPath, pieces, cutRegions):
	lines = [f"{piece['start']:.6f}\t{piece['end']:.6f}\t{piece['label']}" for piece in pieces]
	lines += [f"{region['start']:.6f}\t{region['end']:.6f}\tcut: {region['text']}" for region in cutRegions]
	lines.sort(key=lambda line: float(line.split("\t")[0]))
	labelsPath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def renderPieces(samples, pieces, outputPath):
	fadeSamples = int(FADE_SECONDS * SAMPLE_RATE)
	ramp = numpy.linspace(0.0, 1.0, fadeSamples, dtype=numpy.float32)
	chunks = []
	for piece in pieces:
		chunk = samples[int(round(piece["start"] * SAMPLE_RATE)):int(round(piece["end"] * SAMPLE_RATE))].copy()
		if len(chunk) > 2 * fadeSamples:
			# Short fades remove the click of a cut; joins sit in silence, so they are inaudible
			chunk[:fadeSamples] *= ramp
			chunk[-fadeSamples:] *= ramp[::-1]
		chunks.append(chunk)
	edited = numpy.concatenate(chunks)
	command = [findFfmpeg(), "-hide_banner", "-nostats", "-loglevel", "error", "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "-", "-c:a", OUTPUT_CODEC, "-y", str(outputPath)]
	completed = subprocess.run(command, input=edited.tobytes(), capture_output=True, timeout=ENCODE_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"ffmpeg could not write {outputPath}: {completed.stderr.decode('utf-8', 'replace').strip()}")
	return len(edited) / SAMPLE_RATE


def unitStatus(unit):
	if unit["take"] is None:
		return "absente, passage conservé" if unit.get("fallbackText") else "absente"
	notes = []
	if unit["takeCount"] > 1:
		notes.append(f"reprise ({unit['takeCount']} prises, dernière gardée)")
	if unit["take"]["ratio"] < DOUBTFUL_SCORE:
		notes.append("douteuse")
	if unit.get("innerCuts"):
		notes.append("faux départ coupé")
	return ", ".join(notes) or "ok"


def writeReport(reportPath, rushPath, units, words, pieces, cutRegions, hiddenSpeech, sourceDuration, editedDuration, settings, fromLabels):
	def cell(text):
		return text.replace("|", "\\|")

	retaken = sum(1 for unit in units if unit["take"] is not None and unit["takeCount"] > 1)
	missing = [unit for unit in units if unit["take"] is None]
	doubtful = [unit for unit in units if unit["take"] is not None and unit["take"]["ratio"] < DOUBTFUL_SCORE]
	lines = [
		f"# Montage de la voix : {rushPath.name}",
		"",
		f"- Durée du rush : {formatTime(sourceDuration)} ; durée montée : {formatTime(editedDuration)}",
		f"- Phrases : {len(units)} ; reprises : {retaken} ; absentes : {len(missing)} ; douteuses : {len(doubtful)}",
		f"- Passages coupés : {len(cutRegions)} ; pauses maximales : {settings['sentencePause']} s entre phrases, {settings['rowPause']} s entre lignes du script",
		f"- Montage {'repris des repères Audacity' if fromLabels else 'automatique'}",
		"",
	]
	checks = []
	for unit in missing:
		checks.append(f"- Phrase {unit['index']} (ligne {unit['row']}) introuvable : « {unit['text']} »" + (f". Passage conservé tel quel : « {unit['fallbackText']} »" if unit.get("fallbackText") else ""))
	for unit in doubtful:
		checks.append(f"- Phrase {unit['index']} (ligne {unit['row']}) peu ressemblante au script ({unit['take']['ratio']:.0%}) : vérifier à l'écoute")
	for finding in hiddenSpeech:
		checks.append(f"- Phrase {finding['unit']} : {finding['speech']:.1f} s de parole non transcrite entre « {finding['before']} » et « {finding['after']} » (rush {formatTime(finding['start'])}, montage {formatTime(editedTime(finding['start'], pieces))}) : reprise possible, écouter")
	for unit in units:
		for text in unit.get("adLibs", []):
			checks.append(f"- Phrase {unit['index']} : mots hors script conservés « {text} »")
	lines += ["## Points à vérifier", ""] + (checks or ["Aucun."]) + [""]
	lines += ["## Phrases", "", "| # | Ligne | Statut | Gardée (rush) | Ressemblance | Script |", "|---|---|---|---|---|---|"]
	for unit in units:
		take = unit["take"]
		lines.append(f"| {unit['index']} | {unit['row']} | {unitStatus(unit)} | {unit.get('keptAt', '—')} | {f'{take['ratio']:.0%}' if take else '—'} | {cell(unit['text'])} |")
	lines += ["", "## Passages coupés", "", "| Début | Fin | Durée | Transcription |", "|---|---|---|---|"]
	for region in cutRegions:
		lines.append(f"| {formatTime(region['start'])} | {formatTime(region['end'])} | {region['end'] - region['start']:.2f} s | {cell(region['text']) or '(silence)'} |")
	reportPath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
	parser = argparse.ArgumentParser(description="Edit a narration rush: keep the last good take of each script sentence, shorten long pauses, and write the edited audio with a report and Audacity labels.")
	parser.add_argument("rush", type=Path, help="raw recording (m4a, wav...) in <video dir>/recordings/narration")
	parser.add_argument("--script", type=Path, help="defaults to <video dir>/script.md")
	parser.add_argument("--labels", type=Path, help="Audacity label file to apply instead of the automatic edit ('keep' labels are kept, in time order)")
	parser.add_argument("--model", default=DEFAULT_MODEL)
	parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
	parser.add_argument("--sentence-pause", type=float, default=DEFAULT_SENTENCE_PAUSE, help="longest pause kept between sentences (s)")
	parser.add_argument("--row-pause", type=float, default=DEFAULT_ROW_PAUSE, help="longest pause kept between script rows (s)")
	args = parser.parse_args()
	rushPath = args.rush.resolve()
	scriptPath = (args.script or rushPath.parent.parent.parent / "script.md").resolve()
	stem = rushPath.with_name(f"{rushPath.stem}-edit")
	outputPath = stem.with_suffix(".wav")
	labelsPath = stem.with_suffix(".labels.txt")
	settings = {"sentencePause": args.sentence_pause, "rowPause": args.row_pause}
	try:
		if not scriptPath.is_file():
			raise FileNotFoundError(f"script not found: {scriptPath} (use --script)")
		units = buildUnits(scriptPath)
		transcript = transcribeWords(rushPath, args.model, args.device)
		words = transcript["words"]
		if not words:
			raise RuntimeError("Whisper found no word in the rush")
		spokenKeys, owners = buildTranscriptKeys(words)
		selectTakes(units, spokenKeys)
		extendEdges(units, spokenKeys, owners, words)
		for unit in units:
			if unit["take"] is not None:
				unit["keptAt"] = formatTime(words[owners[unit["take"]["start"]]]["start"])
		samples = decodeAudio(rushPath, SAMPLE_RATE)
		envelope = Envelope(samples)
		logger.info("Silence threshold %.1f dBFS (room tone %.1f dBFS)", envelope.threshold, envelope.floor)
		spans = buildSpans(units, words, owners, spokenKeys)
		if args.labels:
			pieces = readLabels(args.labels.resolve())
			logger.info("Applying %d pieces from %s", len(pieces), args.labels)
		else:
			pieces = buildPieces(spans, words, envelope, settings)
		cutRegions = findCutRegions(pieces, words)
		hiddenSpeech = findHiddenSpeech(spans, words, envelope) if not args.labels else []
		editedDuration = renderPieces(samples, pieces, outputPath)
		edit = {
			"rush": rushPath.name,
			"script": scriptPath.as_posix(),
			"transcript": f"{rushPath.stem}.whisper-{args.model}.json",
			"settings": settings,
			"fromLabels": str(args.labels) if args.labels else None,
			"sourceDuration": round(envelope.duration, 3),
			"editedDuration": round(editedDuration, 3),
			"pieces": pieces,
			"units": [{"index": unit["index"], "row": unit["row"], "status": unitStatus(unit), "takeCount": unit["takeCount"], "keptAt": unit.get("keptAt"), "ratio": round(unit["take"]["ratio"], 3) if unit["take"] else None, "text": unit["text"]} for unit in units],
		}
		stem.with_suffix(".json").write_text(json.dumps(edit, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
		if not args.labels:
			writeLabels(labelsPath, pieces, cutRegions)
		writeReport(stem.with_suffix(".report.md"), rushPath, units, words, pieces, cutRegions, hiddenSpeech, envelope.duration, editedDuration, settings, bool(args.labels))
		retaken = sum(1 for unit in units if unit["takeCount"] > 1)
		missing = sum(1 for unit in units if unit["take"] is None)
		logger.info("%d sentences, %d retaken, %d missing; %d cuts; %d spots with untranscribed speech; %s -> %s", len(units), retaken, missing, len(cutRegions), len(hiddenSpeech), formatTime(envelope.duration), formatTime(editedDuration))
		logger.info("Edited audio -> %s (report: %s, labels: %s)", outputPath, stem.with_suffix(".report.md").name, labelsPath.name)
	except Exception:
		logger.exception("Voice edit failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
