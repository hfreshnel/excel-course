import argparse
import json
import logging
import math
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "automation"))
from ffmpeg_tools import findFfmpeg, findFfprobe  # noqa: E402

SAMPLE_RATE = 48000
OUTPUT_CODEC = "pcm_s24le"
HIGHPASS_HZ = 80
TARGET_LUFS = -16.0
TARGET_TRUE_PEAK = -1.5
TARGET_LRA = 11.0
# Speech is brought to this level before compression so the fixed threshold below bites the same way on every recording
PRE_COMPRESSION_LUFS = -20.0
COMPRESSOR = "acompressor=threshold=-18dB:ratio=3:attack=8:release=150:knee=3"
DEESSER = "deesser=i=0.4"
DEFAULT_DENOISE_STRENGTH = 12.0
WINDOW_SAMPLES = 2400
WINDOW_SECONDS = WINDOW_SAMPLES / SAMPLE_RATE
# The quietest windows (pauses between words) give the noise floor; silence is anything close to it
NOISE_FLOOR_PERCENTILE = 0.10
SILENCE_ABOVE_NOISE_DB = 6.0
MIN_SPEECH_ABOVE_SILENCE_DB = 10.0
MIN_SILENCE_SECONDS = 0.6
LIMITER_HEADROOM_DB = 1.0
# Pure digital zeros come out of astats as huge negative values, not -inf
DIGITAL_SILENCE_DB = -120.0
LEADING_SILENCE_TOLERANCE = 0.05
MIN_LEADING_SAMPLE_SECONDS = 0.8
NOISE_SAMPLE_MARGIN = 0.15
NOISE_SAMPLE_MAX_SECONDS = 3.0
MIN_NOISE_SAMPLE_SECONDS = 0.4
TRIM_PADDING_SECONDS = 0.5
CLIPPING_PEAK_DB = -0.1
CLIPPING_MIN_PEAK_COUNT = 10
MIN_SAMPLE_RATE = 44100
LOW_QUALITY_CODECS = {"amr_nb", "amr_wb", "gsm", "gsm_ms", "adpcm_ima_wav"}
LOSSY_CODECS = {"aac", "mp3", "opus", "vorbis", "wmav2"} | LOW_QUALITY_CODECS
QUIET_INPUT_LUFS = -35.0
GOOD_SNR_DB = 45.0
FAIR_SNR_DB = 30.0
POOR_SNR_DB = 20.0
FFMPEG_TIMEOUT_SECONDS = 600

LOUDNORM_JSON_PATTERN = re.compile(r"\{[^{}]*\"input_i\"[^{}]*\}", re.DOTALL)
WINDOW_TIME_PATTERN = re.compile(r"pts_time:\s*(-?[\d.]+)")
WINDOW_RMS_PATTERN = re.compile(r"lavfi\.astats\.Overall\.RMS_level=(\S+)")
ASTATS_PATTERNS = {
	"peakDb": re.compile(r"Peak level dB:\s*(\S+)"),
	"rmsDb": re.compile(r"RMS level dB:\s*(\S+)"),
	"peakCount": re.compile(r"Peak count:\s*(\S+)"),
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("cleanVoice")


def runFfmpeg(ffmpeg, inputPath, filterChain, outputArgs=None):
	command = [ffmpeg, "-hide_banner", "-nostats", "-i", str(inputPath), "-map", "0:a:0", "-af", filterChain]
	command += outputArgs or ["-f", "null", "-"]
	completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=FFMPEG_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		tail = "\n".join(completed.stderr.strip().splitlines()[-8:])
		raise RuntimeError(f"ffmpeg failed ({completed.returncode}) with filters '{filterChain}':\n{tail}")
	return completed.stderr


def toFloat(value):
	try:
		return float(value)
	except (TypeError, ValueError):
		return None


def probeInput(inputPath):
	command = [findFfprobe(), "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate:format=duration,bit_rate", "-of", "json", str(inputPath)]
	completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=FFMPEG_TIMEOUT_SECONDS)
	if completed.returncode != 0:
		raise RuntimeError(f"ffprobe failed on {inputPath}: {completed.stderr.strip()}")
	data = json.loads(completed.stdout)
	if not data.get("streams"):
		raise RuntimeError(f"{inputPath}: no audio stream")
	stream = data["streams"][0]
	fileFormat = data.get("format", {})
	bitRate = toFloat(stream.get("bit_rate")) or toFloat(fileFormat.get("bit_rate"))
	return {
		"codec": stream.get("codec_name"),
		"sampleRate": int(stream.get("sample_rate", 0)),
		"channels": int(stream.get("channels", 0)),
		"bitRateKbps": round(bitRate / 1000) if bitRate else None,
		"duration": round(toFloat(fileFormat.get("duration")) or 0.0, 3),
	}


