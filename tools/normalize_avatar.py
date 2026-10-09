import argparse
import json
import logging
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = REPO_ROOT / "assets" / "avatar" / "poses"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "assets" / "avatar" / "normalized"
CANVAS_WIDTH = 1024
CANVAS_HEIGHT = 1536
# GPT exports the character at alpha 250-254 and leaves faint noise (alpha 1-8) all over the background
ALPHA_OPAQUE_MIN = 250
ALPHA_CLEAR_MAX = 8
# Semi-transparent pixels farther than this from the opaque character are halo, not anti-aliasing
HALO_RADIUS = 4
POSE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
ALPHA_LUT = [255 if value >= ALPHA_OPAQUE_MIN else 0 if value <= ALPHA_CLEAR_MAX else value for value in range(256)]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("normalizeAvatar")


def cleanAlpha(alpha):
	opaqueMask = alpha.point(lambda value: 255 if value >= ALPHA_OPAQUE_MIN else 0)
	neighbourhood = opaqueMask.filter(ImageFilter.MaxFilter(HALO_RADIUS * 2 + 1))
	# The neighbourhood mask is 0 or 255, so multiplying keeps edge anti-aliasing and drops distant halo
	return ImageChops.multiply(alpha.point(ALPHA_LUT), neighbourhood)


def fitCanvas(image):
	# Framing is kept as generated (option A): only the canvas size is unified, anchored at the bottom
	# edge where the waist-up character is cut by the frame
	if image.width != CANVAS_WIDTH:
		height = round(image.height * CANVAS_WIDTH / image.width)
		image = image.resize((CANVAS_WIDTH, height), Image.Resampling.LANCZOS)
	if image.height == CANVAS_HEIGHT:
		return image
	canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
	canvas.paste(image, (0, CANVAS_HEIGHT - image.height))
	return canvas


def normalizePose(sourcePath, outputPath):
	with Image.open(sourcePath) as source:
		image = source.convert("RGBA")
	originalSize = image.size
	originalAlpha = image.getchannel("A")
	alpha = cleanAlpha(originalAlpha)
	changedPixels = sum(ImageChops.difference(originalAlpha, alpha).histogram()[1:])
	image.putalpha(alpha)
	# Colour left in fully transparent pixels shows up as a glow in tools that ignore alpha
	visibleMask = alpha.point(lambda value: 255 if value else 0)
	image = Image.composite(image, Image.new("RGBA", image.size, (0, 0, 0, 0)), visibleMask)
	image = fitCanvas(image)
	bbox = image.getchannel("A").getbbox()
	if bbox is None:
		raise ValueError(f"{sourcePath.name}: the image is fully transparent after cleaning")
	image.save(outputPath, format="PNG")
	left, top, right, bottom = bbox
	logger.info("%s: %dx%d -> %dx%d, %d alpha values fixed, character box x %d-%d y %d-%d", sourcePath.name, *originalSize, *image.size, changedPixels, left, right - 1, top, bottom - 1)
	return {"src": outputPath.name, "bbox": {"x": left, "y": top, "w": right - left, "h": bottom - top}}


def main():
	parser = argparse.ArgumentParser(description="Normalize the GPT avatar poses: clean alpha, remove halo, unify the canvas size.")
	parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
	parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
	args = parser.parse_args()
	sourcePaths = sorted(args.source.glob("*.png"))
	if not sourcePaths:
		logger.error("No PNG pose found in %s", args.source)
		return 1
	args.output.mkdir(parents=True, exist_ok=True)
	poses = {}
	failures = 0
	for sourcePath in sourcePaths:
		poseId = sourcePath.stem
		if not POSE_ID_PATTERN.match(poseId):
			logger.error("%s: pose id must be lowercase kebab-case, skipped", sourcePath.name)
			failures += 1
			continue
		try:
			poses[poseId] = normalizePose(sourcePath, args.output / sourcePath.name)
		except Exception:
			logger.exception("%s: normalization failed", sourcePath.name)
			failures += 1
	manifest = {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT, "poses": poses}
	manifestPath = args.output / "manifest.json"
	try:
		manifestPath.write_text(json.dumps(manifest, indent="\t") + "\n", encoding="utf-8")
	except OSError:
		logger.exception("Cannot write %s", manifestPath)
		return 1
	logger.info("%d poses normalized, %d failures -> %s", len(poses), failures, manifestPath)
	return 1 if failures else 0


if __name__ == "__main__":
	sys.exit(main())
