// @remotion/media replaces OffthreadVideo, whose frame cache overflowed on long full-HD captures ("No frame found at position")
import { Audio, Video } from "@remotion/media";
import { AbsoluteFill, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FocusBlur } from "./FocusBlur";
import { HighlightBox } from "./HighlightBox";
import { TypingCard } from "./TypingCard";
import { fadeOpacity, type LessonData } from "./lesson-data";

const BACKGROUND = "#1B1E24";

export const ExcelLesson: React.FC<LessonData> = ({ capture, audio, highlights, typingCards }) => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();
	const time = frame / fps;
	const activeCard = typingCards.find((card) => fadeOpacity(time, card.start, card.end) > 0);
	const cardOpacity = activeCard ? fadeOpacity(time, activeCard.start, activeCard.end) : 0;
	return (
		<AbsoluteFill style={{ backgroundColor: BACKGROUND }}>
			<Sequence from={Math.round(audio.delay * fps)}>
				<Audio src={staticFile(audio.src)} />
			</Sequence>
			<div style={{ position: "absolute", left: 0, top: capture.offsetY, width: capture.width, height: capture.height, overflow: "hidden" }}>
				<Video src={staticFile(capture.src)} muted style={{ width: capture.width, height: capture.height }} />
				{highlights.map((highlight, index) => {
					const opacity = fadeOpacity(time, highlight.start, highlight.end);
					return opacity > 0 ? highlight.rects.map((rect, rectIndex) => <HighlightBox key={`${index}-${rectIndex}`} rect={rect} opacity={opacity} />) : null;
				})}
				{activeCard ? (
					<>
						<FocusBlur rect={activeCard.targetRect} width={capture.width} height={capture.height} opacity={cardOpacity} />
						<HighlightBox rect={activeCard.targetRect} opacity={cardOpacity} strong />
					</>
				) : null}
			</div>
			{activeCard ? <TypingCard card={activeCard} time={time} opacity={cardOpacity} /> : null}
		</AbsoluteFill>
	);
};
