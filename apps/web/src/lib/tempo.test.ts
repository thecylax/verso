import { describe, expect, it } from 'vitest';
import { parseCitations } from './citations';
import { clockState, parseTempo, stripTempo } from './tempo';
import { formatClock } from './timer';

const MIN = 60_000;

describe('parseTempo', () => {
	it('lê alvo e alerta', () => {
		expect(parseTempo('[[tempo 15m alerta 2m]]\n# A')).toEqual({ targetMs: 15 * MIN, alertMs: 2 * MIN });
	});

	it('aceita horas, segundos, min e espaços', () => {
		expect(parseTempo('[[ tempo  1h 30m ]]')).toEqual({ targetMs: 90 * MIN, alertMs: null });
		expect(parseTempo('[[Tempo 90s Alerta 0s]]')).toEqual({ targetMs: 90_000, alertMs: 0 });
		expect(parseTempo('[[tempo 15min alerta 30s]]')).toEqual({ targetMs: 15 * MIN, alertMs: 30_000 });
	});

	it('usa a primeira diretiva válida e ignora cerca', () => {
		const markdown = '```\n[[tempo 15m alerta 2m]]\n```\n[[tempo 10m alerta 1m]]\n[[tempo 20m]]';
		expect(parseTempo(markdown)).toEqual({ targetMs: 10 * MIN, alertMs: MIN });
	});

	it('rejeita duração ausente, zero no alvo e linha inválida', () => {
		expect(parseTempo('[[tempo]]')).toBeNull();
		expect(parseTempo('[[tempo 0m alerta 1m]]')).toBeNull();
		expect(parseTempo('[[tempo 15]]')).toBeNull();
		expect(parseTempo('[[tempo 15m alerta]]')).toBeNull();
		expect(parseTempo('[[tempo 15m alerta 2m extra]]')).toBeNull();
	});
});

describe('stripTempo', () => {
	it('tira a diretiva da leitura e preserva o resto', () => {
		const markdown = '[[tempo 15m alerta 2m]]\n\n# A graça\nJoão 3:16';
		expect(stripTempo(markdown)).toBe('\n# A graça\nJoão 3:16');
		expect(parseCitations(markdown).map((c) => c.abbrev)).toEqual(['jo']);
		expect(parseCitations('[[tempo 15m alerta 2m]]')).toEqual([]);
	});

	it('não mexe em diretiva dentro de cerca nem em linha inválida', () => {
		expect(stripTempo('```\n[[tempo 15m]]\n```\n[[tempo 15]]')).toBe('```\n[[tempo 15m]]\n```\n[[tempo 15]]');
	});
});

describe('clockState', () => {
	const tempo = { targetMs: 15 * MIN, alertMs: 2 * MIN };

	it('sem diretiva conta para a frente', () => {
		expect(clockState(5000, null)).toEqual({ displayMs: 5000, alerting: false });
	});

	it('conta para trás e alerta no restante', () => {
		expect(clockState(0, tempo)).toEqual({ displayMs: 15 * MIN, alerting: false });
		expect(clockState(13 * MIN, tempo)).toEqual({ displayMs: 2 * MIN, alerting: true });
		expect(clockState(15 * MIN + 1000, tempo).displayMs).toBe(-1000);
		expect(clockState(15 * MIN + 1000, tempo).alerting).toBe(true);
	});

	it('sem alerta não muda a cor, mesmo depois do zero', () => {
		expect(clockState(20 * MIN, { targetMs: 15 * MIN, alertMs: null })).toEqual({
			displayMs: -5 * MIN,
			alerting: false
		});
	});
});

describe('formatClock', () => {
	it('mostra o sinal negativo no segundo cheio', () => {
		expect(formatClock(0)).toBe('00:00');
		expect(formatClock(90_000)).toBe('01:30');
		expect(formatClock(-999)).toBe('00:00');
		expect(formatClock(-1000)).toBe('-00:01');
		expect(formatClock(-3_661_000)).toBe('-1:01:01');
	});
});
