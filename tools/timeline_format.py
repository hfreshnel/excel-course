import json
from pathlib import Path


def writeTimeline(path, timeline):
	# One event per line keeps timeline diffs readable
	lines = ["{"]
	keys = list(timeline)
	for keyIndex, key in enumerate(keys):
		comma = "," if keyIndex < len(keys) - 1 else ""
		value = timeline[key]
		if key == "events":
			lines.append('\t"events": [')
			for eventIndex, event in enumerate(value):
				lines.append("\t\t" + json.dumps(event, ensure_ascii=False) + ("," if eventIndex < len(value) - 1 else ""))
			lines.append("\t]" + comma)
		else:
			lines.append(f"\t{json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}{comma}")
	lines.append("}")
	Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
