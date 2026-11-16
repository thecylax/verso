<script lang="ts">
	import type { IconDefinition } from '@fortawesome/fontawesome-svg-core';

	let { icon, class: className = '' }: { icon: IconDefinition; class?: string } = $props();

	const width = $derived(icon.icon[0]);
	const height = $derived(icon.icon[1]);
	const paths = $derived(Array.isArray(icon.icon[4]) ? icon.icon[4] : [icon.icon[4]]);
</script>

<svg class="icon {className}" viewBox="0 0 {width} {height}" aria-hidden="true">
	{#each paths as d (d)}
		<path fill="currentColor" {d} />
	{/each}
</svg>

<style>
	.icon {
		display: inline-block;
		width: 1em;
		height: 1em;
		vertical-align: -0.125em;
		overflow: visible;
	}
</style>
