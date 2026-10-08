import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

from ffmpeg_tools import findFfmpeg

HIGHLIGHT_COLOR = "0xFFB300"
ACTION_COLOR = "0x00B8D4"
ACTION_MARK_SECONDS = 0.8
BORDER_THICKNESS = 4
FILL_OPACITY = 0.22

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("renderPreview")


def drawBox(rect, color, opacity, thickness, start, end):
	# Commas inside between() must be escaped: the filter graph uses "," to chain filters
	enable = f"between(t\\,{start:.3f}\\,{end:.3f})"
	return f"drawbox=x={rect['x']}:y={rect['y']}:w={rect['w']}:h={rect['h']}:color={color}@{opacity}:t={thickness}:enable={enable}"


def buildFilters(log, showActions):
	leadIn = log["leadIn"]
	filters = []
	for entry in log["events"]:
		if entry.get("status") != "ok" or not entry.get("rects"):
			continue
		if entry["type"] == "highlight":
			# Highlights follow speech time (plannedTime), as the Remotion compositing will
			start = entry["plannedTime"] + leadIn
			end = entry["plannedEnd"] + leadIn
			for rect in entry["rects"]:
				filters.append(drawBox(rect, HIGHLIGHT_COLOR, FILL_OPACITY, "fill", start, end))
				filters.append(drawBox(rect, HIGHLIGHT_COLOR, 1.0, BORDER_THICKNESS, start, end))
		elif showActions:
			# Debug outline at the real execution time, to compare logged rectangles with Excel's own selection
			start = entry["actualTime"] + leadIn
			for rect in entry["rects"]:
				filters.append(drawBox(rect, ACTION_COLOR, 0.9, 2, start, start + ACTION_MARK_SECONDS))
	return filters


def render(takeDir, outputPath, showActions):
	log = json.loads((takeDir / "log.json").read_text(encoding="utf-8"))
	filters = buildFilters(log, showActions)
	delayMs = int(round(log["leadIn"] * 1000))
	videoChain = ",".join(filters) if filters else "null"
	graph = f"[0:v]{videoChain}[v];[1:a]adelay=delays={delayMs}:all=1,apad[a]"
	graphPath = takeDir / "preview.filtergraph.txt"
	graphPath.write_text(graph, encoding="utf-8")
	outputPath.parent.mkdir(parents=True, exist_ok=True)
	command = [
		findFfmpeg(), "-hide_banner", "-loglevel", "warning", "-y",
		"-i", str(takeDir / log["capture"]), "-i", log["audio"],
		# "-/option file" reads the option value from a file (ffmpeg 7.1+), avoiding Windows command-line limits
		"-/filter_complex", str(graphPath),
		"-map", "[v]", "-map", "[a]", "-shortest",
		"-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
		"-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
		str(outputPath),
	]
	logger.info("Rendering %d overlay boxes -> %s", len(filters), outputPath)
	subprocess.run(command, check=True)
	logger.info("Preview ready: %s", outputPath)


def main():
	parser = argparse.ArgumentParser(description="Render a debug preview: capture + placeholder voice + logged rectangles drawn with ffmpeg.")
	parser.add_argument("take", type=Path, help="take directory containing log.json and capture.mp4")
	parser.add_argument("--output", type=Path, help="defaults to <video dir>/renders/preview-<take>.mp4")
	parser.add_argument("--hide-actions", action="store_true", help="do not outline select/formula/value targets")
	args = parser.parse_args()
	takeDir = args.take.resolve()
	outputPath = args.output or takeDir.parent.parent / "renders" / f"preview-{takeDir.name}.mp4"
	try:
		render(takeDir, outputPath, not args.hide_actions)
	except Exception:
		logger.exception("Preview render failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
