export const FONT_MIN = 16;
export const FONT_MAX = 40;
export const FONT_DEFAULT = 18;
export const FONT_STEP = 2;
export const FONT_STORAGE_KEY = 'verso.readingFontSize';

export function clampFontSize(value: number): number {
	return Math.min(FONT_MAX, Math.max(FONT_MIN, Math.round(value)));
}

export function pinchFontSize(initialSize: number, initialDistance: number, currentDistance: number): number {
	if (initialDistance <= 0) return clampFontSize(initialSize);
	return clampFontSize((initialSize * currentDistance) / initialDistance);
}

export function parseStoredFontSize(raw: string | null): number {
	const value = Number(raw);
	if (raw === null || !Number.isInteger(value) || value < FONT_MIN || value > FONT_MAX) return FONT_DEFAULT;
	return value;
}
