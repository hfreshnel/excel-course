import argparse
import difflib
import hashlib
import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy
import soundfile

from align_voice import alignScriptWords, placeMarkers, probeDuration, readScriptWords, setAsidePlaceholder
from clean_voice import LIMITER_HEADROOM_DB, TARGET_LUFS, TARGET_TRUE_PEAK, loudnormMeasure, parseLoudnorm, runFfmpeg
from tts_text import loadLexicon, ttsText
from video_script import readSentences
from whisper_tools import findFfmpeg, transcribeWords, wordKeys

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REFERENCE = REPO_ROOT / "assets" / "voice" / "reference.wav"
MODEL_NAME = "chatterbox-multilingual"
LANGUAGE = "fr"
EXAGGERATION = 0.5
CFG_WEIGHT = 0.5
# Tried in order until a take passes the Whisper check; a seed forced in voice.json is used alone
SEEDS = [1234, 1, 2, 3]
MIN_SIMILARITY = 0.9
# The last sentence of a video must end falling: Chatterbox sometimes rises on the last syllable (+8 st on
# "autres"), which sounds unfinished. Measured with Praat on the final voiced run, against the sentence median.
FINAL_SEEDS = [1234, 1, 2, 3, 4, 5, 6, 7, 8, 9]
FINAL_MAX_PEAK_ST = 1.0
FINAL_MAX_RISE_ST = 3.0
PITCH_FLOOR = 70
PITCH_CEILING = 300
MIN_VOICED_RUN_FRAMES = 5
# The video ends on a long volume fade instead of the usual short one, stretched a little past the last decay
FINAL_FADE = 1.2
FINAL_EXTRA_TAIL = 0.25
MIN_SENTENCE_WORDS = 4
# Whisper stays on the CPU: Chatterbox already takes ~4 GB of the 6 GB GPU
WHISPER_DEVICE = "cpu"
SENTENCE_PAUSE = 0.6
ROW_PAUSE = 0.9
LEAD_SECONDS = 0.5
TAIL_SECONDS = 0.6
# Tail trimming: the model sometimes keeps babbling after the last word (Chatterbox "forcing EOS, long_tail")
SEARCH_BEFORE_END = 0.05
SEARCH_AFTER_END = 0.35
SILENCE_BELOW_SPEECH_DB = 38.0
MIN_SILENT_FRAMES = 4
END_FADE = 0.15
HEAD_SEARCH = 0.3
HEAD_PAD = 0.03
HEAD_FADE = 0.01
# Pauses get pink noise: digital silence sounds like a dropout, and the model's own silence carries a ~430 Hz
# vocoder tone that rings like a bell once repeated in every pause
ROOM_TONE_DBFS = -70.0
CROSSFADE = 0.15
OUTPUT_SAMPLE_RATE = 48000
# Speaking rate: Chatterbox drifts from one sentence to the next (-60 % to +60 % around the median on videos 2 and 3),
# so a normal sentence sounds slow after a fast one. Every sentence is brought towards one target for the whole course,
# in syllables per second of speech (gaps between words capped, pauses excluded).
RATE_TARGET = 5.5
RATE_TOLERANCE = 0.06
# Rubber Band stays transparent on speech within about +-15 %; beyond that other seeds are tried first
MAX_TEMPO_CHANGE = 0.15
RATE_RETRY_DEVIATION = 0.20
MAX_GAP_IN_SPEECH = 0.25
MIN_RATE_SPEECH_SECONDS = 0.8
VOWEL_GROUP_PATTERN = re.compile(r"[aeiouyàâäéèêëîïôöùûüœæ]+")
SYLLABLE_WORD_PATTERN = re.compile(r"[a-zà-ÿœæ]+(?:['’-][a-zà-ÿœæ]+)*")
ELISION_PATTERN = re.compile(r"['’]")
MUTE_ENDING_PATTERN = re.compile(r"(?<=[^aeiouyàâäéèêëîïôöùûüœæ])es?$")
CACHE_DIR_NAME = "voice-tts"
OVERRIDES_NAME = "voice.json"
FFMPEG_TIMEOUT_SECONDS = 600

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logging.getLogger("whisperTools").setLevel(logging.WARNING)
logger = logging.getLogger("synthesizeVoice")


