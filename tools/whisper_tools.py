import ctypes
import json
import logging
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import numpy

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "automation"))
from ffmpeg_tools import findFfmpeg  # noqa: E402

# The Hugging Face cache works without symlinks on Windows, only less compactly
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

DEFAULT_MODEL = "medium"
LANGUAGE = "fr"
CACHE_VERSION = 2
# CTranslate2 needs cuBLAS 12 and cuDNN 9 on Windows (faster-whisper README, "GPU"); without them it runs on CPU
CUDA_DLLS = ("cublas64_12.dll", "cudnn64_9.dll")
CPU_COMPUTE_TYPE = "int8"
GPU_COMPUTE_TYPE = "float16"
# Short pauses must survive: the VAD only skips long silences, word timestamps come from the decoder
VAD_PARAMETERS = {"min_silence_duration_ms": 700, "speech_pad_ms": 300}
BEAM_SIZE = 5
# No initial prompt: Whisper reads it as text already spoken and skips those sentences when they open the audio
WHISPER_SAMPLE_RATE = 16000
DECODE_TIMEOUT_SECONDS = 600

# Whisper writes "44 %", "41,80 €" or "3" where the script says "44 pour cent", "41 euros 80" or "trois":
# both sides are reduced to the same keys so the comparison ignores the spelling
SYMBOL_WORDS = {"%": " pour cent ", "€": " euros ", "&": " et ", "+": " plus ", "=": " égal "}
NUMBER_WORDS = {
	"zero": "0", "un": "1", "une": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9",
	"dix": "10", "onze": "11", "douze": "12", "treize": "13", "quatorze": "14", "quinze": "15", "seize": "16", "vingt": "20", "trente": "30",
	"quarante": "40", "cinquante": "50", "soixante": "60", "cent": "100", "premier": "1", "premiere": "1",
}
# Spellings Whisper uses for words of the scripts
KEY_ALIASES = {"ctrl": "controle"}
# Whisper writes prices "41,80 €" where the scripts say "41 euros 80"
PRICE_PATTERN = re.compile(r"(\d+)\s?,(\d{2})\s*(?:€|euros?)")
KEY_SPLIT_PATTERN = re.compile(r"[\s'’\-]+|(?<=\d)[,.](?=\d)")
KEY_STRIP_PATTERN = re.compile(r"[^a-z0-9]+")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

logger = logging.getLogger("whisperTools")
LOADED_MODELS = {}


