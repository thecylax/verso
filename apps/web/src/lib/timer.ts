export function formatElapsed(ms: number): string {
	const total = Math.max(0, Math.floor(ms / 1000));
	const hours = Math.floor(total / 3600);
	const minutes = Math.floor((total % 3600) / 60);
	const seconds = total % 60;
	const pad = (n: number) => String(n).padStart(2, '0');
	return hours > 0 ? `${hours}:${pad(minutes)}:${pad(seconds)}` : `${pad(minutes)}:${pad(seconds)}`;
}

/** `mm:ss` ou `h:mm:ss`. Abaixo de zero, o sinal aparece no segundo cheio (`-00:01`). */
export function formatClock(ms: number): string {
	const seconds = Math.trunc(ms / 1000);
	const sign = seconds < 0 ? '-' : '';
	return sign + formatElapsed(Math.abs(seconds) * 1000);
}
