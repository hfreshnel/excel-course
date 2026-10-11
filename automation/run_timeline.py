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

CHART_EVENT_TYPES = {"chartCreate", "chartMove", "chartTitle", "axisTitle", "seriesDelete", "seriesCategories", "seriesType", "pointSelect", "pointLabel", "chartBackground", "seriesFill", "seriesLine", "pointsFill", "dataLabels", "legend", "explosion"}
EXCEL_EVENT_TYPES = {"select", "formula", "value", "name", "clear", "addSheet", "renameSheet", "font", "numberFormat", "bold", "tabColor", "autofill", "fitColumns", "activateSheet"} | CHART_EVENT_TYPES
REPO_ROOT = Path(__file__).resolve().parent.parent
XL_LOCATION_AS_NEW_SHEET = 1
XL_CATEGORY = 1
XL_VALUE = 2
XL_LEGEND_POSITIONS = {"bottom": -4107, "right": -4152, "top": -4160, "left": -4131}
MSO_TRUE = -1
XL_LABEL_POSITIONS = {"outsideEnd": 2, "insideEnd": 3, "center": -4108, "bestFit": 5}
# "*" targets every cell of the sheet (Ctrl+A); no pixel rectangle is computed for it
WHOLE_SHEET = "*"
XL_FILL_DEFAULT = 0
# Rendered by Remotion from the voice markers only: not played in Excel, so they can change without a new take
OVERLAY_EVENT_TYPES = {"banner", "callout", "menuPath", "image", "titleCard"}
SETTLE_SECONDS = 1.5
SPIN_THRESHOLD_SECONDS = 0.02

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("runTimeline")


def loadJson(path):
	return json.loads(Path(path).read_text(encoding="utf-8"))


def resolveSchedule(timeline, markers):
	schedule = []
	for index, event in enumerate(timeline["events"]):
		if event["type"] in OVERLAY_EVENT_TYPES:
			continue
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


def targetRange(sheet, target):
	return sheet.Cells if target == WHOLE_SHEET else resolveRange(sheet, target)


def cellValues(target, value):
	# A list fills a row or a column, following the shape of the target
	if not isinstance(value, list):
		return value
	if value and isinstance(value[0], list):
		return tuple(tuple(row) for row in value)
	if target.Rows.Count == 1:
		return (tuple(value),)
	return tuple((item,) for item in value)


def fitColumns(sheet, event):
	# Same widths as automation/exercise_1_states.py: AutoFit plus a margin (text rendered at 90 % overflows a 100 % fit),
	# and a minimum width from a given column on, so that computed values never show ####
	columns = sheet.Range(event["target"]).EntireColumn
	columns.AutoFit()
	margin = event.get("margin", 0)
	minWidth = event.get("minWidth", 0)
	minFrom = sheet.Range(f"{event.get('minFrom', 'A')}1").Column
	for index in range(1, columns.Columns.Count + 1):
		current = columns.Columns(index)
		width = current.ColumnWidth + margin
		if current.Column >= minFrom:
			width = max(width, minWidth)
		current.ColumnWidth = width


def bgr(color):
	red, green, blue = color
	return red + green * 256 + blue * 65536


def chartSeries(chart, key):
	# A series is designated by its 1-based index or by its name (the column header)
	collection = chart.SeriesCollection()
	if isinstance(key, int):
		return collection.Item(key)
	for index in range(1, collection.Count + 1):
		if collection.Item(index).Name == key:
			return collection.Item(index)
	raise LookupError(f"no series named '{key}' (series: {[collection.Item(index).Name for index in range(1, collection.Count + 1)]})")


def allSeries(chart):
	collection = chart.SeriesCollection()
	return [collection.Item(index) for index in range(1, collection.Count + 1)]


