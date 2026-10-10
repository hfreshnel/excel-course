import { Img, interpolate, staticFile } from "remotion";
import { fadeOpacity, type ImageOverlay as ImageOverlayData } from "./lesson-data";

const EXCEL_GREEN = "#217346";
// Same anchors as the callouts: "center" over the grid (where a dialog would open), "right" beside the table
const POSITIONS: Record<ImageOverlayData["position"], React.CSSProperties> = {
	center: { left: "50%", top: 250, width: 1060, transform: "translateX(-50%)" },
	right: { right: 40, top: 300, width: 600 },
	// Leaves the right column to a callout shown at the same time
	left: { left: 40, top: 250, width: 1100 },
};

export const ImageOverlay: React.FC<{ image: ImageOverlayData; time: number }> = ({ image, time }) => {
	const opacity = fadeOpacity(time, image.start, image.end);
	if (opacity <= 0) {
		return null;
	}
	const scale = interpolate(opacity, [0, 1], [0.96, 1]);
	const position = POSITIONS[image.position];
	return (
		<div
			style={{
				position: "absolute",
				...position,
				transform: `${position.transform ?? ""} scale(${scale})`,
				opacity,
				padding: 14,
				borderRadius: 18,
				backgroundColor: "#FFFFFF",
				boxShadow: "0 18px 50px rgba(10, 20, 40, 0.35)",
				boxSizing: "border-box",
			}}
		>
			<Img src={staticFile(image.src)} style={{ display: "block", width: "100%", borderRadius: 8 }} />
			{image.caption ? (
				<div style={{ marginTop: 10, color: EXCEL_GREEN, fontFamily: "'Segoe UI', sans-serif", fontSize: 26, fontWeight: 700 }}>{image.caption}</div>
			) : null}
		</div>
	);
};
