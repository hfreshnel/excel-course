import json
import re
from pathlib import Path

from num2words import num2words

LEXICON_NAME = "tts-lexicon.json"
# Digit groups split by a (non-breaking) space are one number: "34 965" is thirty-four thousand...
GROUPED_NUMBER_PATTERN = re.compile(r"(?<![\d,])(\d{1,3})((?:[   ]\d{3})+)(?![\d])")
CELL_PATTERN = re.compile(r"\b([A-Z]{1,3})(\d+)\b")
DECIMAL_PATTERN = re.compile(r"\b(\d+),(\d+)\b")
INTEGER_PATTERN = re.compile(r"\b\d+\b")
UPPERCASE_WORD_PATTERN = re.compile(r"\b[A-ZÀ-Ý]{2,}\b")
SYMBOLS = {"%": " pour cent", "€": " euros"}
# Single letters Chatterbox misreads (heard on video 2): "D" as "deux", "H" as "a". Spelled as their French names,
# both in cell references ("D2") and in spelled acronyms ("H T").
LETTER_NAMES = {"D": "dé", "H": "ache"}
SINGLE_LETTER_PATTERN = re.compile(r"(?<![\w'’])([A-Z])(?![\w'’])")


def loadLexicon(exerciseDir):
	path = Path(exerciseDir) / LEXICON_NAME
	if not path.is_file():
		return {}
	lexicon = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(lexicon, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in lexicon.items()):
		raise ValueError(f"{path}: expected an object of strings")
	return lexicon


def numberWords(value):
	# 1990 spelling, hyphens everywhere: "quarante et un" was read as two numbers ("40 et 1")
	return num2words(int(value), lang="fr").replace(" ", "-")


def decimalWords(match):
	integer, fraction = match.group(1), match.group(2)
	# Leading zeros are read one by one: "1,05" is "un virgule zéro cinq"
	zeros = len(fraction) - len(fraction.lstrip("0"))
	rest = fraction.lstrip("0")
	spoken = " ".join(["zéro"] * zeros + ([numberWords(rest)] if rest else []))
	return f"{numberWords(integer)} virgule {spoken}"


def ttsText(text, lexicon):
	# The text sent to the speech model only: the script keeps its written form
	for written, spoken in sorted(lexicon.items(), key=lambda item: -len(item[0])):
		text = re.sub(rf"(?<![\w]){re.escape(written)}(?![\w])", spoken, text)
	for symbol, spoken in SYMBOLS.items():
		text = text.replace(symbol, spoken)
	text = GROUPED_NUMBER_PATTERN.sub(lambda match: match.group(1) + re.sub(r"\D", "", match.group(2)), text)
	# Cell references are spelled: "E13" -> "E treize", "AB11" -> "A B onze"
	text = CELL_PATTERN.sub(lambda match: " ".join(match.group(1)) + " " + numberWords(match.group(2)), text)
	text = SINGLE_LETTER_PATTERN.sub(lambda match: LETTER_NAMES.get(match.group(1), match.group(1)), text)
	text = DECIMAL_PATTERN.sub(decimalWords, text)
	text = INTEGER_PATTERN.sub(lambda match: numberWords(match.group()), text)
	# Remaining capitalised words are Excel function names (SOMME, MOYENNE): read as words, not spelled
	text = UPPERCASE_WORD_PATTERN.sub(lambda match: match.group().lower(), text)
	return re.sub(r"\s+", " ", text).strip()
