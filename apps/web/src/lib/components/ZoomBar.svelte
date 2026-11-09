<script lang="ts">
	import { reading, zoomIn, zoomOut } from '$lib/fontSize.svelte';
	import { FONT_MAX, FONT_MIN } from '$lib/zoom';
</script>

<div
	class="glass fixed left-1/2 z-50 flex -translate-x-1/2 items-center gap-1 rounded-full p-1 text-slate-100"
	style="bottom: calc(var(--drawer-offset, 0px) + 12px)"
	role="group"
	aria-label="Tamanho da fonte"
>
	<button
		class="h-10 w-12 rounded-full text-base font-semibold hover:bg-white/10 disabled:opacity-40"
		type="button"
		onclick={zoomOut}
		disabled={reading.fontSize <= FONT_MIN}
		aria-label="Diminuir fonte"
	>
		A−
	</button>
	<span class="w-12 text-center text-sm tabular-nums" aria-live="polite">{reading.fontSize}px</span>
	<button
		class="h-10 w-12 rounded-full text-lg font-semibold hover:bg-white/10 disabled:opacity-40"
		type="button"
		onclick={zoomIn}
		disabled={reading.fontSize >= FONT_MAX}
		aria-label="Aumentar fonte"
	>
		A+
	</button>
</div>