def stripAccents(text):
	return "".join(char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn")


def wordKeys(text):
	text = PRICE_PATTERN.sub(r"\1 euros \2", text)
	for symbol, spoken in SYMBOL_WORDS.items():
		text = text.replace(symbol, spoken)
	keys = []
	for part in KEY_SPLIT_PATTERN.split(stripAccents(text.lower())):
		key = KEY_STRIP_PATTERN.sub("", part)
		if key:
			keys.append(NUMBER_WORDS.get(key, KEY_ALIASES.get(key, key)))
	return keys


def registerPipCudaDlls():
	# pip packages nvidia-cublas-cu12 / nvidia-cudnn-cu12 drop their DLLs under site-packages/nvidia/*/bin
	for sitePath in sys.path:
		nvidiaDir = Path(sitePath) / "nvidia"
		if not nvidiaDir.is_dir():
			continue
		for binDir in nvidiaDir.glob("*/bin"):
			try:
				os.add_dll_directory(str(binDir))
				os.environ["PATH"] = str(binDir) + os.pathsep + os.environ.get("PATH", "")
			except OSError as error:
				logger.warning("Cannot register CUDA DLL folder %s: %s", binDir, error)


def cudaAvailable():
	try:
		import ctranslate2
		if ctranslate2.get_cuda_device_count() < 1:
			return False
	except Exception as error:
		logger.warning("CUDA probe failed: %s", error)
		return False
	registerPipCudaDlls()
	# A missing DLL makes CTranslate2 abort the process mid-transcription, so check before loading the model
	for name in CUDA_DLLS:
		try:
			ctypes.WinDLL(name)
		except OSError:
			logger.info("%s not found: transcribing on CPU", name)
			return False
	return True


def decodeAudio(audioPath, sampleRate):
	# Same decoding as the editing tools (ffmpeg, AAC priming rebased to zero), so every tool shares one time base.
	# It also avoids faster-whisper's PyAV decoder, which breaks with PyAV 19 (unknown "metadata_errors" argument).
	command = [findFfmpeg(), "-hide_banner", "-nostats", "-loglevel", "error", "-i", str(audioPath), "-map", "0:a:0", "-af", "aformat=channel_layouts=mono,asetpts=PTS-STARTPTS", "-ar", str(sampleRate), "-f", "f32le", "-"]
	completed = subprocess.run(command, capture_output=True, timeout=DECODE_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"ffmpeg could not decode {audioPath}: {completed.stderr.decode('utf-8', 'replace').strip()}")
	samples = numpy.frombuffer(completed.stdout, dtype=numpy.float32)
	if samples.size == 0:
		raise RuntimeError(f"{audioPath}: no audio decoded")
	return samples


def resolveDevice(device):
	if device == "auto":
		device = "cuda" if cudaAvailable() else "cpu"
	return device, GPU_COMPUTE_TYPE if device == "cuda" else CPU_COMPUTE_TYPE


def cachePath(audioPath, model):
	return audioPath.with_name(f"{audioPath.stem}.whisper-{model}.json")


def cacheKey(audioPath, model):
	stat = audioPath.stat()
	return {"version": CACHE_VERSION, "size": stat.st_size, "mtimeNs": stat.st_mtime_ns, "model": model}


def loadModel(model, deviceName, computeType):
	# Loaded once per process: sentence-by-sentence checks call Whisper hundreds of times
	key = (model, deviceName, computeType)
	if key not in LOADED_MODELS:
		from faster_whisper import WhisperModel
		logger.info("Loading Whisper %s on %s (%s)", model, deviceName, computeType)
		LOADED_MODELS[key] = WhisperModel(model, device=deviceName, compute_type=computeType)
	return LOADED_MODELS[key]


def transcribeWords(audioPath, model=DEFAULT_MODEL, device="auto", useCache=True):
	audioPath = Path(audioPath).resolve()
	if not audioPath.is_file():
		raise FileNotFoundError(audioPath)
	cacheFile = cachePath(audioPath, model)
	key = cacheKey(audioPath, model)
	if useCache and cacheFile.is_file():
		try:
			cached = json.loads(cacheFile.read_text(encoding="utf-8"))
			if cached.get("key") == key:
				logger.info("Transcription loaded from cache %s", cacheFile.name)
				return cached
		except (OSError, ValueError) as error:
			logger.warning("Ignoring unreadable cache %s: %s", cacheFile, error)
	deviceName, computeType = resolveDevice(device)
	whisper = loadModel(model, deviceName, computeType)
	started = time.perf_counter()
	# condition_on_previous_text=False limits repetition loops and keeps retakes from being merged away
	segments, info = whisper.transcribe(
		decodeAudio(audioPath, WHISPER_SAMPLE_RATE),
		language=LANGUAGE,
		beam_size=BEAM_SIZE,
		word_timestamps=True,
		vad_filter=True,
		vad_parameters=VAD_PARAMETERS,
		condition_on_previous_text=False,
	)
	words = []
	segmentList = []
	for segment in segments:
		segmentList.append({"start": round(segment.start, 3), "end": round(segment.end, 3), "text": segment.text.strip()})
		for word in segment.words or []:
			text = word.word.strip()
			if text:
				words.append({"text": text, "start": round(word.start, 3), "end": round(word.end, 3), "probability": round(word.probability, 3)})
		logger.debug("  %7.2f-%7.2f %s", segment.start, segment.end, segment.text.strip())
	elapsed = time.perf_counter() - started
	logger.info("Transcribed %.1f s of audio in %.1f s (%d words)", info.duration, elapsed, len(words))
	result = {
		"key": key,
		"audio": audioPath.name,
		"model": model,
		"device": deviceName,
		"computeType": computeType,
		"language": info.language,
		"duration": round(info.duration, 3),
		"elapsedSeconds": round(elapsed, 1),
		"segments": segmentList,
		"words": words,
	}
	try:
		cacheFile.write_text(json.dumps(result, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
	except OSError as error:
		logger.warning("Cannot write transcription cache %s: %s", cacheFile, error)
	return result
