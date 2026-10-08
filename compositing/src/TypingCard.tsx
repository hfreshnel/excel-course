import type { FormulaToken, TypingCard as TypingCardData } from "./lesson-data";

// Excel colours each referenced range differently while a formula is edited; the card mimics that palette
const NAME_COLORS = ["#1F5FBF", "#C0392B", "#7D3C98", "#1E8449", "#B9770E", "#117A8B"];
const NEUTRAL_COLOR = "#2B2F36";
const TOKEN_ENTER_SECONDS = 0.18;
const CARET_BLINK_SECONDS = 0.5;
const COMMIT_FLASH_SECONDS = 0.6;

const tokenColor = (token: FormulaToken, nameColors: Map<string, string>): string => {
	if (token.kind === "name") {
		return nameColors.get(token.text) ?? NEUTRAL_COLOR;
	}
	return token.kind === "number" || token.kind === "string" ? "#0E6655" : NEUTRAL_COLOR;
};

export const TypingCard: React.FC<{ card: TypingCardData; time: number; opacity: number }> = ({ card, time, opacity }) => {
	const nameColors = new Map<string, string>();
	for (const token of card.tokens) {
		if (token.kind === "name" && !nameColors.has(token.text)) {
			nameColors.set(token.text, NAME_COLORS[nameColors.size % NAME_COLORS.length]);
		}
	}
	const committed = time >= card.commit;
	const flash = committed ? Math.max(0, 1 - (time - card.commit) / COMMIT_FLASH_SECONDS) : 0;
	const caretVisible = !committed && Math.floor(time / CARET_BLINK_SECONDS) % 2 === 0;
	const scale = 0.96 + 0.04 * opacity;
	return (
		<div
			style={{
				position: "absolute",
				left: "50%",
				top: "50%",
				transform: `translate(-50%, -50%) scale(${scale})`,
				opacity,
				minWidth: 760,
				padding: "34px 52px 40px",
				borderRadius: 22,
				backgroundColor: "rgba(255, 255, 255, 0.97)",
				boxShadow: `0 24px 70px rgba(10, 20, 40, 0.35), 0 0 0 ${2 + 4 * flash}px rgba(33, 115, 70, ${0.25 + 0.75 * flash})`,
				fontFamily: "'Segoe UI', sans-serif",
			}}
		>
			<div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 22, color: "#5F6670", fontSize: 30, fontWeight: 600 }}>
				<span style={{ padding: "4px 14px", borderRadius: 8, backgroundColor: "#217346", color: "white", fontSize: 26, fontWeight: 700 }}>{card.label}</span>
				<span>{committed ? "Validé avec Entrée" : "Saisie"}</span>
			</div>
			<div style={{ fontFamily: "Consolas, 'Cascadia Mono', monospace", fontSize: 64, fontWeight: 600, whiteSpace: "pre", display: "flex", alignItems: "center" }}>
				{card.tokens.map((token, index) => {
					const progress = Math.max(0, Math.min(1, (time - token.time) / TOKEN_ENTER_SECONDS));
					if (progress <= 0) {
						return null;
					}
					return (
						<span key={index} style={{ color: tokenColor(token, nameColors), opacity: progress, transform: `translateY(${(1 - progress) * 10}px)`, display: "inline-block" }}>
							{token.text}
						</span>
					);
				})}
				<span style={{ display: "inline-block", width: 5, height: 70, marginLeft: 6, backgroundColor: "#217346", opacity: caretVisible ? 1 : 0 }} />
			</div>
		</div>
	);
};
