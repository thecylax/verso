<script lang="ts">
	let { mode = $bindable('edit') }: { mode: 'edit' | 'view' } = $props();
</script>

<div class="inline-flex rounded-lg border border-white/15 p-0.5" role="group" aria-label="Modo da nota">
	<button
		class={['rounded-md px-3 py-1.5 text-sm font-medium', mode === 'edit' ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-white/5']}
		type="button"
		aria-pressed={mode === 'edit'}
		onclick={() => (mode = 'edit')}
	>
		Editar
	</button>
	<button
		class={['rounded-md px-3 py-1.5 text-sm font-medium', mode === 'view' ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-white/5']}
		type="button"
		aria-pressed={mode === 'view'}
		onclick={() => (mode = 'view')}
	>
		Ver
	</button>
</div>
