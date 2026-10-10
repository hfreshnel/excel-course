import { interpolate } from "remotion";
import { fadeOpacity, type TitleCard as TitleCardData } from "./lesson-data";

const EXCEL_GREEN = "#217346";

// Full-frame plate over the capture: opening title, transitions
export const TitleCard: React.FC<{ card: TitleCardData; time: number }> = ({ card, time }) => {
	const opacity = fadeOpacity(time, card.start, card.end);
	if (opacity <= 0) {
		return null;
	}
	const rise = interpolate(opacity, [0, 1], [24, 0]);
	return (
		<div
			style={{
				position: "absolute",
				inset: 0,
				opacity,
				display: "flex",
				flexDirection: "column",
				alignItems: "center",
				justifyContent: "center",
				gap: 26,
				background: `radial-gradient(circle at 50% 40%, #2C6E49 0%, ${EXCEL_GREEN} 35%, #0F3B24 100%)`,
				fontFamily: "'Segoe UI', sans-serif",
				color: "white",
				textAlign: "center",
			}}
		>
			{card.kicker ? <div style={{ fontSize: 34, fontWeight: 600, letterSpacing: 4, textTransform: "uppercase", opacity: 0.85, transform: `translateY(${rise}px)` }}>{card.kicker}</div> : null}
			<div style={{ fontSize: 92, fontWeight: 700, lineHeight: 1.1, maxWidth: 1500, transform: `translateY(${rise}px)` }}>{card.title}</div>
			{card.subtitle ? <div style={{ fontSize: 40, fontWeight: 500, opacity: 0.9, transform: `translateY(${rise * 1.5}px)` }}>{card.subtitle}</div> : null}
		</div>
	);
};
