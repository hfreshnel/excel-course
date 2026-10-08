import { Composition } from "remotion";
import { ExcelLesson } from "./ExcelLesson";
import { defaultLessonData, type LessonData } from "./lesson-data";

export const RemotionRoot: React.FC = () => (
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
);