def executeChartEvent(session, state, event):
	eventType = event["type"]
	if eventType == "chartCreate":
		sheet = session.sheet(state["sheet"])
		# AddChart2 plots the current selection, as the Insert ribbon does
		callWithRetry(lambda: resolveRange(sheet, event["target"]).Select())
		shape = callWithRetry(lambda: sheet.Shapes.AddChart2(-1, event["chartType"]))
		state["chart"] = callWithRetry(lambda: shape.Chart)
		return
	chart = state.get("chart")
	if chart is None:
		raise RuntimeError(f"{eventType}: no chart created yet in this take")
	if eventType == "chartMove":
		callWithRetry(lambda: chart.Location(XL_LOCATION_AS_NEW_SHEET, event["name"]))
		workbook = session.workbook
		state["chart"] = workbook.Charts(event["name"])
		# Excel inserts the chart sheet before the data sheet; G1 to G4 are kept after D1, in order
		state["chart"].Move(None, workbook.Sheets(workbook.Sheets.Count))
		state["chart"] = workbook.Charts(event["name"])
		state["chart"].Activate()
		state["sheet"] = event["name"]
	elif eventType == "chartTitle":
		chart.HasTitle = True
		chart.ChartTitle.Text = event["text"]
	elif eventType == "axisTitle":
		axis = chart.Axes(XL_CATEGORY if event["axis"] == "category" else XL_VALUE, event.get("group", 1))
		axis.HasTitle = True
		axis.AxisTitle.Text = event["text"]
	elif eventType == "seriesDelete":
		# Excel takes a numeric column (years) for a series: it is removed when present, as the video explains
		for series in reversed(allSeries(chart)):
			if series.Name == event["name"]:
				series.Delete()
	elif eventType == "seriesCategories":
		categories = session.sheet(event.get("dataSheet", state["dataSheet"])).Range(event["target"])
		for series in allSeries(chart):
			series.XValues = categories
	elif eventType == "seriesType":
		series = chartSeries(chart, event["series"])
		series.ChartType = event["chartType"]
		series.AxisGroup = event.get("axisGroup", 1)
	elif eventType == "pointSelect":
		# Without "point" the whole series is selected (first click), with it a single point (second click)
		series = chartSeries(chart, event.get("series", 1))
		if event.get("point") is None:
			series.Select()
		else:
			series.Points(event["point"]).Select()
	elif eventType == "pointLabel":
		point = chartSeries(chart, event.get("series", 1)).Points(event["point"])
		point.HasDataLabel = True
		point.DataLabel.Text = event["text"]
	elif eventType == "chartBackground":
		picture = (REPO_ROOT / event["picture"]).resolve()
		chart.ChartArea.Format.Fill.UserPicture(str(picture))
		# The plot area is filled white by default and would hide the wall
		chart.PlotArea.Format.Fill.Visible = 0
	elif eventType == "seriesFill":
		targets = allSeries(chart) if event.get("series", "all") == "all" else [chartSeries(chart, event["series"])]
		for series in targets:
			series.Format.Fill.Visible = MSO_TRUE
			series.Format.Fill.Solid()
			series.Format.Fill.ForeColor.RGB = bgr(event["color"])
	elif eventType == "seriesLine":
		series = chartSeries(chart, event["series"])
		series.Format.Line.Visible = MSO_TRUE
		series.Format.Line.ForeColor.RGB = bgr(event["color"])
		if event.get("weight"):
			series.Format.Line.Weight = event["weight"]
	elif eventType == "pointsFill":
		series = chartSeries(chart, event.get("series", 1))
		for index, color in enumerate(event["colors"], start=1):
			fill = series.Points(index).Format.Fill
			fill.Visible = MSO_TRUE
			fill.Solid()
			fill.ForeColor.RGB = bgr(color)
	elif eventType == "dataLabels":
		series = chartSeries(chart, event.get("series", 1))
		series.HasDataLabels = True
		labels = series.DataLabels()
		labels.ShowCategoryName = event.get("category", False)
		labels.ShowValue = event.get("value", True)
		labels.ShowLegendKey = False
		if event.get("position"):
			labels.Position = XL_LABEL_POSITIONS[event["position"]]
		if "leaderLines" in event:
			series.HasLeaderLines = event["leaderLines"]
	elif eventType == "legend":
		chart.HasLegend = event.get("visible", True)
		if event.get("visible", True) and event.get("position"):
			chart.Legend.Position = XL_LEGEND_POSITIONS[event["position"]]
	elif eventType == "explosion":
		series = chartSeries(chart, event.get("series", 1))
		if "value" in event:
			series.Explosion = event["value"]
		for pointIndex, value in event.get("points", {}).items():
			series.Points(int(pointIndex)).Explosion = value


