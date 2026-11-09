<script lang="ts">
	import MarkdownIt from 'markdown-it';
	import { splitTopics } from '$lib/topics';

	let {
		markdown,
		root = null,
		onactive
	}: { markdown: string; root?: HTMLElement | null; onactive?: (index: number) => void } = $props();

	const renderer = new MarkdownIt({ html: false, linkify: true, breaks: false });

	const topics = $derived(splitTopics(markdown));
	const rendered = $derived(topics.map((topic) => renderer.render(topic.markdown)));

	let container: HTMLDivElement;

	$effect(() => {
		void rendered;
		if (!onactive || !root || !container) return;
		const report = onactive;
		const visible = new Set<number>();
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					const index = Number((entry.target as HTMLElement).dataset.topicIndex);
					// Seção vazia ou só encostando na borda da faixa não conta como visível.
					if (entry.isIntersecting && entry.intersectionRect.height > 1) visible.add(index);
					else visible.delete(index);
				}
				if (visible.size > 0) report(Math.min(...visible));
			},
			{ root, rootMargin: '0px 0px -60% 0px' }
		);
		container.querySelectorAll('section[data-topic-index]').forEach((section) => observer.observe(section));
		return () => observer.disconnect();
	});
</script>

<div class="reading" bind:this={container}>
	{#each topics as topic, i (topic.index)}
		<section data-topic-index={topic.index} id="topico-{topic.index}">
			{@html rendered[i]}
		</section>
	{/each}
</div>
