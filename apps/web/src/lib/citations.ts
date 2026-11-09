import type { Passage } from './api';
import { BOOKS, BOOKS_BY_ABBREV } from './books';
import { maskFences } from './markdown';

export type ParsedCitation = {
	version: string | null;
	abbrev: string;
	chapter: number;
	start: number | null;
	end: number | null;
	index: number;
};

const ALIAS_TO_ABBREV = new Map<string, string>(
	BOOKS.flatMap((book) => book.aliases.map((alias) => [alias, book.abbrev] as [string, string]))
);

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const aliasAlternation = [...ALIAS_TO_ABBREV.keys()]
	.sort((a, b) => b.length - a.length)
	.map(escapeRegExp)
	.join('|');

const EXPLICIT =
	/\[\[([a-z0-9]{2,20}):([a-z0-9]{1,8}):(\d{1,3})(?::(\d{1,3})(?:-(\d{1,3}))?)?\]\]/g;
const NATURAL = new RegExp(
	`(?<![\\p{L}\\p{N}])(${aliasAlternation})\\.?(?![\\p{L}\\p{N}])\\s*(\\d{1,3})(?:\\s*[:.]\\s*(\\d{1,3})(?:\\s*[-–—]\\s*(\\d{1,3}))?)?`,
	'gu'
);
const CHAPTER_ONLY_END = /[^\S\n]*(?:\n|$|[,.;!?)\]}”"'])/y;
const INLINE_CODE = /`[^`\n]*`/g;
const HTML_COMMENT = /<!--[\s\S]*?-->/g;

const blank = (match: string) => match.replace(/[^\n]/g, ' ');

export function maskCode(markdown: string): string {
	return maskFences(markdown).replace(INLINE_CODE, blank).replace(HTML_COMMENT, blank);
}

function build(
	version: string | null,
	abbrev: string,
	chapter: number,
	start: number | null,
	end: number | null,
	index: number
): ParsedCitation | null {
	const book = BOOKS_BY_ABBREV[abbrev];
	if (!book || chapter < 1 || chapter > book.chapters) return null;
	if (start !== null) {
		if (end === null) end = start;
		if (start < 1 || end < 1) return null;
		if (end < start) [start, end] = [end, start];
	} else {
		end = null;
	}
	return { version, abbrev, chapter, start, end, index };
}

const num = (value: string | undefined) => (value === undefined ? null : Number(value));

export function parseCitations(markdown: string): ParsedCitation[] {
	let text = maskCode(markdown).toLocaleLowerCase('pt-BR');
	const found: ParsedCitation[] = [];

	text = text.replace(EXPLICIT, (match, version, abbrev, chapter, start, end, offset: number) => {
		const citation = build(version, abbrev, Number(chapter), num(start), num(end), offset);
		if (citation) found.push(citation);
		return ' '.repeat(match.length);
	});

	for (const match of text.matchAll(NATURAL)) {
		const [whole, alias, chapter, verse, end] = match;
		if (verse === undefined) {
			CHAPTER_ONLY_END.lastIndex = match.index + whole.length;
			if (!CHAPTER_ONLY_END.test(text)) continue;
		}
		const citation = build(
			null,
			ALIAS_TO_ABBREV.get(alias)!,
			Number(chapter),
			num(verse),
			num(end),
			match.index
		);
		if (citation) found.push(citation);
	}

	found.sort((a, b) => a.index - b.index);
	const seen = new Set<string>();
	return found.filter((c) => {
		const key = `${c.version ?? ''}|${c.abbrev}|${c.chapter}|${c.start}|${c.end}`;
		if (seen.has(key)) return false;
		seen.add(key);
		return true;
	});
}

export function findPassage(citation: ParsedCitation, passages: Passage[]): Passage | undefined {
	return passages.find(
		(p) =>
			p.abbrev === citation.abbrev &&
			p.chapter === citation.chapter &&
			p.start === citation.start &&
			p.end === citation.end &&
			(citation.version === null || p.version === citation.version)
	);
}

export function referenceLabel(
	ref: { abbrev: string; chapter: number; start: number | null; end: number | null; version: string | null },
	bookName: string | undefined,
	accountVersion: string
): string {
	const name = bookName || BOOKS_BY_ABBREV[ref.abbrev]?.name || ref.abbrev;
	let label = `${name} ${ref.chapter}`;
	if (ref.start !== null) {
		label += ref.end !== null && ref.end !== ref.start ? `:${ref.start}-${ref.end}` : `:${ref.start}`;
	}
	if (ref.version && ref.version !== accountVersion) label = `${ref.version.toUpperCase()} ${label}`;
	return label;
}
