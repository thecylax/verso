import { describe, expect, it } from 'vitest';
import { parseCitations } from './citations';
import { splitTopics } from './topics';

const VECTOR = `intro

# A
texto a João 3:16

## B
texto b

# C`;

describe('splitTopics', () => {
	it('vetor da arquitetura: Início, A, B, C', () => {
		const topics = splitTopics(VECTOR);
		expect(topics.map((t) => t.title)).toEqual(['Início', 'A', 'B', 'C']);
		expect(topics.map((t) => t.level)).toEqual([0, 1, 2, 1]);
		expect(topics[0].markdown.trim()).toBe('intro');
		expect(topics.map((t) => t.index)).toEqual([0, 1, 2, 3]);
	});

	it('o tópico A contém a citação jo 3:16 e o seguinte é B', () => {
		const topics = splitTopics(VECTOR);
		const a = topics.findIndex((t) => t.title === 'A');
		expect(parseCitations(topics[a].markdown).map((c) => [c.abbrev, c.chapter, c.start])).toEqual([['jo', 3, 16]]);
		expect(topics[a + 1].title).toBe('B');
		expect(parseCitations(topics[a + 1].markdown)).toEqual([]);
	});

	it('# dentro de cerca não cria tópico', () => {
		const topics = splitTopics('# A\n```\n# não\n```\n~~~\n## também não\n~~~\n# B');
		expect(topics.map((t) => t.title)).toEqual(['Início', 'A', 'B']);
	});

	it('documento sem heading tem um único tópico Início com o texto todo', () => {
		const topics = splitTopics('só texto\nmais texto');
		expect(topics).toHaveLength(1);
		expect(topics[0]).toMatchObject({ title: 'Início', level: 0, markdown: 'só texto\nmais texto' });
	});

	it('Início existe vazio quando o documento começa com heading', () => {
		const topics = splitTopics('# A\ntexto');
		expect(topics[0]).toMatchObject({ title: 'Início', markdown: '' });
		expect(topics[1].markdown).toBe('# A\ntexto');
	});

	it('heading de nível menor também encerra o tópico, e corta # de fechamento', () => {
		const topics = splitTopics('## X ##\na\n# Y\nb');
		expect(topics.map((t) => t.title)).toEqual(['Início', 'X', 'Y']);
	});

	it('aceita até 3 espaços antes do heading e exige espaço depois dos #', () => {
		const topics = splitTopics('   # A\n#hashtag\n    # código');
		expect(topics.map((t) => t.title)).toEqual(['Início', 'A']);
	});
});