def formatTime(seconds):
	minutes, rest = divmod(max(0.0, seconds), 60)
	return f"{int(minutes)}:{rest:05.2f}"


def fileHash(path):
	return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def loadOverrides(videoDir, sentenceIds):
	path = videoDir / OVERRIDES_NAME
	if not path.is_file():
		return {}, {}
	data = json.loads(path.read_text(encoding="utf-8"))
	seeds = data.get("seeds", {})
	texts = data.get("text", {})
	unknown = [sentenceId for sentenceId in list(seeds) + list(texts) if sentenceId not in sentenceIds]
	if unknown:
		raise ValueError(f"{path}: unknown sentence ids {unknown} (ids are listed in the voice report)")
	if not all(isinstance(seed, int) for seed in seeds.values()) or not all(isinstance(text, str) for text in texts.values()):
		raise ValueError(f"{path}: seeds must be integers and texts strings")
	return seeds, texts


def similarity(scriptText, words):
	# Keyed on the whole transcript: Whisper splits "41,80 €" into "41" and ",80 €"
	spoken = wordKeys(" ".join(word["text"] for word in words))
	return difflib.SequenceMatcher(None, wordKeys(scriptText), spoken, autojunk=False).ratio()


def countSyllables(text):
	# Approximation of spoken French syllables: vowel groups, mute final "e"/"es", silent "u" of "qu"/"gu", elisions
	total = 0
	for word in SYLLABLE_WORD_PATTERN.findall(text.lower()):
		for part in word.split("-"):
			pieces = ELISION_PATTERN.split(part)
			for elided in pieces[:-1]:
				total += max(0, len(VOWEL_GROUP_PATTERN.findall(elided.replace("qu", "k"))) - 1)
			core = re.sub(r"gu(?=[eiéèêy])", "g", pieces[-1].replace("qu", "k"))
			if len(core) > 2:
				core = MUTE_ENDING_PATTERN.sub("", core)
			if core:
				total += max(1, len(VOWEL_GROUP_PATTERN.findall(core)))
	return total


def speechSeconds(words):
	if not words:
		return 0.0
	voiced = sum(max(0.0, word["end"] - word["start"]) for word in words)
	gaps = sum(min(MAX_GAP_IN_SPEECH, max(0.0, following["start"] - word["end"])) for word, following in zip(words, words[1:]))
	return voiced + gaps


def speakingRate(scriptText, spokenText, words):
	seconds = speechSeconds(scriptBounds(scriptText, words))
	if seconds < MIN_RATE_SPEECH_SECONDS:
		return None
	return round(countSyllables(spokenText) / seconds, 2)


def rateDeviation(rate):
	return 0.0 if rate is None else rate / RATE_TARGET - 1


def tempoFor(rate):
	if rate is None or abs(rateDeviation(rate)) <= RATE_TOLERANCE:
		return 1.0
	return round(min(1 + MAX_TEMPO_CHANGE, max(1 - MAX_TEMPO_CHANGE, RATE_TARGET / rate)), 3)


def stretch(piece, sampleRate, tempo, workDir):
	# Rubber Band keeps pitch and formants; tempo < 1 slows the sentence down
	inputPath = workDir / "stretch-in.wav"
	outputPath = workDir / "stretch-out.wav"
	soundfile.write(inputPath, piece, sampleRate, subtype="FLOAT")
	command = [findFfmpeg(), "-hide_banner", "-nostats", "-loglevel", "error", "-i", str(inputPath), "-af", f"rubberband=tempo={tempo}:pitchq=quality:formant=preserved", "-c:a", "pcm_f32le", "-y", str(outputPath)]
	completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=FFMPEG_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"ffmpeg rubberband failed (tempo {tempo}): {completed.stderr.strip()}")
	stretched, stretchedRate = soundfile.read(outputPath, dtype="float32")
	if stretchedRate != sampleRate:
		raise RuntimeError(f"rubberband changed the sample rate ({sampleRate} -> {stretchedRate})")
	expected = len(piece) / tempo
	if abs(len(stretched) - expected) > 0.05 * sampleRate:
		logger.warning("Stretched length %.2f s instead of %.2f s (tempo %s)", len(stretched) / sampleRate, expected / sampleRate, tempo)
	return stretched


