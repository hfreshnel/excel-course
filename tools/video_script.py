import re
from pathlib import Path

SPOKEN_COLUMN_INDEX = 2
EXPECTED_COLUMN_COUNT = 4
# "{@name}" fires at the start of the word that follows it; markers are never spoken
MARKER_PATTERN = re.compile(r"\{@([A-Za-z][A-Za-z0-9_]*)\}")
ROW_MARKER_PATTERN = re.compile(r"^r\d+$")
WHITESPACE_PATTERN = re.compile(r"\s+")


def isDataRow(line):
	return line.startswith("|") and not line.startswith("|---") and not line.startswith("| TC")


def splitRow(line):
	# Rows look like "|TC|screen|spoken|action|": strip the outer pipes before splitting
	return line.strip()[1:-1].split("|")


def stripMarkers(text):
	return WHITESPACE_PATTERN.sub(" ", MARKER_PATTERN.sub("", text)).strip()


def readRows(scriptPath):
	rows = []
	text = Path(scriptPath).read_text(encoding="utf-8")
	for lineNumber, line in enumerate(text.splitlines(), start=1):
		if not isDataRow(line):
			continue
		cells = splitRow(line)
		if len(cells) != EXPECTED_COLUMN_COUNT:
			raise ValueError(f"{scriptPath}:{lineNumber}: expected {EXPECTED_COLUMN_COUNT} columns, got {len(cells)}")
		rows.append({"lineNumber": lineNumber, "cells": cells})
	return rows


def readSpokenItems(scriptPath):
	# Flattens the spoken column into ("marker", name) / ("text", chunk) items.
	# Each row opens with an implicit marker "r<index>" (1-based).
	items = []
	seenMarkers = set()
	for rowIndex, row in enumerate(readRows(scriptPath), start=1):
		items.append(("marker", f"r{rowIndex}"))
		spoken = row["cells"][SPOKEN_COLUMN_INDEX]
		position = 0
		for match in MARKER_PATTERN.finditer(spoken):
			name = match.group(1)
			if ROW_MARKER_PATTERN.match(name):
				raise ValueError(f"{scriptPath}:{row['lineNumber']}: marker '{name}' clashes with implicit row markers")
			if name in seenMarkers:
				raise ValueError(f"{scriptPath}:{row['lineNumber']}: duplicate marker '{name}'")
			seenMarkers.add(name)
			chunk = stripMarkers(spoken[position:match.start()])
			if chunk:
				items.append(("text", chunk))
			items.append(("marker", name))
			position = match.end()
		chunk = stripMarkers(spoken[position:])
		if chunk:
			items.append(("text", chunk))
	return items


def readCleanSpokenText(scriptPath):
	return [stripMarkers(row["cells"][SPOKEN_COLUMN_INDEX]) for row in readRows(scriptPath)]
