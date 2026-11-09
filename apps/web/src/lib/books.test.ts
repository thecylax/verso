import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { BOOKS } from './books';

const pythonCatalogPath = fileURLToPath(new URL('../../../api/app/books.py', import.meta.url));

function readPythonCatalog(): { abbrev: string; chapters: number; aliases: string[]; name: string }[] {
	const source = readFileSync(pythonCatalogPath, 'utf8').replace(/\r\n/g, '\n');
	const start = source.indexOf('BOOKS = ') + 'BOOKS = '.length;
	const end = source.indexOf('\n]\n', start) + 2;
	return JSON.parse(source.slice(start, end));
}

describe('catálogo de livros', () => {
	it('tem 66 livros com abreviações únicas', () => {
		expect(BOOKS).toHaveLength(66);
		expect(new Set(BOOKS.map((b) => b.abbrev)).size).toBe(66);
	});

	it('Tito tem 3 capítulos e Filemom 1', () => {
		expect(BOOKS.find((b) => b.abbrev === 'tt')?.chapters).toBe(3);
		expect(BOOKS.find((b) => b.abbrev === 'fm')?.chapters).toBe(1);
	});

	it('nenhum alias se repete entre livros', () => {
		const aliases = BOOKS.flatMap((b) => b.aliases);
		expect(new Set(aliases).size).toBe(aliases.length);
	});

	it('books.ts e books.py têm as mesmas abreviações e os mesmos capítulos', () => {
		const python = readPythonCatalog();
		expect(python.map((b) => b.abbrev)).toEqual(BOOKS.map((b) => b.abbrev));
		expect(python.map((b) => b.chapters)).toEqual(BOOKS.map((b) => b.chapters));
		expect(python).toEqual(BOOKS);
	});
});
