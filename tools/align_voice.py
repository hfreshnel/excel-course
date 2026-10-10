import argparse
import bisect
import difflib
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from video_script import ROW_MARKER_PATTERN, readSpokenItems
from whisper_tools import DEFAULT_MODEL, findFfmpeg, transcribeWords, wordKeys

PLACEHOLDER_SOURCE = "placeholder-sapi"
# 16-bit 48 kHz: read by every tool down the line (Excel take, Remotion), transparent once encoded to AAC
OUTPUT_ARGS = ["-af", "aresample=48000:osf=s16:dither_method=triangular", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le"]
MIN_MATCHED_SHARE = 0.6
# Runs of spoken words absent from the script: a leftover retake, or a misheard number
MIN_EXTRA_RUN_WORDS = 2
FFMPEG_TIMEOUT_SECONDS = 600

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("alignVoice")


def readScriptWords(scriptPath):
	# Script words in spoken order, plus where each marker sits: before word index N, in row R
	words = []
	markers = []
	row = 0
	for kind, value in readSpokenItems(scriptPath):
		if kind == "marker":
			if ROW_MARKER_PATTERN.match(value):
				row += 1
			markers.append({"name": value, "wordIndex": len(words), "row": row})
			continue
		for text in value.split():
			words.append({"text": text, "row": row, "keys": wordKeys(text)})
	return words, markers


def fillGaps(values):
	known = [index for index, value in enumerate(values) if value is not None]
	if not known:
		raise RuntimeError("No script word could be aligned with the transcript")
	for index, value in enumerate(values):
		if value is not None:
			continue
		position = bisect.bisect_left(known, index)
		previous = known[position - 1] if position > 0 else None
		following = known[position] if position < len(known) else None
		if previous is None:
			values[index] = values[following]
		elif following is None:
			values[index] = values[previous]
		else:
			ratio = (index - previous) / (following - previous)
			values[index] = values[previous] + ratio * (values[following] - values[previous])
	return values


def alignScriptWords(scriptWords, spokenWords):
	scriptKeys = []
	scriptOwners = []
	for index, word in enumerate(scriptWords):
		scriptKeys += word["keys"]
		scriptOwners += [index] * len(word["keys"])
	spokenKeys = []
	spokenOwners = []
	for index, word in enumerate(spokenWords):
		keys = wordKeys(word["text"])
		spokenKeys += keys
		spokenOwners += [index] * len(keys)
	starts = [None] * len(scriptWords)
	ends = [None] * len(scriptWords)
	spokenMatched = [False] * len(spokenWords)
	matcher = difflib.SequenceMatcher(None, scriptKeys, spokenKeys, autojunk=False)
	for block in matcher.get_matching_blocks():
		for offset in range(block.size):
			scriptIndex = scriptOwners[block.a + offset]
			spokenIndex = spokenOwners[block.b + offset]
			spoken = spokenWords[spokenIndex]
			spokenMatched[spokenIndex] = True
			if starts[scriptIndex] is None:
				starts[scriptIndex] = spoken["start"]
			ends[scriptIndex] = spoken["end"]
	matched = sum(start is not None for start in starts)
	extras = []
	run = []
	for index, isMatched in enumerate(spokenMatched + [True]):
		if not isMatched:
			run.append(index)
			continue
		if len(run) >= MIN_EXTRA_RUN_WORDS:
			extras.append({"start": spokenWords[run[0]]["start"], "end": spokenWords[run[-1]]["end"], "text": " ".join(spokenWords[k]["text"] for k in run)})
		run = []
	return fillGaps(starts), fillGaps(ends), matched, extras


def placeMarkers(markers, scriptWords, starts, ends):
	# A marker fires at the start of the next word; a marker closing its row fires at the end of the last word said
	times = {}
	for marker in markers:
		index = marker["wordIndex"]
		if index < len(scriptWords) and scriptWords[index]["row"] == marker["row"]:
			times[marker["name"]] = round(starts[index], 3)
		elif index > 0:
			# Whisper word ends may run past the next word's start: a row-closing marker never fires after the next row opens
			end = min(ends[index - 1], starts[index]) if index < len(scriptWords) else ends[index - 1]
			times[marker["name"]] = round(end, 3)
		else:
			times[marker["name"]] = 0.0
	return times


def probeDuration(audioPath):
	command = [findFfmpeg(), "-hide_banner", "-nostats", "-i", str(audioPath), "-map", "0:a:0", "-f", "null", "-"]
	completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=FFMPEG_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"ffmpeg could not read {audioPath}: {completed.stderr.strip()[-400:]}")
	times = [line.split("time=")[1].split()[0] for line in completed.stderr.splitlines() if "time=" in line]
	if not times:
		raise RuntimeError(f"cannot measure the duration of {audioPath}")
	hours, minutes, seconds = times[-1].split(":")
	return round(int(hours) * 3600 + int(minutes) * 60 + float(seconds), 3)


