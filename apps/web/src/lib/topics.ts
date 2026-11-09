import { fencedLineFlags } from './markdown';

export type Topic = {
	index: number;
	title: string;
	markdown: string;
	level: number; // 0 no preâmbulo; 1 a 6 nos headings
};

const HEADING = /^ {0,3}(#{1,6}) (.*)$/;
const CLOSING_HASHES = /\s+#+\s*$/;

export function splitTopics(markdown: string): Topic[] {
	const lines = markdown.split('\n');
	const flags = fencedLineFlags(lines);
	const topics: { title: string; level: number; lines: string[] }[] = [
		{ title: 'Início', level: 0, lines: [] }
	];

	lines.forEach((line, i) => {
		const heading = flags[i] ? null : HEADING.exec(line.replace(/\r$/, ''));
		if (heading) {
			const title = heading[2].replace(CLOSING_HASHES, '').trim();
			topics.push({ title, level: heading[1].length, lines: [line] });
		} else {
			topics[topics.length - 1].lines.push(line);
		}
	});

	return topics.map((topic, index) => ({
		index,
		title: topic.title,
		level: topic.level,
		markdown: topic.lines.join('\n')
	}));
}