def executeEvent(session, state, event, view):
	eventType = event["type"]
	if eventType == "chartCreate":
		# Not retried as a whole: a rejected call after AddChart2 would create a second chart
		executeChartEvent(session, state, event)
		return
	if eventType in CHART_EVENT_TYPES:
		# The other chart edits are idempotent: a call rejected while Excel redraws is replayed whole
		callWithRetry(lambda: executeChartEvent(session, state, event))
		# Under load Excel deferred the repaint of a series colour by 25 s (video 6 take): the chart is redrawn now
		if eventType != "chartMove":
			callWithRetry(lambda: state["chart"].Refresh())
		return
	if eventType == "addSheet":
		workbook = session.workbook
		added = callWithRetry(lambda: workbook.Worksheets.Add(None, workbook.Worksheets(event["after"])))
		state["sheet"] = added.Name
		# A new sheet opens at 100 %: the take view (zoom, scroll) is applied to it as to the start sheet
		session.freezeView(state["sheet"], view.get("zoom", 100), 1, 1, "A1")
		return
	if eventType == "activateSheet":
		callWithRetry(lambda: session.workbook.Sheets(event["name"]).Activate())
		state["sheet"] = event["name"]
		return
	if eventType == "renameSheet":
		sheet = session.sheet(state["sheet"])
		callWithRetry(lambda: setattr(sheet, "Name", event["name"]))
		state["sheet"] = event["name"]
		return
	sheet = session.sheet(state["sheet"])
	if eventType == "select":
		callWithRetry(lambda: targetRange(sheet, event["target"]).Select())
	elif eventType == "formula":
		# Formula2Local keeps dynamic-array semantics (no implicit "@") and accepts the French syntax of the scripts
		callWithRetry(lambda: setattr(sheet.Range(event["target"]), "Formula2Local", event["formula"]))
	elif eventType == "value":
		target = resolveRange(sheet, event["target"])
		callWithRetry(lambda: setattr(target, "Value2", cellValues(target, event["value"])))
		if event.get("numberFormat"):
			callWithRetry(lambda: setattr(target, "NumberFormatLocal", session.localFormats()[event["numberFormat"]]))
	elif eventType == "font":
		callWithRetry(lambda: setattr(targetRange(sheet, event["target"]).Font, "Name", event["font"]))
	elif eventType == "numberFormat":
		# NumberFormat is parsed with the caller locale through pywin32, hence the local formats
		callWithRetry(lambda: setattr(targetRange(sheet, event["target"]), "NumberFormatLocal", session.localFormats()[event["format"]]))
	elif eventType == "bold":
		callWithRetry(lambda: setattr(targetRange(sheet, event["target"]).Font, "Bold", event.get("bold", True)))
	elif eventType == "tabColor":
		red, green, blue = event["color"]
		# Excel colours are BGR integers
		callWithRetry(lambda: setattr(sheet.Tab, "Color", red + green * 256 + blue * 65536))
	elif eventType == "autofill":
		source = resolveRange(sheet, event["target"])
		callWithRetry(lambda: source.AutoFill(sheet.Range(event["destination"]), XL_FILL_DEFAULT))
	elif eventType == "fitColumns":
		# Each width change repaints the grid (4.8 s for 16 columns in the video 1 take): the widths are applied at once
		application = session.app
		application.ScreenUpdating = False
		try:
			callWithRetry(lambda: fitColumns(sheet, event))
		finally:
			application.ScreenUpdating = True
	elif eventType == "clear":
		# Same effect as the Delete key: contents go, formats stay
		callWithRetry(lambda: resolveRange(sheet, event["target"]).ClearContents())
	elif eventType == "name":
		# The Name Box shows the new name by itself; reselecting a single cell right away would blank it
		callWithRetry(lambda: setattr(resolveRange(sheet, event["target"]), "Name", event["name"]))


def eventRects(session, state, event, uiRects, area):
	if event.get("ui"):
		return [uiRects[event["ui"]]]
	target = event.get("destination") if event["type"] == "autofill" else event.get("target")
	if not target or target == WHOLE_SHEET or event["type"] in {"addSheet", "renameSheet", "tabColor", "activateSheet"} | CHART_EVENT_TYPES:
		return None
	return session.rangeRects(state["sheet"], target, area)


