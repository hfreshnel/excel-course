import argparse
import bisect
import difflib
import json
import logging
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

from video_script import MARKER_PATTERN, SPOKEN_COLUMN_INDEX, readRows, stripMarkers

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSITING_DIR = REPO_ROOT / "compositing"
FPS = 30
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
CARD_LEAD_SECONDS = 0.35
CARD_HOLD_SECONDS = 0.9
DICTATION_START_PATTERN = re.compile(r"saisissez\s*:?\s*", re.IGNORECASE)
DICTATION_END_PATTERN = re.compile(r",\s*puis\b|\.(?=\s|$)")
WORD_PATTERN = re.compile(r"\S+")
NORMALIZE_PATTERN = re.compile(r"[^\w]+")
FORMULA_TOKEN_PATTERN = re.compile(r"""
	(?P<string>"[^"]*")
	|(?P<number>\d+(?:,\d+)?%?)
	|(?P<name>[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_.]*)
	|(?P<operator><>|<=|>=|[=+\-*/^&<>])
	|(?P<paren>[()])
	|(?P<separator>[;:])
""", re.VERBOSE)
TYPED_EVENT_TYPES = {"formula"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("renderLesson")


def normalizeWord(word):
	return NORMALIZE_PATTERN.sub("", word.lower())


def readScriptWords(scriptPath):
	rows = []
	for row in readRows(scriptPath):
		raw = row["cells"][SPOKEN_COLUMN_INDEX]
		clean = stripMarkers(raw)
		# Marker offsets are measured in the cleaned text, where they bound the dictation search
		markerOffsets = {match.group(1): len(stripMarkers(raw[:match.start()])) for match in MARKER_PATTERN.finditer(raw)}
		words = [(match.start(), match.group()) for match in WORD_PATTERN.finditer(clean)]
		rows.append({"clean": clean, "words": words, "markers": markerOffsets})
	return rows


def alignWordTimes(rows, audioWords):
	# Sequence alignment tolerates transcription differences (Whisper) as well as the exact SAPI words
	scriptWords = [word for row in rows for _, word in row["words"]]
	scriptKeys = [normalizeWord(word) for word in scriptWords]
	audioKeys = [normalizeWord(word["text"]) for word in audioWords]
	matcher = difflib.SequenceMatcher(None, scriptKeys, audioKeys, autojunk=False)
	times = [None] * len(scriptWords)
	for block in matcher.get_matching_blocks():
		for offset in range(block.size):
			times[block.a + offset] = audioWords[block.b + offset]["start"]
	matchedCount = sum(time is not None for time in times)
	logger.info("Aligned %d of %d script words to audio words", matchedCount, len(scriptWords))
	# Unmatched words are interpolated between their matched neighbours
	known = [index for index, time in enumerate(times) if time is not None]
	if not known:
		raise RuntimeError("No script word could be aligned with the audio words")
	for index in range(len(times)):
		if times[index] is not None:
			continue
		position = bisect.bisect_left(known, index)
		previous = known[position - 1] if position > 0 else None
		following = known[position] if position < len(known) else None
		if previous is None:
			times[index] = times[following]
		elif following is None:
			times[index] = times[previous]
		else:
			ratio = (index - previous) / (following - previous)
			times[index] = times[previous] + ratio * (times[following] - times[previous])
	wordTimes = []
	cursor = 0
	for row in rows:
		wordTimes.append(times[cursor:cursor + len(row["words"])])
		cursor += len(row["words"])
	return wordTimes


def tokenizeFormula(formula):
	tokens = []
	position = 0
	for match in FORMULA_TOKEN_PATTERN.finditer(formula):
		skipped = formula[position:match.start()]
		if skipped.strip():
			raise ValueError(f"cannot tokenize '{skipped}' in {formula}")
		tokens.append({"text": match.group(), "kind": match.lastgroup})
		position = match.end()
	if formula[position:].strip():
		raise ValueError(f"cannot tokenize '{formula[position:]}' in {formula}")
	return tokens


def findMarkerRow(rows, markerName):
	for rowIndex, row in enumerate(rows):
		if markerName in row["markers"]:
			return rowIndex
	raise KeyError(f"marker '{markerName}' not found in the script")


def dictationSegments(row, event):
	clean = row["clean"]
	if "dictationFrom" in event:
		start = row["markers"][event["dictationFrom"]]
	else:
		limit = row["markers"][event["at"]]
		matches = list(DICTATION_START_PATTERN.finditer(clean, 0, limit))
		if not matches:
			raise ValueError(f"no 'saisissez' before marker '{event['at']}': add \"dictationFrom\" to the event")
		start = matches[-1].end()
	endMatch = DICTATION_END_PATTERN.search(clean, start)
	end = endMatch.start() if endMatch else len(clean)
	segments = []
	cursor = start
	for part in clean[start:end].split(","):
		leading = len(part) - len(part.lstrip())
		if part.strip():
			segments.append({"text": part.strip(), "offset": cursor + leading})
		cursor += len(part) + 1
	return segments


def segmentTime(row, rowTimes, offset):
	for wordIndex, (wordOffset, _) in enumerate(row["words"]):
		if wordOffset >= offset:
			return rowTimes[wordIndex]
	return rowTimes[-1]


def buildTypingCards(rows, wordTimes, timeline, logByIndex, leadIn):
	cards = []
	for index, event in enumerate(timeline["events"]):
		if event["type"] not in TYPED_EVENT_TYPES:
			continue
		entry = logByIndex.get(index)
		if entry is None or entry.get("status") != "ok":
			logger.warning("Formula event %d has no successful log entry, skipped", index)
			continue
		tokens = tokenizeFormula(event["formula"])
		rowIndex = findMarkerRow(rows, event["at"])
		segments = dictationSegments(rows[rowIndex], event)
		if len(segments) != len(tokens):
			raise ValueError(f"event {index} ({event['target']}): {len(tokens)} formula tokens {[t['text'] for t in tokens]} but {len(segments)} dictated segments {[s['text'] for s in segments]}")
		for token, segment in zip(tokens, segments):
			token["time"] = round(segmentTime(rows[rowIndex], wordTimes[rowIndex], segment["offset"]) + leadIn, 3)
			token["spoken"] = segment["text"]
		commitTime = entry["plannedTime"] + leadIn
		cards.append({
			"label": event["target"],
			"tokens": tokens,
			"start": round(tokens[0]["time"] - CARD_LEAD_SECONDS, 3),
			"commit": round(commitTime, 3),
			"end": round(commitTime + CARD_HOLD_SECONDS, 3),
			"targetRect": entry["rects"][0],
		})
		logger.info("Card %s: %s", event["target"], " ".join(f"{t['text']}@{t['time']:.2f}" for t in tokens))
	return cards


def buildComposition(takeDir):
	videoDir = takeDir.parent.parent
	log = json.loads((takeDir / "log.json").read_text(encoding="utf-8"))
	timeline = json.loads((videoDir / "timeline.json").read_text(encoding="utf-8"))
	voice = json.loads((videoDir / "recordings" / "voice" / "markers.json").read_text(encoding="utf-8"))
	if not voice.get("words"):
		raise RuntimeError("markers.json has no word timings: regenerate the voice")
	leadIn = log["leadIn"]
	rows = readScriptWords(videoDir / "script.md")
	wordTimes = alignWordTimes(rows, voice["words"])
	logByIndex = {entry["index"]: entry for entry in log["events"]}
	highlights = [
		{"start": round(entry["plannedTime"] + leadIn, 3), "end": round(entry["plannedEnd"] + leadIn, 3), "rects": entry["rects"]}
		for entry in log["events"] if entry["type"] == "highlight" and entry.get("status") == "ok"
	]
	area = log["captureArea"]
	shutil.copyfile(log["audio"], takeDir / "audio.wav")
	return {
		"fps": FPS,
		"width": OUTPUT_WIDTH,
		"height": OUTPUT_HEIGHT,
		"durationInFrames": math.ceil(log["captureDuration"] * FPS),
		"capture": {"src": log["capture"], "width": area["w"], "height": area["h"], "offsetY": (OUTPUT_HEIGHT - area["h"]) // 2},
		"audio": {"src": "audio.wav", "delay": leadIn},
		"highlights": highlights,
		"typingCards": buildTypingCards(rows, wordTimes, timeline, logByIndex, leadIn),
	}


def render(takeDir, outputPath, concurrency):
	npx = shutil.which("npx.cmd") or shutil.which("npx")
	if npx is None:
		raise FileNotFoundError("npx not found: install Node.js")
	outputPath.parent.mkdir(parents=True, exist_ok=True)
	command = [npx, "remotion", "render", "src/index.ts", "ExcelLesson", str(outputPath), f"--props={takeDir / 'composition.json'}", f"--public-dir={takeDir}", f"--concurrency={concurrency}"]
	logger.info("Rendering: %s", " ".join(command))
	subprocess.run(command, cwd=COMPOSITING_DIR, check=True)
	logger.info("Video ready: %s", outputPath)


def main():
	parser = argparse.ArgumentParser(description="Build the compositing data of a take (highlights, typing cards) and render it with Remotion.")
	parser.add_argument("take", type=Path, help="take directory containing log.json and capture.mp4")
	parser.add_argument("--output", type=Path, help="defaults to <video dir>/renders/lesson-<take>.mp4")
	parser.add_argument("--data-only", action="store_true", help="write composition.json without rendering")
	parser.add_argument("--concurrency", type=int, default=4)
	args = parser.parse_args()
	takeDir = args.take.resolve()
	outputPath = (args.output or takeDir.parent.parent / "renders" / f"lesson-{takeDir.name}.mp4").resolve()
	try:
		composition = buildComposition(takeDir)
		(takeDir / "composition.json").write_text(json.dumps(composition, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
		logger.info("%d highlights, %d typing cards -> %s", len(composition["highlights"]), len(composition["typingCards"]), takeDir / "composition.json")
		if not args.data_only:
			render(takeDir, outputPath, args.concurrency)
	except Exception:
		logger.exception("Lesson render failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
