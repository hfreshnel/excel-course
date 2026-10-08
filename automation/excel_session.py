import ctypes
import logging
import shutil
import time
from pathlib import Path

import pywintypes
import win32api
import win32con
import win32gui
import winreg
import win32com.client

logger = logging.getLogger("excelSession")

RPC_RETRY_HRESULTS = {-2147418111, -2147417846}  # RPC_E_CALL_REJECTED, RPC_E_SERVERCALL_RETRYLATER
XL_MAXIMIZED = -4137
XL_OPEN_XML_WORKBOOK = 51
MSO_LANGUAGE_ID_UI = 2
XL_LINK_TYPE_EXCEL_LINKS = 1
DONT_UPDATE_LINKS = 0
PROCESS_PER_MONITOR_DPI_AWARE = 2
OFFICE_THEME_KEY = r"Software\Microsoft\Office\16.0\Common"
OFFICE_THEME_VALUE = "UI Theme"
OFFICE_THEME_COLORFUL = 0
TEACHING_CALLOUTS_KEY = OFFICE_THEME_KEY + r"\TeachingCallouts"
TEACHING_CALLOUT_SEEN = 2
# One-time Excel bubbles that would cover the grid in a recording
RECORDING_CALLOUTS = ["DynamicArrayFirstSpillCallout"]


def enableDpiAwareness():
	# Excel reports physical pixels; this process must use the same coordinate space
	try:
		ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
	except Exception:
		try:
			ctypes.windll.user32.SetProcessDPIAware()
		except Exception:
			logger.exception("Could not enable DPI awareness, pixel rectangles may be scaled")


def callWithRetry(func, *args, attempts=40, delay=0.25):
	for attempt in range(1, attempts + 1):
		try:
			return func(*args)
		except pywintypes.com_error as error:
			if error.hresult not in RPC_RETRY_HRESULTS or attempt == attempts:
				raise
			logger.warning("Excel busy (attempt %d/%d), retrying", attempt, attempts)
			time.sleep(delay)


def resolveRange(sheet, address):
	# pywin32 invokes with the user locale, so Excel would expect ";" between areas on a French system.
	# Building the union explicitly keeps addresses written with "," valid everywhere.
	parts = [part.strip() for part in address.split(",") if part.strip()]
	if len(parts) == 1:
		return sheet.Range(parts[0])
	return sheet.Application.Union(*(sheet.Range(part) for part in parts))


def readOfficeTheme():
	try:
		with winreg.OpenKey(winreg.HKEY_CURRENT_USER, OFFICE_THEME_KEY) as key:
			return winreg.QueryValueEx(key, OFFICE_THEME_VALUE)[0]
	except FileNotFoundError:
		return None


def writeOfficeTheme(value):
	with winreg.CreateKey(winreg.HKEY_CURRENT_USER, OFFICE_THEME_KEY) as key:
		if value is None:
			winreg.DeleteValue(key, OFFICE_THEME_VALUE)
		else:
			winreg.SetValueEx(key, OFFICE_THEME_VALUE, 0, winreg.REG_DWORD, value)


def markCalloutsSeen(names):
	# Same effect as clicking "OK" once on each bubble; the value is persistent and harmless
	with winreg.CreateKey(winreg.HKEY_CURRENT_USER, TEACHING_CALLOUTS_KEY) as key:
		for name in names:
			try:
				current = winreg.QueryValueEx(key, name)[0]
			except FileNotFoundError:
				current = None
			if current is None or current < TEACHING_CALLOUT_SEEN:
				winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, TEACHING_CALLOUT_SEEN)
				logger.info("Teaching callout %s marked as seen (was %s)", name, current)


