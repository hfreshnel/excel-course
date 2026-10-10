import { fadeOpacity, type Callout } from "./lesson-data";

const EXCEL_GREEN = "#217346";
const LINE_ENTER_SECONDS = 0.25;
// Capture pixels at 90 % zoom: the table (columns A to M) ends near x = 1220 and the avatar starts near x = 1610, y = 630.
// "right": beside the table, below row 1 and above the avatar (about 290 px high at most).
// "rightColumn": narrower, between the table and the avatar, down to row 31 (long lists).
// "center": over the grid, where Excel would open a dialog box; anchored below the formula bar, clear of a menu path.
const POSITIONS: Record<Callout["position"], React.CSSProperties> = {
	right: { right: 40, top: 340, width: 600 },
	rightColumn: { left: 1235, top: 320, width: 375 },
	center: { left: "50%", top: 240, transform: "translateX(-50%)", minWidth: 720 },
};

export const CalloutBox: React.FC<{ callout: Callout; time: number }> = ({ callout, time }) => {
	const opacity = fadeOpacity(time, callout.start, callout.end);
	if (opacity <= 0) {
		return null;
	}
	const hasDetails = callout.lines.some((line) => line.detail);
	const detailSize = callout.position === "right" ? 30 : 26;
	return (
		<div
			style={{
				position: "absolute",
				...POSITIONS[callout.position],
				opacity,
				padding: "26px 34px 30px",
				borderRadius: 18,
				borderLeft: `10px solid ${EXCEL_GREEN}`,
				backgroundColor: "#FFFFFF",
				boxShadow: "0 18px 50px rgba(10, 20, 40, 0.3)",
				fontFamily: "'Segoe UI', sans-serif",
				color: "#1F2329",
				boxSizing: "border-box",
			}}
		>
			{callout.title ? <div style={{ marginBottom: 16, color: EXCEL_GREEN, fontSize: 28, fontWeight: 700, letterSpacing: 0.5 }}>{callout.title}</div> : null}
			<div style={{ display: "grid", gridTemplateColumns: hasDetails ? "auto 1fr" : "1fr", columnGap: callout.position === "rightColumn" ? 22 : 34, rowGap: hasDetails ? 4 : 12 }}>
				{callout.lines.map((line, index) => {
					const progress = Math.max(0, Math.min(1, (time - line.time) / LINE_ENTER_SECONDS));
					const style: React.CSSProperties = { opacity: progress, transform: `translateX(${(1 - progress) * 14}px)` };
					const textStyle: React.CSSProperties =
						line.kind === "formula"
							? { fontFamily: "Consolas, 'Cascadia Mono', monospace", fontSize: hasDetails ? detailSize : 44, fontWeight: 600 }
							: { fontSize: hasDetails ? detailSize : 36, fontWeight: 500 };
					return (
						<div key={index} style={{ display: "contents" }}>
							<div style={{ ...style, ...textStyle }}>{line.text}</div>
							{hasDetails ? <div style={{ ...style, fontFamily: "Consolas, 'Cascadia Mono', monospace", fontSize: detailSize - 2, color: "#5F6670", alignSelf: "center" }}>{line.detail}</div> : null}
						</div>
					);
				})}
			</div>
		</div>
	);
};
