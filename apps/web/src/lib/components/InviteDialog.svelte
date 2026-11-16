<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '$lib/api';

	let { onclose }: { onclose: () => void } = $props();

	let link = $state('');
	let error = $state('');
	let busy = $state(true);
	let copied = $state(false);
	let closeButton = $state<HTMLButtonElement | null>(null);

	function requestClose() {
		onclose();
	}

	async function copy() {
		if (!link) return;
		try {
			await navigator.clipboard.writeText(link);
			copied = true;
			error = '';
		} catch {
			copied = false;
			error = 'Não foi possível copiar. Selecione o link e copie manualmente.';
		}
	}

	onMount(() => {
		const previousOverflow = document.body.style.overflow;
		document.body.style.overflow = 'hidden';
		let alive = true;
		const onKey = (event: KeyboardEvent) => {
			if (event.key === 'Escape') {
				event.preventDefault();
				requestClose();
			}
		};
		document.addEventListener('keydown', onKey);
		void (async () => {
			try {
				const created = await api<{ token: string; expires_at: string }>('/auth/invites', 'POST');
				if (!alive) return;
				link = `${location.origin}/cadastro?convite=${encodeURIComponent(created.token)}`;
			} catch (err) {
				if (!alive) return;
				error = err instanceof ApiError ? err.message : 'Não foi possível gerar o convite.';
			} finally {
				if (alive) {
					busy = false;
					closeButton?.focus();
				}
			}
		})();
		return () => {
			alive = false;
			document.body.style.overflow = previousOverflow;
			document.removeEventListener('keydown', onKey);
		};
	});
</script>

<div class="backdrop">
	<button class="backdrop-dismiss" type="button" tabindex="-1" aria-label="Fechar" onclick={requestClose}></button>
	<div class="glass panel" role="dialog" tabindex="-1" aria-modal="true" aria-labelledby="invite-dialog-title">
		<h2 id="invite-dialog-title" class="text-lg font-semibold text-slate-50">Convidar</h2>
		<p class="mt-3 text-sm leading-relaxed text-slate-300">
			Quem receber este link pode criar uma conta. Ele vale por 48 horas e só pode ser usado uma vez.
		</p>

		{#if busy}
			<p class="mt-4 text-sm text-slate-300">Gerando convite…</p>
		{:else if link}
			<label class="mt-4 flex flex-col gap-1 text-sm text-slate-300">
				Link
				<input class="field" type="text" readonly value={link} onclick={(event) => event.currentTarget.select()} />
			</label>
		{/if}

		{#if error}
			<p class="mt-4 rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{error}</p>
		{/if}

		<div class="mt-4 flex gap-2">
			<button bind:this={closeButton} class="btn min-h-11 flex-1" type="button" onclick={requestClose}>Fechar</button>
			{#if link}
				<button class="btn btn-primary min-h-11 flex-1" type="button" onclick={copy}>
					{copied ? 'Copiado' : 'Copiar link'}
				</button>
			{/if}
		</div>
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