class ExcelSession:
	def __init__(self, visible=True, officeTheme=None):
		self.visible = visible
		self.officeTheme = officeTheme
		self.savedTheme = None
		self.themeOverridden = False
		self.app = None
		self.workbook = None
		self.hwnd = None

	def start(self):
		if self.officeTheme is not None:
			# Office reads its theme at startup; the user's value is restored in close()
			self.savedTheme = readOfficeTheme()
			if self.savedTheme != self.officeTheme:
				writeOfficeTheme(self.officeTheme)
				self.themeOverridden = True
				logger.info("Office theme temporarily set to %s (user value %s)", self.officeTheme, self.savedTheme)
		if self.visible:
			try:
				markCalloutsSeen(RECORDING_CALLOUTS)
			except Exception:
				logger.exception("Could not mark teaching callouts as seen")
		# DispatchEx starts a dedicated instance and never hijacks a user's open Excel
		self.app = win32com.client.DispatchEx("Excel.Application")
		self.app.Visible = self.visible
		self.app.DisplayAlerts = False
		self.app.ScreenUpdating = True
		logger.info("Excel %s build %s, UI language %s", self.app.Version, self.app.Build, self.app.LanguageSettings.LanguageID(MSO_LANGUAGE_ID_UI))
		return self

	def describe(self):
		return {"version": str(self.app.Version), "build": int(self.app.Build), "uiLanguage": int(self.app.LanguageSettings.LanguageID(MSO_LANGUAGE_ID_UI))}

	def openCopy(self, sourcePath, workPath):
		workPath = Path(workPath)
		workPath.parent.mkdir(parents=True, exist_ok=True)
		shutil.copyfile(sourcePath, workPath)
		# UpdateLinks=0: the client workbook links to a file on its author's machine, which would raise a modal prompt
		self.workbook = callWithRetry(self.app.Workbooks.Open, str(workPath.resolve()), DONT_UPDATE_LINKS)
		return self.workbook

	def breakExternalLinks(self):
		links = self.workbook.LinkSources(XL_LINK_TYPE_EXCEL_LINKS)
		for link in links or ():
			self.workbook.BreakLink(link, XL_LINK_TYPE_EXCEL_LINKS)
			logger.warning("Broke external link to %s", link)

	def localFormats(self):
		# NumberFormat is parsed with the caller locale through pywin32, so formats are built for NumberFormatLocal
		thousands = self.app.ThousandsSeparator
		decimal = self.app.DecimalSeparator
		return {"currency": f"#{thousands}##0{decimal}00 €", "percent2": f"0{decimal}00%", "percent1": f"0{decimal}0%", "percent0": "0%"}

	def saveAs(self, targetPath):
		targetPath = Path(targetPath).resolve()
		targetPath.parent.mkdir(parents=True, exist_ok=True)
		if targetPath.exists():
			targetPath.unlink()
		callWithRetry(self.workbook.SaveAs, str(targetPath), XL_OPEN_XML_WORKBOOK)
		logger.info("Saved %s", targetPath)

	def sheet(self, name):
		return self.workbook.Worksheets(name)

	def freezeView(self, sheetName, zoom, scrollRow=1, scrollColumn=1, activeCell="A1"):
		sheet = self.sheet(sheetName)
		sheet.Activate()
		window = self.app.ActiveWindow
		window.WindowState = XL_MAXIMIZED
		self.app.DisplayFormulaBar = True
		self.app.DisplayStatusBar = True
		window.DisplayGridlines = True
		window.DisplayHeadings = True
		window.Zoom = zoom
		window.ScrollRow = scrollRow
		window.ScrollColumn = scrollColumn
		sheet.Range(activeCell).Select()
		self.hwnd = int(window.Hwnd)
		return window

	def bringToFront(self, topmost=True):
		try:
			# A synthetic key event gives this process the right to change the foreground window
			win32api.keybd_event(win32con.VK_F24, 0, 0, 0)
			win32api.keybd_event(win32con.VK_F24, 0, win32con.KEYEVENTF_KEYUP, 0)
			win32gui.SetForegroundWindow(self.hwnd)
		except Exception:
			logger.warning("SetForegroundWindow failed, relying on topmost only")
		try:
			insertAfter = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
			win32gui.SetWindowPos(self.hwnd, insertAfter, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
		except Exception:
			logger.exception("SetWindowPos failed")

	def dismissTransientUi(self):
		# The hidden cursor can still trigger hover tooltips, and Escape closes teaching callouts (harmless in Ready mode)
		try:
			area = self.workArea()
			win32api.SetCursorPos((area["x"] + area["w"] // 2, area["y"] + area["h"] - 6))
			if win32gui.GetForegroundWindow() == self.hwnd:
				win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
				win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
		except Exception:
			logger.exception("Could not dismiss transient UI")

	def workArea(self):
		monitor = win32api.MonitorFromWindow(self.hwnd, win32con.MONITOR_DEFAULTTOPRIMARY)
		left, top, right, bottom = win32api.GetMonitorInfo(monitor)["Work"]
		# libx264 with yuv420p needs even dimensions
		return {"x": left, "y": top, "w": (right - left) & ~1, "h": (bottom - top) & ~1}

	def rangeRects(self, sheetName, address, origin):
		pane = self.app.ActiveWindow.ActivePane
		rects = []
		for area in resolveRange(self.sheet(sheetName), address).Areas:
			left = pane.PointsToScreenPixelsX(area.Left)
			top = pane.PointsToScreenPixelsY(area.Top)
			right = pane.PointsToScreenPixelsX(area.Left + area.Width)
			bottom = pane.PointsToScreenPixelsY(area.Top + area.Height)
			rects.append({"address": area.Address.replace("$", ""), "x": left - origin["x"], "y": top - origin["y"], "w": right - left, "h": bottom - top, "check": self.checkPoint(area)})
		return rects

	def checkPoint(self, area):
		# Round-trips the top-left cell centre through RangeFromPoint to validate the conversion
		try:
			firstCell = area.Cells(1, 1)
			pane = self.app.ActiveWindow.ActivePane
			x = pane.PointsToScreenPixelsX(firstCell.Left + firstCell.Width / 2)
			y = pane.PointsToScreenPixelsY(firstCell.Top + firstCell.Height / 2)
			hit = self.app.ActiveWindow.RangeFromPoint(x, y)
			hitAddress = hit.Address if hit is not None and hasattr(hit, "Address") else None
			return "ok" if hitAddress == firstCell.Address else f"mismatch:{hitAddress}"
		except Exception as error:
			return f"error:{error}"

	def close(self):
		if self.hwnd:
			try:
				win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
			except Exception:
				pass
		if self.workbook is not None:
			try:
				self.workbook.Close(False)
			except Exception:
				logger.exception("Workbook close failed")
			self.workbook = None
		if self.app is not None:
			try:
				self.app.Quit()
			except Exception:
				logger.exception("Excel quit failed")
			self.app = None
		if self.themeOverridden:
			try:
				writeOfficeTheme(self.savedTheme)
				self.themeOverridden = False
				logger.info("Office theme restored to %s", self.savedTheme)
			except Exception:
				logger.exception("Could not restore the Office theme (HKCU %s, value %s = %s)", OFFICE_THEME_KEY, OFFICE_THEME_VALUE, self.savedTheme)