def baseFilters():
	# Phone files often start at a non-zero timestamp (AAC priming): rebase so command and trim times match file time
	return f"aresample={SAMPLE_RATE},aformat=sample_fmts=fltp:channel_layouts=mono,asetpts=PTS-STARTPTS,highpass=f={HIGHPASS_HZ}"


def parseAstats(stderr):
	stats = {}
	for key, pattern in ASTATS_PATTERNS.items():
		matches = pattern.findall(stderr)
		stats[key] = toFloat(matches[-1]) if matches else None
	return stats


def parseLoudnorm(stderr):
	matches = LOUDNORM_JSON_PATTERN.findall(stderr)
	if not matches:
		raise RuntimeError("loudnorm statistics not found in ffmpeg output")
	return json.loads(matches[-1])


def loudnormMeasure():
	return f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TRUE_PEAK}:LRA={TARGET_LRA}:print_format=json"


def analyzeLevels(ffmpeg, inputPath):
	stderr = runFfmpeg(ffmpeg, inputPath, f"{baseFilters()},astats=measure_perchannel=none,{loudnormMeasure()}")
	stats = parseAstats(stderr)
	loudness = parseLoudnorm(stderr)
	return {
		"peakDb": stats["peakDb"],
		"peakCount": stats["peakCount"],
		"integratedLufs": toFloat(loudness["input_i"]),
		"truePeakDb": toFloat(loudness["input_tp"]),
		"loudnessRange": toFloat(loudness["input_lra"]),
	}


def measureWindows(ffmpeg, inputPath):
	# Short-term RMS per 50 ms window, printed by ametadata in the ffmpeg log
	stderr = runFfmpeg(ffmpeg, inputPath, f"{baseFilters()},asetnsamples=n={WINDOW_SAMPLES}:p=0,astats=metadata=1:reset=1:measure_perchannel=none:measure_overall=RMS_level,ametadata=mode=print:key=lavfi.astats.Overall.RMS_level")
	windows = []
	currentTime = None
	for line in stderr.splitlines():
		timeMatch = WINDOW_TIME_PATTERN.search(line)
		if timeMatch:
			currentTime = float(timeMatch.group(1))
			continue
		rmsMatch = WINDOW_RMS_PATTERN.search(line)
		if rmsMatch and currentTime is not None:
			rms = toFloat(rmsMatch.group(1))
			windows.append((currentTime, rms if rms is not None and rms > DIGITAL_SILENCE_DB else float("-inf")))
			currentTime = None
	if not windows:
		raise RuntimeError("no short-term level could be measured")
	return windows


def estimateNoiseFloor(windows):
	finite = sorted(rms for _, rms in windows if rms != float("-inf"))
	if not finite:
		return float("-inf")
	return finite[int(len(finite) * NOISE_FLOOR_PERCENTILE)]


def findSilences(windows, thresholdDb, duration):
	silences = []
	runStart = None
	for time, rms in windows:
		if rms < thresholdDb:
			if runStart is None:
				runStart = time
		elif runStart is not None:
			if time - runStart >= MIN_SILENCE_SECONDS:
				silences.append((round(runStart, 3), round(time, 3)))
			runStart = None
	if runStart is not None and duration - runStart >= MIN_SILENCE_SECONDS:
		silences.append((round(runStart, 3), round(duration, 3)))
	return silences


def averageRms(windows, start, end):
	powers = [10 ** (rms / 10) for time, rms in windows if start <= time and time + WINDOW_SECONDS <= end and rms != float("-inf")]
	if not powers:
		return float("-inf")
	return round(10 * math.log10(sum(powers) / len(powers)), 1)


