import { AbsoluteFill } from "remotion";
import { ProfessorEx } from "./ProfessorEx";
import type { AvatarData } from "./lesson-data";

const POSE_SECONDS = 2.5;
const PREVIEW_POSES = ["neutral", "welcome", "explain", "point", "warning", "cheer"];

export type AvatarPreviewData = {
	avatar: AvatarData;
};

// Static files come from assets/avatar/normalized (npm run studio:avatar)
export const defaultAvatarPreviewData: AvatarPreviewData = {
	avatar: {
		poses: Object.fromEntries(PREVIEW_POSES.map((pose) => [pose, `${pose}.png`])),
		imageWidth: 1024,
		imageHeight: 1536,
		height: 420,
		left: 24,
		defaultPose: "neutral",
		cues: PREVIEW_POSES.map((pose, index) => ({ pose, start: 1 + index * POSE_SECONDS })),
	},
};

export const AVATAR_PREVIEW_FRAMES = Math.ceil((2 + PREVIEW_POSES.length * POSE_SECONDS) * 30);

// The light area mimics the Excel grid behind the avatar
export const AvatarPreview: React.FC<AvatarPreviewData> = ({ avatar }) => (
	<AbsoluteFill style={{ backgroundColor: "#1B1E24" }}>
		<div style={{ position: "absolute", left: 0, top: 30, width: 1920, height: 1020, backgroundColor: "#F7F7F7" }} />
		<ProfessorEx avatar={avatar} />
	</AbsoluteFill>
);
