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

from video_script import MARKER_PATTERN, POSE_ID_PATTERN, POSE_MARKER_PATTERN, SPOKEN_COLUMN_INDEX, readRows, stripMarkers

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSITING_DIR = REPO_ROOT / "compositing"
AVATAR_DIR = REPO_ROOT / "assets" / "avatar" / "normalized"
AVATAR_HEIGHT = 420
AVATAR_LEFT = 24
AVATAR_DEFAULT_POSE = "neutral"
# A pose outlives the last word of its sentence a little, without overlapping the next word
POSE_HOLD_SECONDS = 0.3
POSE_MERGE_GAP_SECONDS = 1.5
NEUTRAL_MIN_SECONDS = 1.0
SENTENCE_END_PATTERN = re.compile(r"[.!?…](?=\s|$)")
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
		poses = []
		for match in POSE_MARKER_PATTERN.finditer(raw):
			if not POSE_ID_PATTERN.match(match.group(1)):
				raise ValueError(f"{scriptPath}:{row['lineNumber']}: invalid pose id '{match.group(1)}' (lowercase kebab-case expected)")
			poses.append((len(stripMarkers(raw[:match.start()])), match.group(1)))
		words = [(match.start(), match.group()) for match in WORD_PATTERN.finditer(clean)]
		rows.append({"lineNumber": row["lineNumber"], "clean": clean, "words": words, "markers": markerOffsets, "poses": poses})
	return rows


def fillGaps(values):
	# Unmatched words are interpolated between their matched neighbours
	known = [index for index, value in enumerate(values) if value is not None]
	if not known:
		raise RuntimeError("No script word could be aligned with the audio words")
	for index in range(len(values)):
		if values[index] is not None:
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


def splitByRow(rows, values):
	result = []
	cursor = 0
	for row in rows:
		result.append(values[cursor:cursor + len(row["words"])])
		cursor += len(row["words"])
	return result


def alignWordTimes(rows, audioWords):
	# Sequence alignment tolerates transcription differences (Whisper) as well as the exact SAPI words
	scriptWords = [word for row in rows for _, word in row["words"]]
	scriptKeys = [normalizeWord(word) for word in scriptWords]
	audioKeys = [normalizeWord(word["text"]) for word in audioWords]
	matcher = difflib.SequenceMatcher(None, scriptKeys, audioKeys, autojunk=False)
	starts = [None] * len(scriptWords)
	ends = [None] * len(scriptWords)
	for block in matcher.get_matching_blocks():
		for offset in range(block.size):
			audioWord = audioWords[block.b + offset]
			starts[block.a + offset] = audioWord["start"]
			ends[block.a + offset] = audioWord.get("end", audioWord["start"])
	matchedCount = sum(start is not None for start in starts)
	logger.info("Aligned %d of %d script words to audio words", matchedCount, len(scriptWords))
	return splitByRow(rows, fillGaps(starts)), splitByRow(rows, fillGaps(ends))


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


def buildAvatar(takeDir):
	manifestPath = AVATAR_DIR / "manifest.json"
	if not manifestPath.exists():
		logger.warning("No avatar manifest at %s (run tools/normalize_avatar.py): rendering without avatar", manifestPath)
		return None
	manifest = json.loads(manifestPath.read_text(encoding="utf-8"))
	if AVATAR_DEFAULT_POSE not in manifest["poses"]:
		raise ValueError(f"avatar pose '{AVATAR_DEFAULT_POSE}' missing from {manifestPath}")
	# Remotion serves static files from the take directory (--public-dir), so the poses are copied there
	targetDir = takeDir / "avatar"
	targetDir.mkdir(exist_ok=True)
	poses = {}
	for poseId, pose in manifest["poses"].items():
		shutil.copyfile(AVATAR_DIR / pose["src"], targetDir / pose["src"])
		poses[poseId] = f"avatar/{pose['src']}"
	return {
		"poses": poses,
		"imageWidth": manifest["width"],
		"imageHeight": manifest["height"],
		"height": AVATAR_HEIGHT,
		"left": AVATAR_LEFT,
		"defaultPose": AVATAR_DEFAULT_POSE,
		"cues": [],
	}


