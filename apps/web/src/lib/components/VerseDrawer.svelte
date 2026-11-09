<script lang="ts">
	import { onMount } from 'svelte';
	import type { Passage } from '$lib/api';
	import { findPassage, parseCitations, referenceLabel } from '$lib/citations';

	let {
		topicMarkdown,
		passages,
		accountVersion,
		offset = $bindable(0)
	}: { topicMarkdown: string; passages: Passage[]; accountVersion: string; offset?: number } = $props();

	const MISSING_TEXT: Record<string, string> = {
		not_found: 'Passagem não encontrada nesta versão.',
		invalid_reference: 'Referência inválida.',
		too_many: 'Limite de 40 passagens por nota atingido.'
	};
	const PENDING_TEXT = 'Não foi possível buscar o texto. Tentaremos de novo quando a nota for aberta.';
	const NOT_SAVED_TEXT = 'O texto será buscado quando a nota for salva.';

	function missingText(passage: Passage | undefined): string {
		if (!passage) return NOT_SAVED_TEXT;
		return (passage.error && MISSING_TEXT[passage.error]) || PENDING_TEXT;
	}

	const items = $derived(
		parseCitations(topicMarkdown).map((citation) => {
			const passage = findPassage(citation, passages);
			return {
				key: `${citation.version ?? ''}|${citation.abbrev}|${citation.chapter}|${citation.start}|${citation.end}`,
				label: passage
					? referenceLabel(passage, passage.book_name, accountVersion)
					: referenceLabel(citation, undefined, accountVersion),
				verses: passage && !passage.error ? passage.verses : [],
				missing: missingText(passage)
			};
		})
	);

	const handleText = $derived(
		items.length === 0
			? 'Nenhum versículo neste tópico'
			: items.length === 1
				? '1 versículo'
				: `${items.length} versículos`
	);

	let open = $state(false);
	let dragHeight = $state<number | null>(null);
	let openHeight = $state(420);
	const bodyHeight = $derived(dragHeight ?? (open ? openHeight : 0));

	let drag: { pointerId: number; startY: number; startHeight: number; moved: boolean } | null = null;

	onMount(() => {
		const measure = () => (openHeight = Math.min(window.innerHeight * 0.5, 420));
		measure();
		window.addEventListener('resize', measure);
		return () => window.removeEventListener('resize', measure);
	});

	function onPointerDown(event: PointerEvent) {
		if (event.button !== 0) return;
		suppressClick = false;
		(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
		drag = { pointerId: event.pointerId, startY: event.clientY, startHeight: bodyHeight, moved: false };
	}

	function onPointerMove(event: PointerEvent) {
		if (!drag || drag.pointerId !== event.pointerId) return;
		const delta = drag.startY - event.clientY;
		if (Math.abs(delta) > 4) drag.moved = true;
		if (drag.moved) dragHeight = Math.min(openHeight, Math.max(0, drag.startHeight + delta));
	}

	let suppressClick = false;

	function onPointerUp(event: PointerEvent) {
		if (!drag || drag.pointerId !== event.pointerId) return;
		if (drag.moved) {
			open = (dragHeight ?? 0) > openHeight * 0.3;
			suppressClick = true;
		}
		dragHeight = null;
		drag = null;
	}

	function onPointerCancel() {
		dragHeight = null;
		drag = null;
	}

	function onClick() {
		if (suppressClick) {
			suppressClick = false;
			return;
		}
		open = !open;
	}
</script>

<div
	class="glass fixed bottom-0 left-1/2 z-50 w-full max-w-3xl -translate-x-1/2 rounded-t-2xl text-slate-100"
	style="padding-bottom: env(safe-area-inset-bottom)"
	bind:offsetHeight={offset}
>
	<button
		class="flex w-full touch-none flex-col items-center gap-1 px-4 pt-2 pb-2.5 select-none"
		type="button"
		aria-expanded={open}
		aria-controls="gaveta-versiculos"
		onpointerdown={onPointerDown}
		onpointermove={onPointerMove}
		onpointerup={onPointerUp}
		onpointercancel={onPointerCancel}
		onclick={onClick}
	>
		<span aria-hidden="true" class="h-1 w-10 rounded-full bg-white/40"></span>
		<span class="text-sm font-medium">{handleText}</span>
	</button>

	<div
		id="gaveta-versiculos"
		class={['overflow-y-auto overscroll-contain px-5', dragHeight === null && 'transition-[height] duration-200']}
		style="height: {bodyHeight}px"
		inert={!open && dragHeight === null}
	>
		{#if items.length === 0}
			<p class="py-6 text-center text-slate-300">Nenhum versículo neste tópico.</p>
		{:else}
			<ul class="flex flex-col gap-5 py-3">
				{#each items as item (item.key)}
					<li>
						<h3 class="mb-1 font-semibold text-sky-200">{item.label}</h3>
						{#if item.verses.length === 0}
							<p class="text-slate-300 italic">{item.missing}</p>
						{:else}
							<div class="flex flex-col gap-1.5 leading-relaxed text-slate-100">
								{#each item.verses as verse (verse.number)}
									<p><sup class="mr-1 text-xs text-sky-300">{verse.number}</sup>{verse.text}</p>
								{/each}
							</div>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}
	</div>
</div>