class Synthesizer:
	def __init__(self, referencePath):
		self.referencePath = referencePath
		self.model = None

	def load(self):
		if self.model is None:
			import torch
			from chatterbox.mtl_tts import ChatterboxMultilingualTTS
			if not torch.cuda.is_available():
				raise RuntimeError("CUDA is not available: install the CUDA build of PyTorch in .venv-tts (see CLAUDE.md)")
			logger.info("Loading Chatterbox Multilingual on CUDA")
			self.model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
			self.model.prepare_conditionals(str(self.referencePath), exaggeration=EXAGGERATION)
		return self.model

	def generate(self, text, seed):
		import torch
		model = self.load()
		torch.manual_seed(seed)
		torch.cuda.manual_seed_all(seed)
		wav = model.generate(text, language_id=LANGUAGE, exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT)
		return wav.squeeze(0).cpu().numpy().astype(numpy.float32), model.sr


def terminalPitch(wavPath, scriptText, words):
	import parselmouth
	bounded = scriptBounds(scriptText, words)
	if not bounded:
		return None
	audio, sampleRate = soundfile.read(wavPath, dtype="float64")
	# Analysed up to the last script word only: babble after it must not count as the ending
	audio = audio[:int((bounded[-1]["end"] + 0.15) * sampleRate)]
	frequencies = parselmouth.Sound(audio, sampling_frequency=sampleRate).to_pitch_ac(time_step=0.01, pitch_floor=PITCH_FLOOR, pitch_ceiling=PITCH_CEILING).selected_array["frequency"]
	voiced = frequencies > 0
	if not voiced.any():
		return None
	runs = []
	start = None
	for index, isVoiced in enumerate(list(voiced) + [False]):
		if isVoiced and start is None:
			start = index
		elif not isVoiced and start is not None:
			if index - start >= MIN_VOICED_RUN_FRAMES:
				runs.append((start, index))
			start = None
	if not runs:
		return None
	semitones = 12 * numpy.log2(frequencies[runs[-1][0]:runs[-1][1]] / numpy.median(frequencies[voiced]))
	lowest = int(numpy.argmin(semitones))
	peak = float(semitones.max())
	rise = float(semitones[lowest:].max() - semitones[lowest])
	return {"peakSt": round(peak, 1), "riseSt": round(rise, 1), "ok": peak <= FINAL_MAX_PEAK_ST and rise <= FINAL_MAX_RISE_ST}


