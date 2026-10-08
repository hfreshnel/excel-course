import argparse
import logging
import re
import sys
from pathlib import Path

from video_script import EXPECTED_COLUMN_COUNT, SPOKEN_COLUMN_INDEX, isDataRow, splitRow, stripMarkers

WORDS_PER_MINUTE = 140
TC_ROUNDING_SECONDS = 5
DURATION_LINE_PATTERN = re.compile(r"^\*\*Durée (cible|estimée) :\*\*.*$", re.MULTILINE)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("estimateTimecodes")


def formatTimecode(totalSeconds):
	roundedSeconds = int(round(totalSeconds / TC_ROUNDING_SECONDS) * TC_ROUNDING_SECONDS)
	return f"{roundedSeconds // 60:02d}:{roundedSeconds % 60:02d}"


def formatDuration(totalSeconds):
	roundedSeconds = int(round(totalSeconds / TC_ROUNDING_SECONDS) * TC_ROUNDING_SECONDS)
	minutes, seconds = divmod(roundedSeconds, 60)
	return f"{minutes} min {seconds:02d} s"


def processScript(scriptPath):
	text = scriptPath.read_text(encoding="utf-8")
	outputLines = []
	elapsedSeconds = 0.0
	rowCount = 0
	for lineNumber, line in enumerate(text.splitlines(), start=1):
		if not isDataRow(line):
			outputLines.append(line)
			continue
		cells = splitRow(line)
		if len(cells) != EXPECTED_COLUMN_COUNT:
			raise ValueError(f"{scriptPath}:{lineNumber}: expected {EXPECTED_COLUMN_COUNT} columns, got {len(cells)}")
		cells[0] = formatTimecode(elapsedSeconds)
		elapsedSeconds += len(stripMarkers(cells[SPOKEN_COLUMN_INDEX]).split()) * 60 / WORDS_PER_MINUTE
		outputLines.append("|" + "|".join(cells) + "|")
		rowCount += 1
	durationLine = f"**Durée estimée :** environ {formatDuration(elapsedSeconds)} (texte parlé à {WORDS_PER_MINUTE} mots/min, à recaler sur le rendu audio)"
	newText, replacedCount = DURATION_LINE_PATTERN.subn(durationLine, "\n".join(outputLines) + "\n")
	if replacedCount != 1:
		raise ValueError(f"{scriptPath}: expected exactly one duration line, found {replacedCount}")
	scriptPath.write_text(newText, encoding="utf-8", newline="\n")
	return rowCount, elapsedSeconds


def main():
	parser = argparse.ArgumentParser(description="Recompute estimated timecodes in video script tables from spoken word counts.")
	parser.add_argument("scripts", nargs="+", type=Path)
	args = parser.parse_args()
	failureCount = 0
	totalSeconds = 0.0
	for scriptPath in args.scripts:
		try:
			rowCount, elapsedSeconds = processScript(scriptPath)
			totalSeconds += elapsedSeconds
			logger.info("%s: %d rows, %s", scriptPath, rowCount, formatDuration(elapsedSeconds))
		except Exception as error:
			failureCount += 1
			logger.error("%s: %s", scriptPath, error)
	logger.info("Total spoken duration: %s", formatDuration(totalSeconds))
	return 1 if failureCount else 0


if __name__ == "__main__":
	sys.exit(main())
