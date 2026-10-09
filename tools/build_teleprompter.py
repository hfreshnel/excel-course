import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from video_script import SPOKEN_COLUMN_INDEX, readRows, stripMarkers

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
TEMPLATE_PATH = TOOLS_DIR / "teleprompter_template.html"
DATA_PLACEHOLDER = "/*__TELEPROMPTER_DATA__*/null"
DEFAULT_SOURCE = REPO_ROOT / "exercises" / "exercise-1"
OUTPUT_NAME = "teleprompter.html"
TC_COLUMN_INDEX = 0
SCREEN_COLUMN_INDEX = 1
TITLE_PATTERN = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
MARKDOWN_EMPHASIS_PATTERN = re.compile(r"\*\*|`")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("buildTeleprompter")


def collectScripts(sources):
	scripts = []
	for source in sources:
		if source.is_dir():
			found = sorted(source.glob("video-*/script.md"))
			if not found:
				logger.warning("No video-*/script.md under %s", source)
			scripts.extend(found)
		elif source.is_file():
			scripts.append(source)
		else:
			logger.error("Not found: %s", source)
	return scripts


def defaultOutput(source):
	baseDir = source if source.is_dir() else source.resolve().parent.parent
	return baseDir / "renders" / OUTPUT_NAME


def readVideo(scriptPath):
	text = scriptPath.read_text(encoding="utf-8")
	titleMatch = TITLE_PATTERN.search(text)
	videoId = scriptPath.parent.name
	rows = []
	for row in readRows(scriptPath):
		cells = row["cells"]
		spoken = stripMarkers(cells[SPOKEN_COLUMN_INDEX])
		if not spoken:
			continue
		rows.append({
			"tc": cells[TC_COLUMN_INDEX].strip(),
			"screen": MARKDOWN_EMPHASIS_PATTERN.sub("", cells[SCREEN_COLUMN_INDEX]).strip(),
			"text": spoken,
		})
	if not rows:
		raise ValueError(f"{scriptPath}: no spoken text found")
	return {"id": videoId, "title": titleMatch.group(1) if titleMatch else videoId, "rows": rows}


def buildHtml(videos):
	template = TEMPLATE_PATH.read_text(encoding="utf-8")
	if template.count(DATA_PLACEHOLDER) != 1:
		raise ValueError(f"{TEMPLATE_PATH}: expected exactly one data placeholder")
	data = {"generatedAt": datetime.now().isoformat(timespec="seconds"), "videos": videos}
	# "</" would close the inline <script> early if a script ever contained "</script>"
	payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
	return template.replace(DATA_PLACEHOLDER, payload)


def main():
	parser = argparse.ArgumentParser(description="Build a self-contained HTML teleprompter from video script tables.")
	parser.add_argument("sources", nargs="*", type=Path, help="Exercise directories or script.md files (default: exercise 1)")
	parser.add_argument("--output", type=Path, help=f"Output HTML file (default: <exercise>/renders/{OUTPUT_NAME})")
	parser.add_argument("--open", action="store_true", help="Open the teleprompter in the default browser")
	args = parser.parse_args()
	sources = args.sources or [DEFAULT_SOURCE]
	scripts = collectScripts(sources)
	videos = []
	failureCount = 0
	for scriptPath in scripts:
		try:
			videos.append(readVideo(scriptPath))
		except Exception as error:
			failureCount += 1
			logger.error("Skipped %s: %s", scriptPath, error)
	if not videos:
		logger.error("No script could be read")
		return 1
	outputPath = (args.output or defaultOutput(sources[0])).resolve()
	try:
		outputPath.parent.mkdir(parents=True, exist_ok=True)
		outputPath.write_text(buildHtml(videos), encoding="utf-8", newline="\n")
	except Exception as error:
		logger.error("Could not write %s: %s", outputPath, error)
		return 1
	logger.info("%d video(s), %d paragraph(s) -> %s", len(videos), sum(len(video["rows"]) for video in videos), outputPath)
	if args.open:
		try:
			os.startfile(outputPath)
		except Exception as error:
			logger.error("Could not open %s: %s", outputPath, error)
	return 1 if failureCount else 0


if __name__ == "__main__":
	sys.exit(main())