def synthesizeSentence(sentence, spokenText, seeds, forced, synthesizer, cacheDir, settingsKey, force, final):
	attempts = []
	for seed in seeds:
		key = hashlib.sha256(json.dumps({"settings": settingsKey, "text": spokenText, "seed": seed}, sort_keys=True).encode("utf-8")).hexdigest()[:20]
		wavPath = cacheDir / f"{key}.wav"
		metaPath = cacheDir / f"{key}.json"
		attempt = None
		if metaPath.is_file() and wavPath.is_file() and not force:
			try:
				attempt = json.loads(metaPath.read_text(encoding="utf-8"))
				# Recomputed so that a better comparison (aliases, script fix) applies to cached takes too
				attempt["similarity"] = round(similarity(sentence["text"], attempt["words"]), 3)
				attempt["cached"] = True
			except (OSError, ValueError) as error:
				logger.warning("%s: unreadable cache %s (%s), regenerating", sentence["id"], metaPath.name, error)
		if attempt is None:
			started = time.perf_counter()
			audio, sampleRate = synthesizer.generate(spokenText, seed)
			soundfile.write(wavPath, audio, sampleRate, subtype="FLOAT")
			words = [{"text": word["text"], "start": word["start"], "end": word["end"]} for word in transcribeWords(wavPath, device=WHISPER_DEVICE)["words"]]
			attempt = {"id": sentence["id"], "seed": seed, "spokenText": spokenText, "words": words, "similarity": round(similarity(sentence["text"], words), 3), "seconds": round(time.perf_counter() - started, 1)}
			metaPath.write_text(json.dumps(attempt, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
			attempt["cached"] = False
		attempt["wav"] = wavPath
		attempt["rate"] = speakingRate(sentence["text"], spokenText, attempt["words"])
		rateOk = abs(rateDeviation(attempt["rate"])) <= RATE_RETRY_DEVIATION
		attempt["terminal"] = terminalPitch(wavPath, sentence["text"], attempt["words"]) if final else None
		terminalOk = not final or (attempt["terminal"] is not None and attempt["terminal"]["ok"])
		attempts.append(attempt)
		ending = f", ending peak {attempt['terminal']['peakSt']:+.1f} st rise {attempt['terminal']['riseSt']:.1f} st" if attempt["terminal"] else ""
		rateText = f", rate {attempt['rate']:.2f} syl/s ({rateDeviation(attempt['rate']):+.0%})" if attempt["rate"] is not None else ""
		logger.info("%-5s seed %-5d similarity %.2f%s%s%s", sentence["id"], seed, attempt["similarity"], rateText, ending, " (cached)" if attempt["cached"] else f" ({attempt['seconds']} s)")
		if forced or (attempt["similarity"] >= MIN_SIMILARITY and terminalOk and rateOk):
			break

	# For the last sentence a falling ending outranks everything; then a take that passes the Whisper check,
	# then the rate closest to the target (it is stretched afterwards, within limits), then similarity
	def rank(item):
		passes = item["similarity"] >= MIN_SIMILARITY
		return (not final or bool(item["terminal"] and item["terminal"]["ok"]), passes, -abs(rateDeviation(item["rate"])) if passes else 0.0, item["similarity"])

	best = max(attempts, key=rank)
	best["attempts"] = len(attempts)
	return best


def frameLevels(audio, frame):
	frames = audio[:len(audio) // frame * frame].reshape(-1, frame).astype(numpy.float64)
	return 10 * numpy.log10(numpy.mean(frames * frames, axis=1) + 1e-12)


def scriptBounds(scriptText, words):
	# First and last transcript words that belong to the script: model babble ("bon ?", "Ah !") is left outside
	scriptKeys = wordKeys(scriptText)
	spokenKeys = []
	owners = []
	for index, word in enumerate(words):
		keys = wordKeys(word["text"])
		spokenKeys += keys
		owners += [index] * len(keys)
	matched = [owners[block.b + offset] for block in difflib.SequenceMatcher(None, scriptKeys, spokenKeys, autojunk=False).get_matching_blocks() for offset in range(block.size)]
	if not matched:
		return words
	return words[min(matched):max(matched) + 1]


def trimSentence(audio, sampleRate, words, final):
	# Cut where the voice has really decayed after the last word, then fade; the head keeps a short lead-in
	frame = sampleRate // 100
	levels = frameLevels(audio, frame)
	if not len(levels) or not words:
		return audio, 0.0
	threshold = numpy.percentile(levels, 70) - SILENCE_BELOW_SPEECH_DB
	lastEnd = words[-1]["end"]
	first = max(0, int((lastEnd - SEARCH_BEFORE_END) * 100))
	last = min(len(levels), int((lastEnd + SEARCH_AFTER_END) * 100))
	cutFrame = len(levels)
	for index in range(first, last - MIN_SILENT_FRAMES + 1):
		if (levels[index:index + MIN_SILENT_FRAMES] < threshold).all():
			cutFrame = index
			break
	else:
		if first < last:
			cutFrame = first + int(numpy.argmin(levels[first:last]))
	end = min(len(audio), int((cutFrame / 100 + END_FADE + (FINAL_EXTRA_TAIL if final else 0.0)) * sampleRate))
	firstStart = words[0]["start"]
	headFrame = int(firstStart * 100)
	startFrame = max(0, headFrame - int(HEAD_SEARCH * 100))
	for index in range(headFrame, startFrame + MIN_SILENT_FRAMES - 1, -1):
		if (levels[max(0, index - MIN_SILENT_FRAMES):index] < threshold).all():
			startFrame = index
			break
	start = max(0, int((startFrame / 100 - HEAD_PAD) * sampleRate))
	piece = audio[start:end].copy()
	fade = min(int((FINAL_FADE if final else END_FADE) * sampleRate), len(piece))
	piece[-fade:] *= (0.5 + 0.5 * numpy.cos(numpy.linspace(0, numpy.pi, fade))).astype(numpy.float32)
	headFade = min(int(HEAD_FADE * sampleRate), len(piece))
	piece[:headFade] *= numpy.linspace(0, 1, headFade, dtype=numpy.float32)
	return piece, start / sampleRate


def pinkNoise(length, rng):
	spectrum = numpy.fft.rfft(rng.standard_normal(length))
	spectrum[1:] /= numpy.sqrt(numpy.arange(1, len(spectrum)))
	noise = numpy.fft.irfft(spectrum, length)
	return (noise / numpy.sqrt(numpy.mean(noise ** 2)) * 10 ** (ROOM_TONE_DBFS / 20)).astype(numpy.float32)


def assemble(takes, sampleRate):
	# Each take: trimmed audio, words relative to it, and the pause that follows it
	rng = numpy.random.default_rng(0)
	cross = int(CROSSFADE * sampleRate)
	ramp = numpy.sin(numpy.linspace(0, numpy.pi / 2, cross)).astype(numpy.float32)
	total = int(LEAD_SECONDS * sampleRate) + sum(len(take["audio"]) + int(take["pauseAfter"] * sampleRate) for take in takes) + 2 * cross
	output = numpy.zeros(total, dtype=numpy.float32)
	gaps = [(0, int(LEAD_SECONDS * sampleRate))]
	position = int(LEAD_SECONDS * sampleRate)
	words = []
	for take in takes:
		take["start"] = position / sampleRate
		output[position:position + len(take["audio"])] += take["audio"]
		words += [{"text": word["text"], "start": round(word["start"] + take["start"], 3), "end": round(word["end"] + take["start"], 3)} for word in take["words"]]
		position += len(take["audio"])
		pause = int(take["pauseAfter"] * sampleRate)
		gaps.append((position, position + pause))
		position += pause
	for gapStart, gapEnd in gaps:
		# The noise bed overlaps the voice by CROSSFADE on both sides, faded in and out
		bedStart = max(0, gapStart - cross)
		bedEnd = min(position, gapEnd + cross)
		bed = pinkNoise(bedEnd - bedStart, rng)
		edge = min(cross, len(bed) // 2)
		if gapStart > 0:
			bed[:edge] *= ramp[:edge]
		if gapEnd < position:
			bed[-edge:] *= ramp[::-1][-edge:]
		output[bedStart:bedEnd] += bed
	return output[:position], words


def renderFinal(assembledPath, outputPath):
	ffmpeg = findFfmpeg()
	measured = parseLoudnorm(runFfmpeg(ffmpeg, assembledPath, loudnormMeasure()))
	gainDb = TARGET_LUFS - float(measured["input_i"])
	limit = 10 ** ((TARGET_TRUE_PEAK - LIMITER_HEADROOM_DB) / 20)
	filters = f"volume={gainDb:.2f}dB,alimiter=limit={limit:.4f}:level=false:latency=true,aresample={OUTPUT_SAMPLE_RATE}:osf=s16:dither_method=triangular"
	command = [ffmpeg, "-hide_banner", "-nostats", "-loglevel", "error", "-i", str(assembledPath), "-af", filters, "-ar", str(OUTPUT_SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s16le", "-y", str(outputPath)]
	completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=FFMPEG_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"ffmpeg could not write {outputPath}: {completed.stderr.strip()}")
	return gainDb


def writeReport(reportPath, scriptPath, takes, extras, duration):
	def cell(text):
		return text.replace("|", "\\|")

	flagged = [take for take in takes if take["similarity"] < MIN_SIMILARITY]
	lines = [
		f"# Voix de synthèse : {scriptPath.parent.name}",
		"",
		f"- Durée : {formatTime(duration)} ; phrases : {len(takes)} ; sous le seuil de ressemblance ({MIN_SIMILARITY:.0%}) : {len(flagged)}",
		f"- Corriger une phrase : `{OVERRIDES_NAME}` du dossier de la vidéo, `\"seeds\": {{\"<id>\": <graine>}}` pour une autre prise, `\"text\": {{\"<id>\": \"…\"}}` pour forcer le texte envoyé au modèle",
		"",
		"## Points à vérifier",
		"",
	]
	checks = [f"- {take['id']} ({formatTime(take['start'])}) : ressemblance {take['similarity']:.0%} après {take['attempts']} essai(s), Whisper entend « {' '.join(word['text'] for word in take['words'])} »" for take in flagged]
	checks += [f"- {formatTime(extra['start'])} : mots hors script « {extra['text']} »" for extra in extras]
	checks += [f"- {take['id']} ({formatTime(take['start'])}) : débit {take['rate']:.2f} syllabes/s ({rateDeviation(take['rate']):+.0%} de la cible {RATE_TARGET}), encore à {rateDeviation(take['rate'] * take['tempo']):+.0%} après étirement limité à ±{MAX_TEMPO_CHANGE:.0%}" for take in takes if take["rate"] is not None and abs(rateDeviation(take["rate"] * take["tempo"])) > RATE_TOLERANCE]
	checks += [f"- {take['id']} (dernière phrase) : fin montante après {take['attempts']} essai(s), pic {take['terminal']['peakSt']:+.1f} demi-tons, remontée {take['terminal']['riseSt']:.1f} : écouter, changer la graine dans `{OVERRIDES_NAME}`" for take in takes if take.get("terminal") and not take["terminal"]["ok"]]
	lines += (checks or ["Aucun."]) + ["", "## Phrases", "", "| Id | Début | Graine | Essais | Ressemblance | Débit (syl/s) | Tempo | Texte envoyé au modèle |", "|---|---|---|---|---|---|---|---|"]
	for take in takes:
		rate = f"{take['rate']:.2f}" if take["rate"] is not None else "—"
		lines.append(f"| {take['id']} | {formatTime(take['start'])} | {take['seed']} | {take['attempts']} | {take['similarity']:.0%} | {rate} | {take['tempo']:.3f} | {cell(take['spokenText'])} |")
	reportPath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def synthesize(scriptPath, referencePath, force):
	videoDir = scriptPath.parent
	cacheDir = videoDir / "recordings" / CACHE_DIR_NAME
	outputDir = videoDir / "recordings" / "voice"
	cacheDir.mkdir(parents=True, exist_ok=True)
	sentences = readSentences(scriptPath, MIN_SENTENCE_WORDS)
	if not sentences:
		raise RuntimeError(f"{scriptPath}: no spoken text")
	seedOverrides, textOverrides = loadOverrides(videoDir, {sentence["id"] for sentence in sentences})
	lexicon = loadLexicon(videoDir.parent)
	settingsKey = {"model": MODEL_NAME, "language": LANGUAGE, "reference": fileHash(referencePath), "exaggeration": EXAGGERATION, "cfgWeight": CFG_WEIGHT}
	synthesizer = Synthesizer(referencePath)
	takes = []
	for index, sentence in enumerate(sentences):
		spokenText = textOverrides.get(sentence["id"]) or ttsText(sentence["text"], lexicon)
		forced = sentence["id"] in seedOverrides
		# A question may rise at the end: only a closing statement is checked
		final = index == len(sentences) - 1 and not sentence["text"].rstrip().endswith("?")
		seeds = [seedOverrides[sentence["id"]]] if forced else (FINAL_SEEDS if final else SEEDS)
		take = synthesizeSentence(sentence, spokenText, seeds, forced, synthesizer, cacheDir, settingsKey, force, final)
		audio, sampleRate = soundfile.read(take["wav"], dtype="float32")
		piece, offset = trimSentence(audio, sampleRate, scriptBounds(sentence["text"], take["words"]), index == len(sentences) - 1)
		following = sentences[index + 1] if index + 1 < len(sentences) else None
		pauseAfter = TAIL_SECONDS if following is None else (ROW_PAUSE if following["row"] != sentence["row"] else SENTENCE_PAUSE)
		# Babble cut off after the last script word must not reach markers.json (start past the cut, end before start)
		pieceSeconds = len(piece) / sampleRate
		words = [{"text": word["text"], "start": max(0.0, word["start"] - offset), "end": min(pieceSeconds, word["end"] - offset)} for word in take["words"] if word["end"] > offset and word["start"] - offset < pieceSeconds]
		tempo = tempoFor(take["rate"])
		if tempo != 1.0:
			piece = stretch(piece, sampleRate, tempo, cacheDir)
			words = [{"text": word["text"], "start": word["start"] / tempo, "end": word["end"] / tempo} for word in words]
			logger.info("%-5s rate %.2f syl/s stretched by tempo %.3f", sentence["id"], take["rate"], tempo)
		take["tempo"] = tempo
		takes.append({**take, "audio": piece, "sampleRate": sampleRate, "words": words, "pauseAfter": pauseAfter})
	sampleRate = takes[0]["sampleRate"]
	if any(take["sampleRate"] != sampleRate for take in takes):
		raise RuntimeError("sentence takes have different sample rates")
	assembled, spokenWords = assemble(takes, sampleRate)
	assembledPath = cacheDir / "assembled.wav"
	soundfile.write(assembledPath, assembled, sampleRate, subtype="FLOAT")
	scriptWords, markers = readScriptWords(scriptPath)
	starts, ends, matched, extras = alignScriptWords(scriptWords, spokenWords)
	logger.info("Aligned %d of %d script words (%.0f%%)", matched, len(scriptWords), matched / len(scriptWords) * 100)
	setAsidePlaceholder(outputDir)
	outputDir.mkdir(parents=True, exist_ok=True)
	outputAudio = outputDir / "audio.wav"
	gainDb = renderFinal(assembledPath, outputAudio)
	duration = probeDuration(outputAudio)
	payload = {
		"source": MODEL_NAME,
		"recording": "synthesized",
		"script": scriptPath.as_posix(),
		"reference": referencePath.name,
		"audio": outputAudio.name,
		"duration": duration,
		"alignment": {"scriptWords": len(scriptWords), "matchedWords": matched, "extraWords": extras},
		"markers": placeMarkers(markers, scriptWords, starts, ends),
		"words": spokenWords,
		"sentences": [{"id": take["id"], "seed": take["seed"], "start": round(take["start"], 3), "similarity": take["similarity"], "rate": take["rate"], "tempo": take["tempo"]} for take in takes],
	}
	(outputDir / "markers.json").write_text(json.dumps(payload, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
	writeReport(outputDir / "voice.report.md", scriptPath, takes, extras, duration)
	flagged = sum(take["similarity"] < MIN_SIMILARITY for take in takes)
	logger.info("%d sentences (%d below %.0f%% similarity), %s of audio, gain %+.1f dB -> %s", len(takes), flagged, MIN_SIMILARITY * 100, formatTime(duration), gainDb, outputDir)


def main():
	parser = argparse.ArgumentParser(description="Synthesize the narration of a video with Chatterbox (cloned voice), check every sentence with Whisper, and write recordings/voice/audio.wav + markers.json.")
	parser.add_argument("script", type=Path, help="video script, e.g. exercises/exercise-1/video-03/script.md")
	parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE, help="voice to clone (defaults to assets/voice/reference.wav)")
	parser.add_argument("--force", action="store_true", help="ignore cached sentence takes")
	args = parser.parse_args()
	try:
		scriptPath = args.script.resolve()
		referencePath = args.reference.resolve()
		if not scriptPath.is_file():
			raise FileNotFoundError(scriptPath)
		if not referencePath.is_file():
			raise FileNotFoundError(f"voice reference not found: {referencePath}")
		synthesize(scriptPath, referencePath, args.force)
	except Exception:
		logger.exception("Voice synthesis failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
