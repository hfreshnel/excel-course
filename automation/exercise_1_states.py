import argparse
import logging
import sys
from pathlib import Path

from excel_session import ExcelSession, enableDpiAwareness, resolveRange

REPO_ROOT = Path(__file__).resolve().parent.parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "exercise-1"
DATA_PATH = EXERCISE_DIR / "data" / "01-data.xlsx"
STATES_DIR = EXERCISE_DIR / "states"

SHEET_NAME = "D1"
SOURCE_SHEET_NAME = "QQ"
FONT_NAME = "Cambria"
MIN_COLUMN_WIDTH = 11
AUTOFIT_MARGIN = 1
MIN_WIDTH_FIRST_COLUMN = 4  # D
MIN_WIDTH_LAST_COLUMN = 16  # P
TAB_GREEN = 0x50B000  # Excel colors are BGR: RGB(0, 176, 80)

HEADERS = ["Période", "Année", "Produits", "Prix HT", "Prix Solde", "Economie", "Prix Haut", "Evo %", "Quantité", "Prix TTC", "Prix HT vérif", "CA TTC", "% CA", "Moyenne TTC", "Min %", "Max CA"]
MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
PRICES_HT = [95, 81, 85, 45, 43, 47, 36, 12, 52, 40, 75, 93]
PRICES_HIGH = [96, 82, 86, 46, 44, 48, 37, 13, 53, 41, 76, 94]
QUANTITIES = [28, 69, 14, 37, 12, 81, 75, 31, 63, 58, 76, 36]

CURRENCY_RANGES = "D2:G13,J2:L14,N2,P2"
PERCENT_RANGES = "H2:H13,M2:M14,O2"
BOLD_RANGES = "E2:F13,H2:H13,J2:M13,L14:M14,N2:P2,F18:F19"

COLUMN_NAMES = {"A": "Periode", "B": "Annee", "C": "Produits", "D": "Prix_HT", "E": "Prix_Solde", "F": "Economie", "G": "Prix_Haut", "H": "Evo", "I": "Quantite", "J": "Prix_TTC", "K": "Prix_HT_C", "L": "CA_TTC", "M": "PCA"}
CELL_NAMES = {"F20": "Solde", "F21": "TVA"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("exercise1States")


def column(values):
	return tuple((value,) for value in values)


def applyStep1(workbook, formats):
	sheet = workbook.Worksheets.Add(None, workbook.Worksheets(SOURCE_SHEET_NAME))
	sheet.Name = SHEET_NAME
	sheet.Cells.Font.Name = FONT_NAME
	sheet.Range("A1:P1").Value = (tuple(HEADERS),)
	sheet.Range("A2:A13").Value = column(MONTHS)
	sheet.Range("B2:B13").Value = column(range(2014, 2026))
	sheet.Range("C2:C13").Value = column(f"AB{index}" for index in range(1, 13))
	sheet.Range("D2:D13").Value = column(PRICES_HT)
	sheet.Range("G2:G13").Value = column(PRICES_HIGH)
	sheet.Range("I2:I13").Value = column(QUANTITIES)
	sheet.Range("E18:E21").Value = column(["Date 1", "Date 2", "Solde", "TVA"])
	sheet.Range("F20").Value = 0.44
	sheet.Range("F20").NumberFormatLocal = formats["percent0"]
	sheet.Range("F21").Value = 0.055
	sheet.Range("F21").NumberFormatLocal = formats["percent1"]
	resolveRange(sheet, CURRENCY_RANGES).NumberFormatLocal = formats["currency"]
	resolveRange(sheet, PERCENT_RANGES).NumberFormatLocal = formats["percent2"]
	resolveRange(sheet, BOLD_RANGES).Font.Bold = True
	sheet.Tab.Color = TAB_GREEN
	# Not in the video 1 script: without it, long headers overflow and computed columns show ####
	# (Evo % is narrower than "1,05%", and D2 becomes "100,00 €" in video 3)
	# AutoFit measures at 100 % zoom; text rendered at other zooms can overflow, hence the margin
	sheet.Range("A1:P1").EntireColumn.AutoFit()
	for columnIndex in range(1, MIN_WIDTH_LAST_COLUMN + 1):
		currentColumn = sheet.Columns(columnIndex)
		width = currentColumn.ColumnWidth + AUTOFIT_MARGIN
		if columnIndex >= MIN_WIDTH_FIRST_COLUMN:
			width = max(width, MIN_COLUMN_WIDTH)
		currentColumn.ColumnWidth = width
	return sheet


def applyStep2(workbook):
	sheet = workbook.Worksheets(SHEET_NAME)
	for letter, name in COLUMN_NAMES.items():
		sheet.Range(f"{letter}2:{letter}13").Name = name
	for address, name in CELL_NAMES.items():
		sheet.Range(address).Name = name
	logger.info("Defined %d names", workbook.Names.Count)


def build(statesDir):
	session = ExcelSession(visible=False)
	try:
		session.start()
		session.openCopy(DATA_PATH, statesDir / "work.tmp.xlsx")
		workbook = session.workbook
		session.breakExternalLinks()
		sheet = applyStep1(workbook, session.localFormats())
		sheet.Activate()
		sheet.Range("A1").Select()
		session.saveAs(statesDir / "state-01.xlsx")
		applyStep2(workbook)
		sheet.Range("A1").Select()
		session.saveAs(statesDir / "state-02.xlsx")
	finally:
		session.close()
		(statesDir / "work.tmp.xlsx").unlink(missing_ok=True)


def main():
	parser = argparse.ArgumentParser(description="Build the end-of-step workbooks of exercise 1 that videos start from.")
	parser.add_argument("--states-dir", type=Path, default=STATES_DIR)
	args = parser.parse_args()
	enableDpiAwareness()
	try:
		build(args.states_dir)
	except Exception:
		logger.exception("State build failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
