export type PixelRect = {
	x: number;
	y: number;
	w: number;
	h: number;
};

export type Highlight = {
	start: number;
	end: number;
	rects: PixelRect[];
};

export type FormulaTokenKind = "string" | "number" | "name" | "operator" | "paren" | "separator";

export type FormulaToken = {
	text: string;
	kind: FormulaTokenKind;
	time: number;
	spoken: string;
};

export type TypingCard = {
	label: string;
	tokens: FormulaToken[];
	start: number;
	commit: number;
	end: number;
	targetRect: PixelRect;
};

// Times are in seconds of video time; rectangles are in capture pixels
export type LessonData = {
	fps: number;
	width: number;
	height: number;
	durationInFrames: number;
	capture: { src: string; width: number; height: number; offsetY: number };
	audio: { src: string; delay: number };
	highlights: Highlight[];
	typingCards: TypingCard[];
};

export const defaultLessonData: LessonData = {
	fps: 30,
	width: 1920,
	height: 1080,
	durationInFrames: 300,
	capture: { src: "capture.mp4", width: 1920, height: 1020, offsetY: 30 },
	audio: { src: "audio.wav", delay: 1 },
	highlights: [],
	typingCards: [],
};

export const FADE_SECONDS = 0.25;

export const fadeOpacity = (time: number, start: number, end: number): number => {
	if (time < start - FADE_SECONDS || time > end + FADE_SECONDS) {
		return 0;
	}
	const fadeIn = Math.min(1, (time - start + FADE_SECONDS) / FADE_SECONDS);
	const fadeOut = Math.min(1, (end + FADE_SECONDS - time) / FADE_SECONDS);
	return Math.max(0, Math.min(fadeIn, fadeOut));
};
