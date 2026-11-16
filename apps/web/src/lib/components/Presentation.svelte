<script lang="ts">
	import { onMount } from 'svelte';
	import type { Passage } from '$lib/api';
	import { clockState, parseTempo, stripTempo } from '$lib/tempo';
	import { formatClock } from '$lib/timer';
	import { splitTopics } from '$lib/topics';
	import Icon from './Icon.svelte';
	import ReadingPane from './ReadingPane.svelte';
	import { faChevronDown, faChevronUp, faPause } from '@fortawesome/free-solid-svg-icons';

	let {
		markdown,
		passages,
		accountVersion,
		onclose
	}: { markdown: string; passages: Passage[]; accountVersion: string; onclose: () => void } = $props();

	let root: HTMLDivElement;
	let scroller = $state<HTMLElement | null>(null);
	let simulated = $state(false);
	let active = $state(0);

	const topicCount = $derived(splitTopics(stripTempo(markdown)).length);
	const tempo = $derived(parseTempo(markdown));

	let accumulated = $state(0);
	let resumedAt = $state<number | null>(performance.now());
	let now = $state(performance.now());
	const elapsed = $derived(accumulated + (resumedAt === null ? 0 : now - resumedAt));
	const paused = $derived(resumedAt === null);
	const clock = $derived(clockState(elapsed, tempo));

	function clockName(displayMs: number, isPaused: boolean, alerting: boolean): string {
		const shown = formatClock(displayMs);
		const spoken = shown.startsWith('-') ? `menos ${shown.slice(1)}` : shown;
		const alert = alerting ? ', em alerta' : '';
		return isPaused ? `Cronômetro pausado em ${spoken}${alert}. Retomar` : `Cronômetro ${spoken}${alert}. Pausar`;
	}

	function toggleTimer() {
		const t = performance.now();
		if (resumedAt === null) {
			resumedAt = t;
		} else {
			accumulated += t - resumedAt;
			resumedAt = null;
		}
		now = t;
	}

	function goTo(index: number) {
		if (index < 0 || index >= topicCount) return;
		active = index;
		scroller?.querySelector(`#topico-${index}`)?.scrollIntoView({ block: 'start' });
	}

	let closing = false;
	function close() {
		if (closing) return;
		closing = true;
		if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
		onclose();
	}

	onMount(() => {
		const tick = setInterval(() => (now = performance.now()), 250);
		let wasFullscreen = false;

		const onFullscreenChange = () => {
			if (document.fullscreenElement === root) wasFullscreen = true;
			else if (wasFullscreen) close();
		};
		const onKeydown = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				event.preventDefault();
				close();
			}
		};
		document.addEventListener('fullscreenchange', onFullscreenChange);
		document.addEventListener('keydown', onKeydown);

		if (typeof root.requestFullscreen === 'function') {
			root.requestFullscreen().catch(() => (simulated = true));
		} else {
			simulated = true;
		}

		return () => {
			clearInterval(tick);
			document.removeEventListener('fullscreenchange', onFullscreenChange);
			document.removeEventListener('keydown', onKeydown);
			if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
		};
	});
</script>

<div
	bind:this={root}
	class="presentation flex flex-col bg-[#0b1220]"
	class:simulated
	role="dialog"
	aria-modal="true"
	aria-label="Apresentação"
>
	<div class="flex shrink-0 items-center justify-between gap-3 px-4 py-3">
		<button
			class="glass z-50 rounded-full px-4 py-2 font-mono text-lg tabular-nums {clock.alerting ? 'text-red-400' : 'text-slate-50'}"
			type="button"
			onclick={toggleTimer}
			aria-label={clockName(clock.displayMs, paused, clock.alerting)}
		>
			<span aria-hidden="true">
				{#if paused}<Icon class="mr-1" icon={faPause} />{/if}
				<span class="digits" class:pulsing={clock.alerting && !paused}>{formatClock(clock.displayMs)}</span>
			</span>
		</button>
		<button class="glass z-50 rounded-full px-4 py-2 font-medium text-slate-50" type="button" onclick={close}>
			Fechar
		</button>
	</div>

	<ReadingPane {markdown} {passages} {accountVersion} bind:active bind:scroller>
		{#snippet overlay()}
			<div
				class="fixed right-4 z-50 flex items-center gap-3"
				style="bottom: calc(var(--drawer-offset, 0px) + 72px); right: max(1rem, env(safe-area-inset-right))"
			>
				<button
					class="glass h-12 w-12 rounded-full text-xl text-slate-50 disabled:opacity-40"
					type="button"
					onclick={() => goTo(active - 1)}
					disabled={active <= 0}
					aria-label="Tópico anterior"
				>
					<Icon class="text-lg" icon={faChevronUp} />
				</button>
				<button
					class="glass h-16 w-16 rounded-full text-3xl text-slate-50 disabled:opacity-40"
					type="button"
					onclick={() => goTo(active + 1)}
					disabled={active >= topicCount - 1}
					aria-label="Próximo tópico"
				>
					<Icon class="text-2xl" icon={faChevronDown} />
				</button>
			</div>
		{/snippet}
	</ReadingPane>
</div>

<style>
	.presentation {
		position: fixed;
		inset: 0;
		z-index: 40;
		height: 100dvh;
	}
	.presentation.simulated {
		padding: env(safe-area-inset-top) env(safe-area-inset-right) 0 env(safe-area-inset-left);
	}
	.presentation :global(.reading) {
		color: #f8fafc;
	}

	.digits.pulsing {
		animation: clock-pulse 1.8s ease-in-out infinite;
	}

	@keyframes clock-pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.45;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.digits.pulsing {
			animation: none;
		}
	}
</style>
