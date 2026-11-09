<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { Passage } from '$lib/api';
	import { pinchZoom, reading } from '$lib/fontSize.svelte';
	import { splitTopics } from '$lib/topics';
	import MarkdownView from './MarkdownView.svelte';
	import VerseDrawer from './VerseDrawer.svelte';
	import ZoomBar from './ZoomBar.svelte';

	let {
		markdown,
		passages = null,
		accountVersion,
		active = $bindable(0),
		scroller = $bindable(null),
		controls = true,
		overlay
	}: {
		markdown: string;
		passages?: Passage[] | null;
		accountVersion: string;
		active?: number;
		scroller?: HTMLElement | null;
		controls?: boolean;
		overlay?: Snippet;
	} = $props();

	let drawerOffset = $state(0);
	const topics = $derived(splitTopics(markdown));
	const activeMarkdown = $derived(topics[Math.min(active, topics.length - 1)]?.markdown ?? '');
</script>

<div class="relative flex min-h-0 flex-1 flex-col" style="--drawer-offset: {drawerOffset}px">
	<div
		bind:this={scroller}
		use:pinchZoom
		class="reading-scroller min-h-0 flex-1 overflow-y-auto"
		style="--reading-font-size: {reading.fontSize}px"
	>
		<div class="reading-pad mx-auto max-w-3xl px-5 pt-6">
			<MarkdownView {markdown} root={scroller} onactive={(index) => (active = index)} />
		</div>
	</div>

	{#if controls}
		<ZoomBar />
		{@render overlay?.()}
		{#if passages}
			<VerseDrawer topicMarkdown={activeMarkdown} {passages} {accountVersion} bind:offset={drawerOffset} />
		{/if}
	{/if}
</div>

<style>
	.reading-scroller {
		container-type: size;
	}

	/* Espaço para barra de zoom, botões de tópico e alça da gaveta; uma altura inteira do scroller deixa o último heading chegar ao topo. */
	.reading-pad {
		padding-bottom: max(60vh, calc(128px + env(safe-area-inset-bottom)));
		padding-bottom: max(100cqh, calc(128px + env(safe-area-inset-bottom)));
	}
</style>