def pickNoiseSample(silences):
	# Prefer the leading room tone: the noise profile is then known before the first word
	candidates = [(start, end) for start, end in silences if end - start - 2 * NOISE_SAMPLE_MARGIN >= MIN_NOISE_SAMPLE_SECONDS]
	if not candidates:
		return None
	leading = candidates[0] if candidates[0][0] <= LEADING_SILENCE_TOLERANCE and candidates[0][1] - candidates[0][0] >= MIN_LEADING_SAMPLE_SECONDS else None
	start, end = leading or max(candidates, key=lambda silence: silence[1] - silence[0])
	sampleStart = start + NOISE_SAMPLE_MARGIN
	return (round(sampleStart, 3), round(min(end - NOISE_SAMPLE_MARGIN, sampleStart + NOISE_SAMPLE_MAX_SECONDS), 3))


def speechBounds(silences, duration):
	speechStart = 0.0
	speechEnd = duration
	if silences and silences[0][0] <= LEADING_SILENCE_TOLERANCE:
		speechStart = silences[0][1]
	if silences and silences[-1][1] >= duration - LEADING_SILENCE_TOLERANCE and silences[-1][0] > speechStart:
		speechEnd = silences[-1][0]
	return round(speechStart, 3), round(speechEnd, 3)


def parseSampleRange(text):
	try:
		start, end = (float(part) for part in text.split("-", 1))
	except ValueError:
		raise argparse.ArgumentTypeError(f"expected START-END in seconds, got '{text}'")
	if end - start < MIN_NOISE_SAMPLE_SECONDS:
		raise argparse.ArgumentTypeError(f"noise sample must last at least {MIN_NOISE_SAMPLE_SECONDS} s")
	return (start, end)


def collectWarnings(source, levels, noise):
	warnings = []
	if source["codec"] in LOW_QUALITY_CODECS:
		warnings.append(f"codec {source['codec']} is telephone quality: switch the recorder app to WAV/FLAC or high-quality AAC")
	elif source["codec"] in LOSSY_CODECS:
		warnings.append(f"codec {source['codec']} is lossy ({source['bitRateKbps']} kb/s): acceptable, a lossless setting (WAV/FLAC/ALAC) is better if the app offers it")
	if source["sampleRate"] < MIN_SAMPLE_RATE:
		warnings.append(f"sample rate {source['sampleRate']} Hz is below {MIN_SAMPLE_RATE} Hz: high frequencies are lost for good")
	if levels["peakDb"] is not None and levels["peakDb"] >= CLIPPING_PEAK_DB and (levels["peakCount"] or 0) >= CLIPPING_MIN_PEAK_COUNT:
		warnings.append("clipping detected: saturation cannot be repaired, record again further from the phone or more softly")
	if levels["integratedLufs"] is not None and levels["integratedLufs"] < QUIET_INPUT_LUFS:
		warnings.append(f"recording is quiet ({levels['integratedLufs']:.1f} LUFS): boosting it will raise the noise, move the phone closer")
	snr = noise.get("snrDb")
	if noise.get("gated"):
		warnings.append("pauses are digital silence (recorder noise gate): disable the app's noise reduction if words sound cut")
	elif snr is None:
		warnings.append("no pause long enough to measure background noise: leave 2 s of silence at the start of each recording")
	elif snr < POOR_SNR_DB:
		warnings.append(f"background noise is high (SNR ~{snr:.0f} dB): record in a quieter, softer room; local denoising will leave artifacts")
	elif snr < FAIR_SNR_DB:
		warnings.append(f"background noise is audible (SNR ~{snr:.0f} dB): denoising will help, Adobe Enhance Speech will do better")
	return warnings


def snrVerdict(snr):
	if snr is None:
		return "unknown"
	if snr >= GOOD_SNR_DB:
		return "good"
	if snr >= FAIR_SNR_DB:
		return "fair"
	return "poor"


