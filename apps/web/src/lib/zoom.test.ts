import { describe, expect, it } from 'vitest';
import { FONT_DEFAULT, clampFontSize, parseStoredFontSize, pinchFontSize } from './zoom';

describe('zoom', () => {
	it('limita entre 16 e 40', () => {
		expect(clampFontSize(15)).toBe(16);
		expect(clampFontSize(41)).toBe(40);
		expect(clampFontSize(22)).toBe(22);
	});

	it('valor guardado inválido volta ao padrão', () => {
		expect(parseStoredFontSize(null)).toBe(FONT_DEFAULT);
		expect(parseStoredFontSize('15')).toBe(FONT_DEFAULT);
		expect(parseStoredFontSize('41')).toBe(FONT_DEFAULT);
		expect(parseStoredFontSize('abc')).toBe(FONT_DEFAULT);
		expect(parseStoredFontSize('24')).toBe(24);
	});

	it('pinça escala pela razão das distâncias, com limites', () => {
		expect(pinchFontSize(18, 100, 200)).toBe(36);
		expect(pinchFontSize(18, 100, 50)).toBe(16);
		expect(pinchFontSize(30, 100, 200)).toBe(40);
		expect(pinchFontSize(20, 100, 110)).toBe(22);
	});
});
