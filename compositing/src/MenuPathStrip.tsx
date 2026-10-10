import { fadeOpacity, type MenuPath } from "./lesson-data";

const EXCEL_GREEN = "#217346";
const STEP_ENTER_SECONDS = 0.22;

// Option A: the clicks are not performed in Excel, the path is spelled out over the ribbon instead
export const MenuPathStrip: React.FC<{ path: MenuPath; time: number }> = ({ path, time }) => {
	const opacity = fadeOpacity(time, path.start, path.end);
	if (opacity <= 0) {
		return null;
	}
	const reached = path.steps.filter((step) => time >= step.time).length;
	return (
		<div
			style={{
				position: "absolute",
				left: "50%",
				top: 112,
				transform: "translateX(-50%)",
				opacity,
				display: "flex",
				alignItems: "center",
				gap: 16,
				padding: "16px 28px",
				borderRadius: 999,
				backgroundColor: "#FFFFFF",
				boxShadow: "0 14px 40px rgba(10, 20, 40, 0.35)",
				fontFamily: "'Segoe UI', sans-serif",
				fontSize: 36,
				fontWeight: 600,
				whiteSpace: "nowrap",
			}}
		>
			{path.steps.map((step, index) => {
				const progress = Math.max(0, Math.min(1, (time - step.time) / STEP_ENTER_SECONDS));
				if (progress <= 0) {
					return null;
				}
				const current = index === reached - 1;
				return (
					<div key={index} style={{ display: "flex", alignItems: "center", gap: 16, opacity: progress }}>
						{index > 0 ? <span style={{ color: "#8A9099", fontSize: 40 }}>›</span> : null}
						<span
							style={{
								padding: "6px 18px",
								borderRadius: 10,
								backgroundColor: current ? EXCEL_GREEN : "transparent",
								color: current ? "white" : "#1F2329",
							}}
						>
							{step.text}
						</span>
					</div>
				);
			})}
		</div>
	);
};
