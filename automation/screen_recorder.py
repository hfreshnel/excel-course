import logging
import subprocess
import threading
import time
from pathlib import Path

logger = logging.getLogger("screenRecorder")


def normalizeCapture(ffmpegPath, rawPath, outputPath, frameRate=30):
	# gdigrab stamps frames with the wall clock, so dropped frames leave holes (variable frame rate).
	# Remotion's compositor needs a frame at every position: re-encode at a constant rate,
	# with a keyframe every second for fast seeking.
	command = [
		ffmpegPath, "-hide_banner", "-loglevel", "warning", "-y", "-i", str(rawPath),
		"-fps_mode", "cfr", "-r", str(frameRate),
		"-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-g", str(frameRate),
		"-movflags", "+faststart", str(outputPath),
	]
	logger.info("Normalizing capture to %d fps CFR -> %s", frameRate, outputPath)
	subprocess.run(command, check=True)


class ScreenRecorder:
	def __init__(self, ffmpegPath, outputPath, area, frameRate=30):
		self.ffmpegPath = ffmpegPath
		self.outputPath = Path(outputPath)
		self.area = area
		self.frameRate = frameRate
		self.process = None
		self.captureStart = None
		self.firstProgress = threading.Event()
		self.stderrFile = None

	def buildCommand(self):
		area = self.area
		return [
			self.ffmpegPath, "-hide_banner", "-loglevel", "warning", "-nostats",
			"-progress", "pipe:1", "-stats_period", "0.1",
			"-f", "gdigrab", "-framerate", str(self.frameRate), "-draw_mouse", "0",
			"-offset_x", str(area["x"]), "-offset_y", str(area["y"]), "-video_size", f"{area['w']}x{area['h']}",
			"-i", "desktop",
			"-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-crf", "16", "-pix_fmt", "yuv420p",
			"-y", str(self.outputPath),
		]

	def readProgress(self):
		# ffmpeg reports out_time_us = media time already captured; the first report anchors capture start on our clock
		try:
			for rawLine in self.process.stdout:
				line = rawLine.decode("ascii", "ignore").strip()
				if not self.firstProgress.is_set() and line.startswith("out_time_us="):
					value = line.split("=", 1)[1]
					if value.isdigit() and int(value) > 0:
						self.captureStart = time.perf_counter() - int(value) / 1_000_000
						self.firstProgress.set()
		except Exception:
			logger.exception("Progress reader stopped")

	def start(self, timeoutSeconds=15):
		self.outputPath.parent.mkdir(parents=True, exist_ok=True)
		self.stderrFile = open(self.outputPath.with_suffix(".ffmpeg.log"), "wb")
		command = self.buildCommand()
		logger.info("Starting capture: %s", " ".join(command))
		self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderrFile, creationflags=subprocess.CREATE_NO_WINDOW)
		threading.Thread(target=self.readProgress, daemon=True).start()
		if not self.firstProgress.wait(timeoutSeconds):
			self.stop()
			raise RuntimeError(f"ffmpeg produced no frame within {timeoutSeconds} s, see {self.stderrFile.name}")
		logger.info("Capture running")
		return self.captureStart

	def stop(self, timeoutSeconds=30):
		if self.process is None:
			return
		try:
			if self.process.poll() is None:
				# "q" on stdin lets ffmpeg finalize the MP4 (moov atom); killing it would corrupt the file
				self.process.stdin.write(b"q")
				self.process.stdin.flush()
				self.process.wait(timeoutSeconds)
		except Exception:
			logger.exception("Graceful ffmpeg stop failed, killing it")
			self.process.kill()
		finally:
			if self.stderrFile:
				self.stderrFile.close()
			logger.info("Capture stopped with exit code %s -> %s", self.process.returncode, self.outputPath)
			self.process = None
