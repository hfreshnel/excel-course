import argparse
import json
import logging
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from video_script import ROW_MARKER_PATTERN, readSpokenItems

SAPI_SCRIPT = Path(__file__).resolve().parent / "sapi_synthesize.ps1"
ROW_GAP_SECONDS = 0.35
SYNTHESIS_TIMEOUT_SECONDS = 900

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("placeholderVoice")


def runSapi(chunks, workDir, rate):
	# System.Speech (.NET) exposes per-word audio offsets; SAPI automation events never reach pywin32 here
	inputPath = workDir / "chunks.json"
	inputPath.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
	command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(SAPI_SCRIPT), "-InputPath", str(inputPath), "-OutputDir", str(workDir), "-Rate", str(rate)]
	completed = subprocess.run(command, capture_output=True, text=True, timeout=SYNTHESIS_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"SAPI synthesis failed ({completed.returncode}): {completed.stderr.strip() or completed.stdout.strip()}")
	logger.info("SAPI: %s", completed.stdout.strip())
	results = json.loads((workDir / "words.json").read_text(encoding="utf-8-sig"))
	if len(results) != len(chunks):
		raise RuntimeError(f"SAPI returned {len(results)} chunks, expected {len(chunks)}")
	return results


def synthesize(scriptPath, outputDir, rate):
	outputDir.mkdir(parents=True, exist_ok=True)
	workDir = outputDir / "chunks.tmp"
	shutil.rmtree(workDir, ignore_errors=True)
	workDir.mkdir()
	items = readSpokenItems(scriptPath)
	chunks = [value for kind, value in items if kind == "text"]
	if not chunks:
		raise RuntimeError(f"{scriptPath}: no spoken text found")
	try:
		results = runSapi(chunks, workDir, rate)
		frames = bytearray()
		params = None
		markers = {}
		words = []
		chunkIndex = 0
		for kind, value in items:
			if kind == "marker":
				# Row markers get a short pause before them so rows breathe like paragraphs
				if ROW_MARKER_PATTERN.match(value) and frames:
					frames.extend(b"\x00" * (int(ROW_GAP_SECONDS * params.framerate) * params.sampwidth * params.nchannels))
				markers[value] = round(len(frames) / (params.framerate * params.sampwidth * params.nchannels), 3) if params else 0.0
				continue
			result = results[chunkIndex]
			chunkIndex += 1
			with wave.open(str(workDir / result["wave"]), "rb") as chunkFile:
				chunkParams = chunkFile.getparams()
				chunkFrames = chunkFile.readframes(chunkFile.getnframes())
			if params is None:
				params = chunkParams
			elif (chunkParams.framerate, chunkParams.sampwidth, chunkParams.nchannels) != (params.framerate, params.sampwidth, params.nchannels):
				raise RuntimeError("SAPI returned chunks with different audio formats")
			bytesPerSecond = params.framerate * params.sampwidth * params.nchannels
			chunkStart = len(frames) / bytesPerSecond
			chunkEnd = (len(frames) + len(chunkFrames)) / bytesPerSecond
			# SAPI may report one word several times (e.g. "E2" as "E" then "2"): keep the first event per character position
			chunkWords = []
			for word in result["words"] or []:
				if not chunkWords or word["position"] != chunkWords[-1]["position"]:
					chunkWords.append(word)
			if not chunkWords:
				logger.warning("No word timings for chunk: %s", value[:60])
			for wordIndex, word in enumerate(chunkWords):
				end = chunkStart + chunkWords[wordIndex + 1]["start"] if wordIndex + 1 < len(chunkWords) else chunkEnd
				words.append({"text": word["text"], "start": round(chunkStart + word["start"], 3), "end": round(end, 3)})
			frames.extend(chunkFrames)
	finally:
		shutil.rmtree(workDir, ignore_errors=True)
	audioPath = outputDir / "audio.wav"
	with wave.open(str(audioPath), "wb") as audioFile:
		audioFile.setparams(params)
		audioFile.writeframes(bytes(frames))
	duration = round(len(frames) / (params.framerate * params.sampwidth * params.nchannels), 3)
	payload = {"source": "placeholder-sapi", "script": scriptPath.as_posix(), "audio": audioPath.name, "duration": duration, "markers": markers, "words": words}
	(outputDir / "markers.json").write_text(json.dumps(payload, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
	logger.info("%s: %d markers, %d words, %.1f s of audio -> %s", scriptPath, len(markers), len(words), duration, outputDir)


def main():
	parser = argparse.ArgumentParser(description="Synthesize a placeholder French voice with SAPI and export marker and word timestamps.")
	parser.add_argument("script", type=Path)
	parser.add_argument("--output-dir", type=Path, help="defaults to <video dir>/recordings/voice")
	parser.add_argument("--rate", type=int, default=1, help="SAPI rate, -10 to 10")
	args = parser.parse_args()
	outputDir = args.output_dir or args.script.parent / "recordings" / "voice"
	try:
		synthesize(args.script, outputDir, args.rate)
	except Exception:
		logger.exception("Placeholder voice synthesis failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
