const FENCE_OPEN = /^ {0,3}(`{3,}|~{3,})/;
const FENCE_CLOSE = /^ {0,3}(`{3,}|~{3,})[ \t]*$/;

/** Para cada linha, true se pertence a uma cerca ``` ou ~~~ (inclusive as linhas da cerca). */
export function fencedLineFlags(lines: string[]): boolean[] {
	const flags: boolean[] = [];
	let fence: string | null = null;
	for (const line of lines) {
		if (fence === null) {
			const opened = FENCE_OPEN.exec(line);
			if (opened) fence = opened[1];
			flags.push(Boolean(opened));
			continue;
		}
		flags.push(true);
		const closed = FENCE_CLOSE.exec(line);
		if (closed && closed[1][0] === fence[0] && closed[1].length >= fence.length) fence = null;
	}
	return flags;
}

export function maskFences(text: string): string {
	const lines = text.split('\n');
	const flags = fencedLineFlags(lines);
	return lines.map((line, i) => (flags[i] ? ' '.repeat(line.length) : line)).join('\n');
}