def uiKeys(timeline):
	keys = {event["ui"] for event in timeline["events"] if event.get("ui")}
	if any(event["type"] == "name" for event in timeline["events"]):
		keys.add("nameBox")
	return sorted(keys)


def run(timelinePath, markersPath, statesDir, takeDir, leadIn, tail, frameRate):
	timeline = loadJson(timelinePath)
	voice = loadJson(markersPath)
	schedule = resolveSchedule(timeline, voice["markers"])
	# The current sheet changes when a sheet is added or renamed during the take
	state = {"sheet": timeline["sheet"], "dataSheet": timeline["sheet"]}
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
		session.freezeView(state["sheet"], view.get("zoom", 100), view.get("scrollRow", 1), view.get("scrollColumn", 1), view.get("activeCell", "A1"))
		session.bringToFront(topmost=True)
		session.dismissTransientUi()
		area = session.workArea()
		log["captureArea"] = area
		log["view"] = view
		uiRects = session.uiRects(uiKeys(timeline), area)
		log["uiRects"] = uiRects
		# Let Excel finish painting before the first frame
		time.sleep(SETTLE_SECONDS)
		recorder = ScreenRecorder(findFfmpeg(), takeDir / "capture.raw.mp4", area, frameRate)
		captureStart = recorder.start()
		audioStart = captureStart + leadIn
		for item in schedule:
			event = item["event"]
			waitUntil(audioStart + item["plannedTime"])
			entry = {"index": item["index"], "type": event["type"], "at": event["at"], "target": event.get("target") or event.get("ui"), "plannedTime": round(item["plannedTime"], 3)}
			if item["plannedEnd"] is not None:
				entry["plannedEnd"] = round(item["plannedEnd"], 3)
			try:
				executeEvent(session, state, event, view)
				entry["actualTime"] = round(time.perf_counter() - audioStart, 3)
				entry["jitter"] = round(entry["actualTime"] - entry["plannedTime"], 3)
				rects = eventRects(session, state, event, uiRects, area)
				if rects is not None:
					entry["rects"] = rects
				entry["sheet"] = state["sheet"]
				if event["type"] == "name":
					entry["uiRect"] = uiRects["nameBox"]
				entry["status"] = "ok"
			except Exception as error:
				entry["status"] = f"error: {error}"
				logger.exception("Event %d (%s %s) failed", item["index"], event["type"], event.get("target"))
			logEntries.append(entry)
			logger.info("Event %d %s %s at %.2f s (jitter %+.3f s)", item["index"], event["type"], entry["target"], entry.get("actualTime", -1), entry.get("jitter", 0))
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
	mismatches = [rect for entry in logEntries for rect in entry.get("rects", []) if rect["check"] not in ("ok", "ui")]
	logger.info("%d events, %d failures, %d pixel check mismatches", len(logEntries), len(failures), len(mismatches))
	return not failures


def main():
	parser = argparse.ArgumentParser(description="Play a video timeline in Excel while capturing the screen, and log real timings and pixel rectangles.")
	parser.add_argument("timeline", type=Path)
	parser.add_argument("--markers", type=Path, help="defaults to <video dir>/recordings/voice/markers.json (recorded narration), else voice-placeholder/markers.json")
	parser.add_argument("--states-dir", type=Path, help="defaults to <exercise dir>/states")
	parser.add_argument("--take-dir", type=Path, help="defaults to <video dir>/recordings/take-<timestamp>")
	parser.add_argument("--lead-in", type=float, default=1.0)
	parser.add_argument("--tail", type=float, default=1.5)
	parser.add_argument("--frame-rate", type=int, default=30)
	args = parser.parse_args()
	videoDir = args.timeline.resolve().parent
	markersPath = args.markers
	if markersPath is None:
		recorded = videoDir / "recordings" / "voice" / "markers.json"
		markersPath = recorded if recorded.is_file() else videoDir / "recordings" / "voice-placeholder" / "markers.json"
		logger.info("Voice: %s", markersPath)
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
