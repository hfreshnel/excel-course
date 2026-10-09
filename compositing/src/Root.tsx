import { Composition } from "remotion";
import { AVATAR_PREVIEW_FRAMES, AvatarPreview, defaultAvatarPreviewData } from "./AvatarPreview";
import { ExcelLesson } from "./ExcelLesson";
import { defaultLessonData, type LessonData } from "./lesson-data";

export const RemotionRoot: React.FC = () => (
	<>
		<Composition
			id="ExcelLesson"
			component={ExcelLesson}
			defaultProps={defaultLessonData}
			width={defaultLessonData.width}
			height={defaultLessonData.height}
			fps={defaultLessonData.fps}
			durationInFrames={defaultLessonData.durationInFrames}
			calculateMetadata={({ props }: { props: LessonData }) => ({
				durationInFrames: props.durationInFrames,
				fps: props.fps,
				width: props.width,
				height: props.height,
			})}
		/>
		<Composition
			id="AvatarPreview"
			component={AvatarPreview}
			defaultProps={defaultAvatarPreviewData}
			width={1920}
			height={1080}
			fps={30}
			durationInFrames={AVATAR_PREVIEW_FRAMES}
		/>
	</>
);
