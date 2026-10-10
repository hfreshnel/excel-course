import type { PixelRect } from "./lesson-data";

const DEFAULT_COLOR = "255, 179, 0";
const PADDING = 2;

export const HighlightBox: React.FC<{ rect: PixelRect; opacity: number; strong?: boolean; color?: string }> = ({ rect, opacity, strong = false, color = DEFAULT_COLOR }) => (
	<div
		style={{
			position: "absolute",
			left: rect.x - PADDING,
			top: rect.y - PADDING,
			width: rect.w + PADDING * 2,
			height: rect.h + PADDING * 2,
			opacity,
			borderRadius: 4,
			border: `${strong ? 4 : 3}px solid rgb(${color})`,
			backgroundColor: `rgba(${color}, ${strong ? 0.12 : 0.22})`,
			boxShadow: `0 0 18px rgba(${color}, 0.55)`,
			boxSizing: "border-box",
		}}
	/>
);
