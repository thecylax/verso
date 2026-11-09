<script lang="ts">
	import { onMount } from 'svelte';
	import type { Passage } from '$lib/api';
	import { formatElapsed } from '$lib/timer';
	import { splitTopics } from '$lib/topics';
	import ReadingPane from './ReadingPane.svelte';

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

	const topicCount = $derived(splitTopics(markdown).length);

	let accumulated = $state(0);
	let resumedAt = $state<number | null>(performance.now());
	let now = $state(performance.now());
	const elapsed = $derived(accumulated + (resumedAt === null ? 0 : now - resumedAt));
	const paused = $derived(resumedAt === null);

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
			class="glass z-50 rounded-full px-4 py-2 font-mono text-lg tabular-nums text-slate-50"
			type="button"
			onclick={toggleTimer}
			aria-label={paused ? `Cronômetro pausado em ${formatElapsed(elapsed)}. Retomar` : `Cronômetro ${formatElapsed(elapsed)}. Pausar`}
		>
			<span aria-hidden="true">{paused ? '⏸ ' : ''}{formatElapsed(elapsed)}</span>
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
					<span aria-hidden="true">↑</span>
				</button>
				<button
					class="glass h-16 w-16 rounded-full text-3xl text-slate-50 disabled:opacity-40"
					type="button"
					onclick={() => goTo(active + 1)}
					disabled={active >= topicCount - 1}
					aria-label="Próximo tópico"
				>
					<span aria-hidden="true">↓</span>
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
</style>
