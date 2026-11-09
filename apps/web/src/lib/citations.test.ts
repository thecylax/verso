import { describe, expect, it } from 'vitest';
import type { Passage } from './api';
import { findPassage, parseCitations, referenceLabel } from './citations';

const ref = (c: { version: string | null; abbrev: string; chapter: number; start: number | null; end: number | null }) => ({
	version: c.version,
	abbrev: c.abbrev,
	chapter: c.chapter,
	start: c.start,
	end: c.end
});

describe('parseCitations — entradas que produzem uma citação', () => {
	const cases: [string, ReturnType<typeof ref>][] = [
		['João 3:16', { version: null, abbrev: 'jo', chapter: 3, start: 16, end: 16 }],
		['Jo 3.16', { version: null, abbrev: 'jo', chapter: 3, start: 16, end: 16 }],
		['João 3:16-18', { version: null, abbrev: 'jo', chapter: 3, start: 16, end: 18 }],
		['1 Coríntios 13:4-7', { version: null, abbrev: '1co', chapter: 13, start: 4, end: 7 }],
		['1 Co 13:4', { version: null, abbrev: '1co', chapter: 13, start: 4, end: 4 }],
		['1Co 13:4', { version: null, abbrev: '1co', chapter: 13, start: 4, end: 4 }],
		['Sl 23', { version: null, abbrev: 'sl', chapter: 23, start: null, end: null }],
		['Salmos 23:1', { version: null, abbrev: 'sl', chapter: 23, start: 1, end: 1 }],
		['Gn 1:1-3', { version: null, abbrev: 'gn', chapter: 1, start: 1, end: 3 }],
		['Jó 1:21', { version: null, abbrev: 'job', chapter: 1, start: 21, end: 21 }],
		['Job 1:21', { version: null, abbrev: 'job', chapter: 1, start: 21, end: 21 }],
		['leia João 3:16 hoje', { version: null, abbrev: 'jo', chapter: 3, start: 16, end: 16 }],
		['[[acf:sl:23:1-6]]', { version: 'acf', abbrev: 'sl', chapter: 23, start: 1, end: 6 }],
		['[[nvi:sl:23]]', { version: 'nvi', abbrev: 'sl', chapter: 23, start: null, end: null }],
		['I João 1:9', { version: null, abbrev: '1jo', chapter: 1, start: 9, end: 9 }],
		['2ª Timóteo 3:16', { version: null, abbrev: '2tm', chapter: 3, start: 16, end: 16 }],
		['Sl. 23:1', { version: null, abbrev: 'sl', chapter: 23, start: 1, end: 1 }],
		['(Gn 1)', { version: null, abbrev: 'gn', chapter: 1, start: null, end: null }],
		['João 3:16 e João 3:16', { version: null, abbrev: 'jo', chapter: 3, start: 16, end: 16 }]
	];

	it.each(cases)('%s', (text, expected) => {
		const result = parseCitations(text);
		expect(result).toHaveLength(1);
		expect(ref(result[0])).toEqual(expected);
	});
});

describe('parseCitations — entradas que não produzem citação', () => {
	it.each([
		['João 3 vezes'],
		['`João 3:16`'],
		['```\nJoão 3:16\n```'],
		['~~~\nJoão 3:16\n~~~'],
		['Coríntios 13:4'],
		['João 99:1'],
		['<!-- João 3:16 -->']
	])('%s', (text) => {
		expect(parseCitations(text)).toEqual([]);
	});

	it('Jo 3:16 é João, não Jó', () => {
		const result = parseCitations('Jo 3:16');
		expect(result.map((c) => c.abbrev)).toEqual(['jo']);
	});
});

describe('parseCitations — regras complementares', () => {
	it('troca end < start', () => {
		expect(ref(parseCitations('Gn 1:3-1')[0])).toMatchObject({ start: 1, end: 3 });
	});

	it('descarta versículo 0', () => {
		expect(parseCitations('João 3:0')).toEqual([]);
	});

	it('mantém a ordem do texto e não conta a forma explícita duas vezes', () => {
		const result = parseCitations('Sl 23, depois [[acf:jo:3:16]] e Gn 1:1');
		expect(result.map((c) => `${c.version ?? ''}${c.abbrev}`)).toEqual(['sl', 'acfjo', 'gn']);
	});

	it('capítulo inteiro no fim da linha, com mais texto abaixo', () => {
		expect(parseCitations('Leitura: Salmos 23\nTexto')).toHaveLength(1);
	});
});

describe('findPassage e referenceLabel', () => {
	const passage: Passage = {
		version: 'acf',
		abbrev: 'sl',
		chapter: 23,
		start: 1,
		end: 6,
		book_name: 'Salmos',
		verses: [{ number: 1, text: 'v1' }],
		error: null
	};

	it('citação natural casa com qualquer versão', () => {
		const [citation] = parseCitations('Sl 23:1-6');
		expect(findPassage(citation, [passage])).toBe(passage);
	});

	it('citação explícita exige a mesma versão', () => {
		const [citation] = parseCitations('[[nvi:sl:23:1-6]]');
		expect(findPassage(citation, [passage])).toBeUndefined();
	});

	it('rótulos', () => {
		expect(referenceLabel(passage, passage.book_name, 'nvi')).toBe('ACF Salmos 23:1-6');
		expect(referenceLabel({ ...passage, version: 'nvi' }, 'Salmos', 'nvi')).toBe('Salmos 23:1-6');
		expect(referenceLabel({ ...passage, start: 3, end: 3, version: null }, undefined, 'nvi')).toBe('Salmos 23:3');
		expect(referenceLabel({ ...passage, start: null, end: null, version: null }, undefined, 'nvi')).toBe('Salmos 23');
	});
});