def analyze(ffmpeg, inputPath, manualSample):
	source = probeInput(inputPath)
	levels = analyzeLevels(ffmpeg, inputPath)
	speechLufs = levels["integratedLufs"]
	if speechLufs is None or speechLufs == float("-inf"):
		raise RuntimeError(f"{inputPath}: no audible signal")
	windows = measureWindows(ffmpeg, inputPath)
	noiseFloor = estimateNoiseFloor(windows)
	thresholdDb = min(noiseFloor + SILENCE_ABOVE_NOISE_DB, speechLufs - MIN_SPEECH_ABOVE_SILENCE_DB)
	silences = findSilences(windows, thresholdDb, source["duration"])
	sample = manualSample or pickNoiseSample(silences)
	noiseRms = averageRms(windows, sample[0], sample[1]) if sample else None
	# Some phones gate pauses to digital silence: there is nothing to learn or remove there
	gated = noiseRms == float("-inf")
	if gated:
		noiseRms = None
	snr = round(speechLufs - noiseRms, 1) if noiseRms is not None else None
	noise = {
		"floorDb": round(noiseFloor, 1) if noiseFloor != float("-inf") else None,
		"silenceThresholdDb": round(thresholdDb, 1),
		"sample": sample,
		"sampleSource": "manual" if manualSample else ("auto" if sample else None),
		"rmsDb": noiseRms,
		"snrDb": snr,
		"gated": gated,
		"verdict": "gated" if gated else snrVerdict(snr),
	}
	speechStart, speechEnd = speechBounds(silences, source["duration"])
	return {
		"source": source,
		"levels": levels,
		"noise": noise,
		"speech": {"start": speechStart, "end": speechEnd, "silenceCount": len(silences)},
		"warnings": collectWarnings(source, levels, noise),
	}


def cleaningFilters(plan, gainDb=None, finalGainDb=None, measure=False):
	filters = [baseFilters()]
	if plan["denoise"] == "sampled":
		sampleStart, sampleEnd = plan["noiseSample"]
		# afftdn learns the noise profile between the two commands, then subtracts it everywhere (ffmpeg afftdn docs)
		filters += [f"asendcmd=c='{sampleStart:.3f} afftdn@denoise sn start'", f"asendcmd=c='{sampleEnd:.3f} afftdn@denoise sn stop'", f"afftdn@denoise=nr={plan['denoiseStrength']}"]
	elif plan["denoise"] == "tracked":
		filters.append(f"afftdn=nr={plan['denoiseStrength']}:tn=1")
	if plan["trim"]:
		filters.append(f"atrim=start={plan['trim'][0]}:end={plan['trim'][1]},asetpts=PTS-STARTPTS")
	if gainDb is not None:
		filters += [f"volume={gainDb:.2f}dB", DEESSER, COMPRESSOR]
	if finalGainDb is not None:
		# Static gain + peak limiter instead of loudnorm, whose dynamic fallback pumps; the margin covers inter-sample peaks
		limit = 10 ** ((TARGET_TRUE_PEAK - LIMITER_HEADROOM_DB) / 20)
		filters += [f"volume={finalGainDb:.2f}dB", f"alimiter=limit={limit:.4f}:level=false:latency=true"]
	if measure:
		filters.append(loudnormMeasure())
	return ",".join(filters)


def buildPlan(report, args):
	plan = {"denoise": "off", "noiseSample": None, "denoiseStrength": args.denoise_strength, "trim": None}
	if report["noise"]["gated"]:
		logger.info("Pauses are digital silence: denoising skipped")
	elif not args.no_denoise:
		if report["noise"]["sample"]:
			plan["denoise"] = "sampled"
			plan["noiseSample"] = report["noise"]["sample"]
		else:
			plan["denoise"] = "tracked"
			logger.warning("No noise sample available: falling back to adaptive noise tracking (less precise)")
	if not args.no_trim:
		duration = report["source"]["duration"]
		trimStart = max(0.0, report["speech"]["start"] - TRIM_PADDING_SECONDS)
		trimEnd = min(duration, report["speech"]["end"] + TRIM_PADDING_SECONDS)
		if trimStart > 0 or trimEnd < duration:
			plan["trim"] = (round(trimStart, 3), round(trimEnd, 3))
	return plan


