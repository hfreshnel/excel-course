import { Img, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { AvatarCue, AvatarData } from "./lesson-data";

const POP_FROM_SCALE = 0.93;
const BREATH_PERIOD_SECONDS = 3.6;
const BREATH_AMPLITUDE = 0.012;
const SWAY_PERIOD_SECONDS = 5.3;
const SWAY_DEGREES = 0.6;

const activeCueIndex = (cues: AvatarCue[], time: number): number => {
	let index = -1;
	for (let cursor = 0; cursor < cues.length && cues[cursor].start <= time; cursor++) {
		index = cursor;
	}
	return index;
};

const imageStyle: React.CSSProperties = { position: "absolute", inset: 0, width: "100%", height: "100%" };

export const ProfessorEx: React.FC<{ avatar: AvatarData }> = ({ avatar }) => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();
	const time = frame / fps;
	const index = activeCueIndex(avatar.cues, time);
	const pose = index >= 0 ? avatar.cues[index].pose : avatar.defaultPose;
	const src = staticFile(avatar.poses[pose] ?? avatar.poses[avatar.defaultPose]);
	const cueFrame = index >= 0 ? Math.round(avatar.cues[index].start * fps) : 0;
	// Poses are swapped with a hard cut plus a small bounce: a cross-fade ghosts the head when the body turns
	const pop = index >= 0 ? spring({ frame: frame - cueFrame, fps, config: { damping: 11, stiffness: 180, mass: 0.6 } }) : 1;
	const popScale = POP_FROM_SCALE + (1 - POP_FROM_SCALE) * pop;
	const enter = spring({ frame, fps, config: { damping: 15, stiffness: 120 } });
	const breath = 1 + BREATH_AMPLITUDE * Math.sin((2 * Math.PI * time) / BREATH_PERIOD_SECONDS);
	const sway = SWAY_DEGREES * Math.sin((2 * Math.PI * time) / SWAY_PERIOD_SECONDS);
	const width = (avatar.height * avatar.imageWidth) / avatar.imageHeight;
	return (
		<div
			style={{
				position: "absolute",
				left: avatar.left,
				bottom: 0,
				width,
				height: avatar.height,
				transformOrigin: "50% 100%",
				transform: `translateY(${(1 - enter) * avatar.height}px) rotate(${sway}deg) scale(${popScale}, ${popScale * breath})`,
			}}
		>
			<Img src={src} style={imageStyle} />
		</div>
	);
};
