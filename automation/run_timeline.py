import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from excel_session import OFFICE_THEME_COLORFUL, ExcelSession, callWithRetry, enableDpiAwareness, resolveRange
from ffmpeg_tools import findFfmpeg
from screen_recorder import ScreenRecorder, normalizeCapture

EXCEL_EVENT_TYPES = {"select", "formula", "value"}
SETTLE_SECONDS = 1.5
SPIN_THRESHOLD_SECONDS = 0.02

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("runTimeline")


def loadJson(path):
	return json.loads(Path(path).read_text(encoding="utf-8"))


def resolveSchedule(timeline, markers):
	schedule = []
	for index, event in enumerate(timeline["events"]):
		if event["at"] not in markers:
			raise KeyError(f"event {index}: unknown marker '{event['at']}'")
		plannedTime = markers[event["at"]] + event.get("offset", 0.0)
		plannedEnd = None
		if event["type"] == "highlight":
			if "to" in event:
				if event["to"] not in markers:
					raise KeyError(f"event {index}: unknown marker '{event['to']}'")
				plannedEnd = markers[event["to"]]
			else:
				plannedEnd = plannedTime + event.get("duration", 2.0)
		elif event["type"] not in EXCEL_EVENT_TYPES:
			raise ValueError(f"event {index}: unknown type '{event['type']}'")
		schedule.append({"index": index, "event": event, "plannedTime": max(plannedTime, 0.0), "plannedEnd": plannedEnd})
	# Stable sort keeps the file order for events sharing a timestamp (select before formula, etc.)
	schedule.sort(key=lambda item: item["plannedTime"])
	return schedule


def waitUntil(deadline):
	while True:
		remaining = deadline - time.perf_counter()
		if remaining <= 0:
			return
		if remaining > SPIN_THRESHOLD_SECONDS:
			time.sleep(remaining - SPIN_THRESHOLD_SECONDS)


def executeEvent(session, sheetName, event):
	sheet = session.sheet(sheetName)
	eventType = event["type"]
	if eventType == "select":
		callWithRetry(lambda: resolveRange(sheet, event["target"]).Select())
	elif eventType == "formula":
		# Formula2Local keeps dynamic-array semantics (no implicit "@") and accepts the French syntax of the scripts
		callWithRetry(lambda: setattr(sheet.Range(event["target"]), "Formula2Local", event["formula"]))
	elif eventType == "value":
		callWithRetry(lambda: setattr(sheet.Range(event["target"]), "Value2", event["value"]))


def run(timelinePath, markersPath, statesDir, takeDir, leadIn, tail, frameRate):
	timeline = loadJson(timelinePath)
	voice = loadJson(markersPath)
	schedule = resolveSchedule(timeline, voice["markers"])
	sheetName = timeline["sheet"]
	view = timeline.get("view", {})
	takeDir.mkdir(parents=True, exist_ok=True)
	logEntries = []
	log = {
		"video": timeline["video"],
		"createdAt": datetime.now().isoformat(timespec="seconds"),
		"timeBase": "seconds from audio start; video time = audio time + leadIn",
		"leadIn": leadIn,
		"audio": str((Path(markersPath).parent / voice["audio"]).resolve()),
		"audioDuration": voice["duration"],
		"voiceSource": voice.get("source"),
		"capture": "capture.mp4",
		"events": logEntries,
	}
	session = ExcelSession(visible=True, officeTheme=OFFICE_THEME_COLORFUL)
	recorder = None
	try:
		session.start()
		log["excel"] = session.describe()
		session.openCopy(statesDir / timeline["startState"], takeDir / "work.xlsx")
		session.freezeView(sheetName, view.get("zoom", 100), view.get("scrollRow", 1), view.get("scrollColumn", 1), view.get("activeCell", "A1"))
		session.bringToFront(topmost=True)
		session.dismissTransientUi()
		area = session.workArea()
		log["captureArea"] = area
		log["view"] = view
		# Let Excel finish painting before the first frame
		time.sleep(SETTLE_SECONDS)
		recorder = ScreenRecorder(findFfmpeg(), takeDir / "capture.raw.mp4", area, frameRate)
		captureStart = recorder.start()
		audioStart = captureStart + leadIn
		for item in schedule:
			event = item["event"]
			waitUntil(audioStart + item["plannedTime"])
			entry = {"index": item["index"], "type": event["type"], "at": event["at"], "target": event.get("target"), "plannedTime": round(item["plannedTime"], 3)}
			if item["plannedEnd"] is not None:
				entry["plannedEnd"] = round(item["plannedEnd"], 3)
			try:
				executeEvent(session, sheetName, event)
				entry["actualTime"] = round(time.perf_counter() - audioStart, 3)
				entry["jitter"] = round(entry["actualTime"] - entry["plannedTime"], 3)
				if event.get("target"):
					entry["rects"] = session.rangeRects(sheetName, event["target"], area)
				entry["status"] = "ok"
			except Exception as error:
				entry["status"] = f"error: {error}"
				logger.exception("Event %d (%s %s) failed", item["index"], event["type"], event.get("target"))
			logEntries.append(entry)
			logger.info("Event %d %s %s at %.2f s (jitter %+.3f s)", item["index"], event["type"], event.get("target"), entry.get("actualTime", -1), entry.get("jitter", 0))
		waitUntil(audioStart + voice["duration"] + tail)
		log["captureDuration"] = round(time.perf_counter() - captureStart, 3)
		recorder.stop()
		normalizeCapture(findFfmpeg(), takeDir / "capture.raw.mp4", takeDir / "capture.mp4", frameRate)
		# Only a complete take may produce the next video's start state
		if timeline.get("endState") and all(entry["status"] == "ok" for entry in logEntries):
			session.saveAs(statesDir / timeline["endState"])
	finally:
		if recorder is not None:
			recorder.stop()
		session.close()
		(takeDir / "log.json").write_text(json.dumps(log, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
		logger.info("Log written to %s", takeDir / "log.json")
	failures = [entry for entry in logEntries if entry.get("status") != "ok"]
	mismatches = [rect for entry in logEntries for rect in entry.get("rects", []) if rect["check"] != "ok"]
	logger.info("%d events, %d failures, %d pixel check mismatches", len(logEntries), len(failures), len(mismatches))
	return not failures


def main():
	parser = argparse.ArgumentParser(description="Play a video timeline in Excel while capturing the screen, and log real timings and pixel rectangles.")
	parser.add_argument("timeline", type=Path)
	parser.add_argument("--markers", type=Path, help="defaults to <video dir>/recordings/voice/markers.json")
	parser.add_argument("--states-dir", type=Path, help="defaults to <exercise dir>/states")
	parser.add_argument("--take-dir", type=Path, help="defaults to <video dir>/recordings/take-<timestamp>")
	parser.add_argument("--lead-in", type=float, default=1.0)
	parser.add_argument("--tail", type=float, default=1.5)
	parser.add_argument("--frame-rate", type=int, default=30)
	args = parser.parse_args()
	videoDir = args.timeline.resolve().parent
	markersPath = args.markers or videoDir / "recordings" / "voice" / "markers.json"
	statesDir = args.states_dir or videoDir.parent / "states"
	takeDir = args.take_dir or videoDir / "recordings" / f"take-{datetime.now():%Y%m%d-%H%M%S}"
	enableDpiAwareness()
	try:
		succeeded = run(args.timeline, markersPath, statesDir, takeDir, args.lead_in, args.tail, args.frame_rate)
	except Exception:
		logger.exception("Timeline run failed")
		return 1
	print(takeDir)
	return 0 if succeeded else 2


if __name__ == "__main__":
	sys.exit(main())