def clean(ffmpeg, inputPath, outputPath, report, plan):
	firstPass = parseLoudnorm(runFfmpeg(ffmpeg, inputPath, cleaningFilters(plan, measure=True)))
	gainDb = PRE_COMPRESSION_LUFS - float(firstPass["input_i"])
	secondPass = parseLoudnorm(runFfmpeg(ffmpeg, inputPath, cleaningFilters(plan, gainDb=gainDb, measure=True)))
	finalGainDb = TARGET_LUFS - float(secondPass["input_i"])
	outputPath.parent.mkdir(parents=True, exist_ok=True)
	runFfmpeg(ffmpeg, inputPath, cleaningFilters(plan, gainDb=gainDb, finalGainDb=finalGainDb), ["-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", OUTPUT_CODEC, "-y", str(outputPath)])
	final = parseLoudnorm(runFfmpeg(ffmpeg, outputPath, loudnormMeasure()))
	report["processing"] = {
		"denoise": plan["denoise"],
		"noiseSample": plan["noiseSample"],
		"denoiseStrength": plan["denoiseStrength"] if plan["denoise"] != "off" else None,
		"trim": plan["trim"],
		"preCompressionGainDb": round(gainDb, 2),
		"finalGainDb": round(finalGainDb, 2),
	}
	report["output"] = {
		"path": outputPath.name,
		"sampleRate": SAMPLE_RATE,
		"codec": OUTPUT_CODEC,
		"integratedLufs": toFloat(final["input_i"]),
		"truePeakDb": toFloat(final["input_tp"]),
		"loudnessRange": toFloat(final["input_lra"]),
	}


def logReport(report):
	source = report["source"]
	levels = report["levels"]
	noise = report["noise"]
	logger.info("Source: %s, %d Hz, %d ch, %s kb/s, %.1f s", source["codec"], source["sampleRate"], source["channels"], source["bitRateKbps"] or "?", source["duration"])
	logger.info("Levels: %.1f LUFS, true peak %.1f dBTP, LRA %.1f LU", levels["integratedLufs"], levels["truePeakDb"], levels["loudnessRange"])
	if noise["sample"] and not noise["gated"]:
		logger.info("Noise: %s dBFS RMS over %.2f-%.2f s (%s), floor %s dBFS, SNR ~%s dB -> %s", noise["rmsDb"], noise["sample"][0], noise["sample"][1], noise["sampleSource"], noise["floorDb"], noise["snrDb"], noise["verdict"])
	logger.info("Speech: %.2f-%.2f s", report["speech"]["start"], report["speech"]["end"])
	if "output" in report:
		output = report["output"]
		processing = report["processing"]
		logger.info("Processing: denoise %s, trim %s, gain %+.1f dB before compression, %+.1f dB after", processing["denoise"], processing["trim"] or "none", processing["preCompressionGainDb"], processing["finalGainDb"])
		logger.info("Output: %.1f LUFS, true peak %.1f dBTP, LRA %.1f LU", output["integratedLufs"], output["truePeakDb"], output["loudnessRange"])
	for warning in report["warnings"]:
		logger.warning(warning)


def main():
	parser = argparse.ArgumentParser(description="Diagnose a voice recording and clean it: high-pass, denoise, trim, de-ess, compress and normalize to a fixed loudness.")
	parser.add_argument("input", type=Path, help="raw recording in any format ffmpeg reads (m4a, wav, mp3...)")
	parser.add_argument("--output", type=Path, help="defaults to <input dir>/<input name>-clean.wav")
	parser.add_argument("--analyze-only", action="store_true", help="print the diagnosis without writing audio")
	parser.add_argument("--no-denoise", action="store_true", help="skip denoising (input already cleaned, e.g. by Adobe Enhance Speech)")
	parser.add_argument("--noise-sample", type=parseSampleRange, help="START-END in seconds of pure room tone, overrides auto-detection")
	parser.add_argument("--denoise-strength", type=float, default=DEFAULT_DENOISE_STRENGTH, help="noise reduction in dB (afftdn nr); higher removes more noise but sounds more artificial")
	parser.add_argument("--no-trim", action="store_true", help="keep leading and trailing silence")
	args = parser.parse_args()
	inputPath = args.input.resolve()
	outputPath = (args.output or inputPath.with_name(f"{inputPath.stem}-clean.wav")).resolve()
	try:
		if not inputPath.is_file():
			raise FileNotFoundError(f"{inputPath} not found")
		if outputPath == inputPath:
			raise ValueError("output would overwrite the input recording")
		ffmpeg = findFfmpeg()
		report = analyze(ffmpeg, inputPath, args.noise_sample)
		report["input"] = inputPath.name
		if not args.analyze_only:
			plan = buildPlan(report, args)
			clean(ffmpeg, inputPath, outputPath, report, plan)
			reportPath = outputPath.with_suffix(".report.json")
			reportPath.write_text(json.dumps(report, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
			logger.info("Cleaned audio -> %s (report: %s)", outputPath, reportPath.name)
		logReport(report)
	except Exception:
		logger.exception("Voice cleaning failed")
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
