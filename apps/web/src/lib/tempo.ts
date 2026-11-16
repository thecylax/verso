import { fencedLineFlags } from './markdown';

export type Tempo = {
	targetMs: number;
	alertMs: number | null;
};

const TEMPO_LINE = /^ {0,3}\[\[\s*tempo\s+(.+?)\s*\]\]\s*$/i;
const DURATION = /^(?:(\d+)h)?(?:(\d+)min|(\d+)m)?(?:(\d+)s)?$/i;

/** `15m`, `90s`, `1h30m` ou `1h 30m`. Texto que não é duração devolve null. Zero é duração. */
export function parseDuration(raw: string): number | null {
	const text = raw.replace(/\s+/g, '');
	if (!text) return null;
	const match = DURATION.exec(text);
	if (!match) return null;
	const hours = Number(match[1] ?? 0);
	const minutes = Number(match[2] ?? match[3] ?? 0);
	const seconds = Number(match[4] ?? 0);
	return ((hours * 60 + minutes) * 60 + seconds) * 1000;
}

function tempoFromLine(line: string): Tempo | null {
	const match = TEMPO_LINE.exec(line.replace(/\r$/, ''));
	if (!match) return null;
	const parts = match[1].split(/\s+alerta\s+/i);
	if (parts.length > 2) return null;
	const targetMs = parseDuration(parts[0]);
	if (targetMs === null || targetMs <= 0) return null;
	if (parts.length === 1) return { targetMs, alertMs: null };
	const alertMs = parseDuration(parts[1]);
	if (alertMs === null) return null;
	return { targetMs, alertMs };
}

/** Primeira diretiva válida fora de cerca. As demais são ignoradas. */
export function parseTempo(markdown: string): Tempo | null {
	const lines = markdown.split('\n');
	const flags = fencedLineFlags(lines);
	for (let i = 0; i < lines.length; i++) {
		if (flags[i]) continue;
		const tempo = tempoFromLine(lines[i]);
		if (tempo) return tempo;
	}
	return null;
}

/** Remove as diretivas válidas, para que não apareçam na leitura. */
export function stripTempo(markdown: string): string {
	const lines = markdown.split('\n');
	const flags = fencedLineFlags(lines);
	return lines.filter((line, i) => flags[i] || tempoFromLine(line) === null).join('\n');
}

export function clockState(elapsedMs: number, tempo: Tempo | null): { displayMs: number; alerting: boolean } {
	if (!tempo) return { displayMs: elapsedMs, alerting: false };
	const displayMs = tempo.targetMs - elapsedMs;
	return {
		displayMs,
		alerting: tempo.alertMs !== null && displayMs <= tempo.alertMs
	};
}