def buildPoseCues(rows, wordStarts, wordEnds, leadIn, availablePoses):
	unknown = [f"line {row['lineNumber']}: {pose}" for row in rows for _, pose in row["poses"] if pose not in availablePoses]
	if unknown:
		raise ValueError(f"unknown avatar poses ({', '.join(unknown)}); available: {', '.join(sorted(availablePoses))}")
	globalStarts = [start for rowStarts in wordStarts for start in rowStarts]
	rowFirstIndex = []
	cursor = 0
	for row in rows:
		rowFirstIndex.append(cursor)
		cursor += len(row["words"])
	intervals = []
	for rowIndex, row in enumerate(rows):
		for markerOffset, pose in row["poses"]:
			wordIndices = [index for index, (offset, _) in enumerate(row["words"]) if offset >= markerOffset]
			if not wordIndices:
				logger.warning("Line %d: pose '%s' is not followed by any word, skipped", row["lineNumber"], pose)
				continue
			sentenceEnd = SENTENCE_END_PATTERN.search(row["clean"], markerOffset)
			endOffset = sentenceEnd.start() if sentenceEnd else len(row["clean"])
			lastWord = max([index for index in wordIndices if row["words"][index][0] < endOffset] or [wordIndices[0]])
			start = wordStarts[rowIndex][wordIndices[0]]
			end = wordEnds[rowIndex][lastWord] + POSE_HOLD_SECONDS
			nextGlobal = rowFirstIndex[rowIndex] + lastWord + 1
			if nextGlobal < len(globalStarts):
				end = min(end, globalStarts[nextGlobal])
			intervals.append({"pose": pose, "start": start + leadIn, "end": max(start, end) + leadIn})
	intervals.sort(key=lambda interval: interval["start"])
	# A pose lasts until the end of its sentence, unless the next pose starts earlier; then back to the default pose.
	# The same pose repeated on the next sentence is held through the pause instead of flickering and bouncing again.
	cues = []
	for index, interval in enumerate(intervals):
		if not cues or cues[-1]["pose"] != interval["pose"]:
			cues.append({"pose": interval["pose"], "start": round(interval["start"], 3)})
		following = intervals[index + 1] if index + 1 < len(intervals) else None
		if following is not None and following["pose"] == interval["pose"] and following["start"] - interval["end"] < POSE_MERGE_GAP_SECONDS:
			continue
		# A return to the default pose shorter than NEUTRAL_MIN_SECONDS would only flicker: the pose is held instead
		if (following is None or following["start"] - interval["end"] >= NEUTRAL_MIN_SECONDS) and cues[-1]["pose"] != AVATAR_DEFAULT_POSE:
			cues.append({"pose": AVATAR_DEFAULT_POSE, "start": round(interval["end"], 3)})
	for cue in cues:
		logger.info("Pose %s at %.2f s", cue["pose"], cue["start"])
	return cues


def buildComposition(takeDir):
	videoDir = takeDir.parent.parent
	log = json.loads((takeDir / "log.json").read_text(encoding="utf-8"))
	timeline = json.loads((videoDir / "timeline.json").read_text(encoding="utf-8"))
	voice = json.loads((videoDir / "recordings" / "voice" / "markers.json").read_text(encoding="utf-8"))
	if not voice.get("words"):
		raise RuntimeError("markers.json has no word timings: regenerate the voice")
	leadIn = log["leadIn"]
	rows = readScriptWords(videoDir / "script.md")
	wordTimes, wordEnds = alignWordTimes(rows, voice["words"])
	logByIndex = {entry["index"]: entry for entry in log["events"]}
	highlights = [
		{"start": round(entry["plannedTime"] + leadIn, 3), "end": round(entry["plannedEnd"] + leadIn, 3), "rects": entry["rects"]}
		for entry in log["events"] if entry["type"] == "highlight" and entry.get("status") == "ok"
	]
	area = log["captureArea"]
	shutil.copyfile(log["audio"], takeDir / "audio.wav")
	composition = {
		"fps": FPS,
		"width": OUTPUT_WIDTH,
		"height": OUTPUT_HEIGHT,
		"durationInFrames": math.ceil(log["captureDuration"] * FPS),
		"capture": {"src": log["capture"], "width": area["w"], "height": area["h"], "offsetY": (OUTPUT_HEIGHT - area["h"]) // 2},
		"audio": {"src": "audio.wav", "delay": leadIn},
		"highlights": highlights,
		"typingCards": buildTypingCards(rows, wordTimes, timeline, logByIndex, leadIn),
	}
	avatar = buildAvatar(takeDir)
	if avatar is not None:
		avatar["cues"] = buildPoseCues(rows, wordTimes, wordEnds, leadIn, avatar["poses"])
		composition["avatar"] = avatar
	elif any(row["poses"] for row in rows):
		logger.warning("The script has pose markers but no avatar is available: poses ignored")
	return composition


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