def setAsidePlaceholder(outputDir):
	# The SAPI placeholder of this video is moved, not deleted: older takes and comparisons may still need it
	markersPath = outputDir / "markers.json"
	if not markersPath.is_file():
		return
	try:
		source = json.loads(markersPath.read_text(encoding="utf-8")).get("source")
	except (OSError, ValueError) as error:
		raise RuntimeError(f"{markersPath} is unreadable, not overwriting it: {error}")
	if source != PLACEHOLDER_SOURCE:
		return
	placeholderDir = outputDir.with_name("voice-placeholder")
	if placeholderDir.exists():
		raise RuntimeError(f"{outputDir} holds the placeholder voice but {placeholderDir} already exists: move one of them by hand")
	shutil.move(str(outputDir), str(placeholderDir))
	logger.info("Placeholder voice moved to %s", placeholderDir)


def align(audioPath, scriptPath, outputDir, model, device):
	scriptWords, markers = readScriptWords(scriptPath)
	transcript = transcribeWords(audioPath, model, device)
	spokenWords = [{"text": word["text"], "start": word["start"], "end": word["end"]} for word in transcript["words"]]
	if not spokenWords:
		raise RuntimeError(f"Whisper found no word in {audioPath}")
	starts, ends, matched, extras = alignScriptWords(scriptWords, spokenWords)
	share = matched / len(scriptWords)
	logger.info("Aligned %d of %d script words (%.0f%%)", matched, len(scriptWords), share * 100)
	for extra in extras:
		logger.warning("Words not in the script at %d:%05.2f: \"%s\" (leftover retake or misheard words? listen)", extra["start"] // 60, extra["start"] % 60, extra["text"])
	if share < MIN_MATCHED_SHARE:
		raise RuntimeError(f"only {share:.0%} of the script was found in the recording: wrong script, or the rush was not edited")
	times = placeMarkers(markers, scriptWords, starts, ends)
	setAsidePlaceholder(outputDir)
	outputDir.mkdir(parents=True, exist_ok=True)
	outputAudio = outputDir / "audio.wav"
	command = [findFfmpeg(), "-hide_banner", "-nostats", "-loglevel", "error", "-i", str(audioPath), "-map", "0:a:0", *OUTPUT_ARGS, "-y", str(outputAudio)]
	completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=FFMPEG_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"ffmpeg could not write {outputAudio}: {completed.stderr.strip()}")
	payload = {
		"source": f"whisper-{model}",
		"recording": audioPath.name,
		"script": scriptPath.as_posix(),
		"audio": outputAudio.name,
		"duration": probeDuration(outputAudio),
		"alignment": {"scriptWords": len(scriptWords), "matchedWords": matched, "extraWords": extras},
		"markers": times,
		"words": spokenWords,
	}
	(outputDir / "markers.json").write_text(json.dumps(payload, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
	logger.info("%d markers, %d words, %.1f s of audio -> %s", len(times), len(spokenWords), payload["duration"], outputDir)


def main():
	parser = argparse.ArgumentParser(description="Align the final narration with the script (Whisper word timestamps) and write recordings/voice/audio.wav + markers.json.")
	parser.add_argument("audio", type=Path, help="edited and cleaned narration, e.g. recordings/narration/rush-<date>-edit-clean.wav")
	parser.add_argument("--script", type=Path, help="defaults to <video dir>/script.md")
	parser.add_argument("--output-dir", type=Path, help="defaults to <video dir>/recordings/voice")
	parser.add_argument("--model", default=DEFAULT_MODEL)
	parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
	args = parser.parse_args()
	audioPath = args.audio.resolve()
	videoDir = audioPath.parent.parent.parent
	scriptPath = (args.script or videoDir / "script.md").resolve()
	outputDir = (args.output_dir or videoDir / "recordings" / "voice").resolve()
	try:
		if not scriptPath.is_file():
			raise FileNotFoundError(f"script not found: {scriptPath} (use --script)")
		align(audioPath, scriptPath, outputDir, args.model, args.device)
	except Exception:
		logger.exception("Voice alignment failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
