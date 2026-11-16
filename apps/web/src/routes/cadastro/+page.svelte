<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { api, ApiError, type User } from '$lib/api';
	import { session } from '$lib/session.svelte';

	let name = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let busy = $state(false);
	let checking = $state(true);
	let ready = $state(false);

	const invite = $derived(page.url.searchParams.get('convite')?.trim() ?? '');

	onMount(async () => {
		try {
			session.user = await api<User>('/auth/me');
			await goto('/app', { replaceState: true });
			return;
		} catch {
			// Sem sessão: segue para validar o convite.
		}
		if (!invite) {
			error = 'Cadastro só é possível com um convite.';
			checking = false;
			return;
		}
		try {
			await api(`/auth/invites/${encodeURIComponent(invite)}`);
			ready = true;
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Convite inválido ou já utilizado.';
		} finally {
			checking = false;
		}
	});

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		error = '';
		if (password.length < 8) {
			error = 'A senha precisa ter pelo menos 8 caracteres.';
			return;
		}
		busy = true;
		try {
			session.user = await api<User>('/auth/register', 'POST', { name, email, password, invite });
			await goto('/app');
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Algo deu errado. Tente de novo.';
		} finally {
			busy = false;
		}
	}
</script>

<main class="login-bg flex min-h-dvh items-center justify-center px-4 py-10">
	{#if !checking}
		<div class="glass w-full max-w-sm rounded-2xl p-6 text-slate-100 sm:p-8">
			<h1 class="mb-1 text-3xl font-bold tracking-tight">Verso</h1>
			<p class="mb-6 text-sm text-slate-300">
				{ready ? 'Crie sua conta com este convite.' : 'Este link não serve para criar uma conta.'}
			</p>

			{#if ready}
				<form class="flex flex-col gap-4" onsubmit={submit} novalidate>
					<label class="flex flex-col gap-1 text-sm">
						Nome
						<input class="field" type="text" autocomplete="name" bind:value={name} required maxlength="80" />
					</label>
					<label class="flex flex-col gap-1 text-sm">
						E-mail
						<input class="field" type="email" autocomplete="email" bind:value={email} required />
					</label>
					<label class="flex flex-col gap-1 text-sm">
						Senha
						<input class="field" type="password" autocomplete="new-password" bind:value={password} required />
					</label>

					{#if error}
						<p class="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{error}</p>
					{/if}

					<button
						class="mt-2 rounded-lg bg-sky-500 px-4 py-2.5 font-semibold text-slate-950 hover:bg-sky-400 disabled:opacity-60"
						type="submit"
						disabled={busy}
					>
						Criar conta
					</button>
				</form>
			{:else if error}
				<p class="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{error}</p>
			{/if}

			<p class="mt-5 text-center text-sm">
				<a class="text-sky-300 underline-offset-2 hover:underline" href="/">Já tenho conta</a>
			</p>
		</div>
	{/if}
</main>

<style>
	.login-bg {
		background:
			radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.25), transparent 45%),
			radial-gradient(circle at 80% 70%, rgba(129, 140, 248, 0.25), transparent 50%),
			#0b1220;
	}
</style>
