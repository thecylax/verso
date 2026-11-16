<script lang="ts">
	import { onMount, untrack } from 'svelte';

	let {
		mode,
		initialName = '',
		busy = false,
		error = '',
		onclose,
		onsubmit
	}: {
		mode: 'create' | 'rename' | 'delete';
		initialName?: string;
		busy?: boolean;
		error?: string;
		onclose: () => void;
		onsubmit: (name: string) => void;
	} = $props();

	let name = $state(untrack(() => initialName));
	let localError = $state('');
	let input = $state<HTMLInputElement | null>(null);
	let cancelButton = $state<HTMLButtonElement | null>(null);

	const title = $derived(
		mode === 'create' ? 'Nova pasta' : mode === 'rename' ? 'Renomear pasta' : 'Apagar pasta'
	);
	const confirmLabel = $derived(mode === 'create' ? 'Criar' : mode === 'rename' ? 'Salvar' : 'Apagar');
	const shownError = $derived(localError || error);

	function requestClose() {
		if (!busy) onclose();
	}

	function submit(event: SubmitEvent) {
		event.preventDefault();
		if (busy) return;
		if (mode === 'delete') {
			onsubmit('');
			return;
		}
		const trimmed = name.trim();
		if (trimmed.length < 1 || trimmed.length > 80) {
			localError = 'O nome da pasta deve ter de 1 a 80 caracteres.';
			return;
		}
		localError = '';
		onsubmit(trimmed);
	}

	onMount(() => {
		const previousOverflow = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		if (mode === 'delete') cancelButton?.focus();
		else {
			input?.focus();
			input?.select();
		}
		const onKey = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				event.preventDefault();
				requestClose();
			}
		};
		document.addEventListener('keydown', onKey);
		return () => {
			document.body.style.overflow = previousOverflow;
			document.removeEventListener('keydown', onKey);
		};
	});
</script>

<div class="backdrop">
	<button class="backdrop-dismiss" type="button" tabindex="-1" aria-label="Fechar" onclick={requestClose}></button>
	<div
		class="glass panel"
		role="dialog"
		tabindex="-1"
		aria-modal="true"
		aria-labelledby="folder-dialog-title"
		aria-describedby={shownError ? 'folder-dialog-error' : undefined}
	>
		<h2 id="folder-dialog-title" class="text-lg font-semibold text-slate-50">{title}</h2>

		<form class="mt-4 flex flex-col gap-4" onsubmit={submit} novalidate>
			{#if mode === 'delete'}
				<p class="text-sm leading-relaxed text-slate-300">
					Apagar a pasta “{initialName}”? Só uma pasta vazia pode ser apagada.
				</p>
			{:else}
				<label class="flex flex-col gap-1 text-sm text-slate-300">
					Nome
					<input
						bind:this={input}
						bind:value={name}
						class="field"
						type="text"
						name="folder-name"
						maxlength="80"
						autocomplete="off"
						enterkeyhint="done"
						required
						oninput={() => (localError = '')}
					/>
				</label>
			{/if}

			{#if shownError}
				<p id="folder-dialog-error" class="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">
					{shownError}
				</p>
			{/if}

			<div class="flex gap-2">
				<button bind:this={cancelButton} class="btn min-h-11 flex-1" type="button" onclick={requestClose} disabled={busy}>
					Cancelar
				</button>
				<button
					class="btn min-h-11 flex-1 {mode === 'delete' ? 'btn-danger' : 'btn-primary'}"
					type="submit"
					disabled={busy}
				>
					{busy ? 'Aguarde…' : confirmLabel}
				</button>
			</div>
		</form>
	</div>
</div>

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		z-index: 60;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding:
			max(12vh, env(safe-area-inset-top))
			max(1rem, env(safe-area-inset-right))
			max(1rem, env(safe-area-inset-bottom))
			max(1rem, env(safe-area-inset-left));
		background: rgba(2, 6, 23, 0.72);
	}

	.backdrop-dismiss {
		position: absolute;
		inset: 0;
		border: 0;
		background: transparent;
	}

	.panel {
		position: relative;
		z-index: 1;
		width: min(100%, 26rem);
		border-radius: 1rem;
		padding: 1.25rem;
	}

	@media (min-width: 640px) {
		.backdrop {
			align-items: center;
			padding-top: max(1rem, env(safe-area-inset-top));
		}
	}
</style>
