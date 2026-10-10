import { interpolate } from "remotion";
import { fadeOpacity, type StepBanner as StepBannerData } from "./lesson-data";

const EXCEL_GREEN = "#217346";
const SLIDE_PIXELS = 40;

// Sits over the ribbon, which carries no content of the lesson (option A: nothing is clicked there)
export const StepBanner: React.FC<{ banner: StepBannerData; time: number }> = ({ banner, time }) => {
	const opacity = fadeOpacity(time, banner.start, banner.end);
	if (opacity <= 0) {
		return null;
	}
	const offset = interpolate(opacity, [0, 1], [-SLIDE_PIXELS, 0]);
	return (
		<div
			style={{
				position: "absolute",
				left: "50%",
				top: 70,
				transform: `translate(-50%, ${offset}px)`,
				opacity,
				display: "flex",
				alignItems: "stretch",
				borderRadius: 18,
				overflow: "hidden",
				backgroundColor: "#FFFFFF",
				boxShadow: "0 18px 50px rgba(10, 20, 40, 0.35)",
				fontFamily: "'Segoe UI', sans-serif",
				whiteSpace: "nowrap",
			}}
		>
			<div style={{ display: "flex", alignItems: "center", padding: "0 30px", backgroundColor: EXCEL_GREEN, color: "white", fontSize: 30, fontWeight: 700, letterSpacing: 1 }}>
				{banner.step.toUpperCase()}
			</div>
			<div style={{ display: "flex", alignItems: "center", gap: 18, padding: "22px 38px", color: "#1F2329", fontSize: 46, fontWeight: 600 }}>
				{banner.done ? <span style={{ color: EXCEL_GREEN, fontSize: 50 }}>✓</span> : null}
				<span>{banner.title}</span>
			</div>
		</div>
	);
};
