import type { PixelRect } from "./lesson-data";

const BLUR_PIXELS = 3;
const DIM_COLOR = "rgba(24, 28, 36, 0.14)";
const PADDING = 4;

// Four bands around the target cell carry the backdrop blur, so the capture is decoded only once
export const FocusBlur: React.FC<{ rect: PixelRect; width: number; height: number; opacity: number }> = ({ rect, width, height, opacity }) => {
	const left = Math.max(0, rect.x - PADDING);
	const top = Math.max(0, rect.y - PADDING);
	const right = Math.min(width, rect.x + rect.w + PADDING);
	const bottom = Math.min(height, rect.y + rect.h + PADDING);
	const bands = [
		{ left: 0, top: 0, width, height: top },
		{ left: 0, top: bottom, width, height: height - bottom },
		{ left: 0, top, width: left, height: bottom - top },
		{ left: right, top, width: width - right, height: bottom - top },
	];
	return (
		<>
			{bands.map((band, index) => (
				<div
					key={index}
					style={{
						position: "absolute",
						...band,
						opacity,
						backdropFilter: `blur(${BLUR_PIXELS}px)`,
						backgroundColor: DIM_COLOR,
					}}
				/>
			))}
		</>
	);
};
