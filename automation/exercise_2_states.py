import argparse
import logging
import sys
from pathlib import Path

from excel_session import ExcelSession, enableDpiAwareness

REPO_ROOT = Path(__file__).resolve().parent.parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "exercise-2"
DATA_PATH = EXERCISE_DIR / "data" / "01-data.xlsx"
STATES_DIR = EXERCISE_DIR / "states"

# The Salaries column of Q1 is empty in the statement (filled in the 2024 version and in the hidden SOL sheet):
# until the client sends a corrected statement, the start state takes the salaries of SOL (values only)
SALARIES_TARGET = ("Q1", "D2:D19")
SALARIES_SOURCE = ("SOL", "D2:D19")
START_SHEET = "QS"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("exercise2States")


def build(statesDir):
	statesDir.mkdir(parents=True, exist_ok=True)
	session = ExcelSession(visible=False).start()
	try:
		workbook = session.openCopy(DATA_PATH, statesDir / "work.tmp.xlsx")
		session.breakExternalLinks()
		target = workbook.Worksheets(SALARIES_TARGET[0]).Range(SALARIES_TARGET[1])
		target.Value2 = workbook.Worksheets(SALARIES_SOURCE[0]).Range(SALARIES_SOURCE[1]).Value2
		logger.info("Salaries copied from %s!%s to %s!%s", *SALARIES_SOURCE, *SALARIES_TARGET)
		# The hidden sheets (S5, SOL, CC) stay hidden; the workbook opens on the questions
		sheet = workbook.Worksheets(START_SHEET)
		sheet.Activate()
		sheet.Range("A1").Select()
		session.saveAs(statesDir / "state-00.xlsx")
	finally:
		session.close()
		(statesDir / "work.tmp.xlsx").unlink(missing_ok=True)


def main():
	parser = argparse.ArgumentParser(description="Build the start workbook of exercise 2 (statement plus the salaries of the solution sheet).")
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
