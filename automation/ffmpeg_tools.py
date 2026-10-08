import os
import shutil
from pathlib import Path


def findFfmpeg():
	# A fresh winget install only updates PATH for new shells, so also probe the winget links folder
	candidates = [os.environ.get("FFMPEG_PATH"), shutil.which("ffmpeg")]
	localAppData = os.environ.get("LOCALAPPDATA")
	if localAppData:
		candidates.append(str(Path(localAppData) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"))
		packages = Path(localAppData) / "Microsoft" / "WinGet" / "Packages"
		if packages.is_dir():
			candidates.extend(str(path) for path in sorted(packages.glob("Gyan.FFmpeg*/*/bin/ffmpeg.exe"), reverse=True))
	for candidate in candidates:
		if candidate and Path(candidate).is_file():
			return candidate
	raise FileNotFoundError("ffmpeg not found: install it (winget install Gyan.FFmpeg) or set FFMPEG_PATH")


def findFfprobe():
	# ffprobe ships next to ffmpeg in every build we install
	ffmpegPath = Path(findFfmpeg())
	sibling = ffmpegPath.with_name("ffprobe" + ffmpegPath.suffix)
	if sibling.is_file():
		return str(sibling)
	found = shutil.which("ffprobe")
	if found:
		return found
	raise FileNotFoundError(f"ffprobe not found next to {ffmpegPath} nor on PATH")
