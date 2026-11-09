<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api, ApiError, type User } from '$lib/api';
	import { session } from '$lib/session.svelte';

	let mode = $state<'login' | 'register'>('login');
	let name = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let busy = $state(false);
	let checking = $state(true);

	onMount(async () => {
		try {
			session.user = await api<User>('/auth/me');
			await goto('/app', { replaceState: true });
		} catch {
			checking = false;
		}
	});

	function switchMode(next: 'login' | 'register') {
		mode = next;
		error = '';
	}

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		error = '';
		if (mode === 'register' && password.length < 8) {
			error = 'A senha precisa ter pelo menos 8 caracteres.';
			return;
		}
		busy = true;
		try {
			session.user =
				mode === 'login'
					? await api<User>('/auth/login', 'POST', { email, password })
					: await api<User>('/auth/register', 'POST', { name, email, password });
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
				{mode === 'login' ? 'Entre para ver suas notas.' : 'Crie sua conta para começar.'}
			</p>

			<form class="flex flex-col gap-4" onsubmit={submit} novalidate>
				{#if mode === 'register'}
					<label class="flex flex-col gap-1 text-sm">
						Nome
						<input class="field" type="text" autocomplete="name" bind:value={name} required maxlength="80" />
					</label>
				{/if}
				<label class="flex flex-col gap-1 text-sm">
					E-mail
					<input class="field" type="email" autocomplete="email" bind:value={email} required />
				</label>
				<label class="flex flex-col gap-1 text-sm">
					Senha
					<input
						class="field"
						type="password"
						autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
						bind:value={password}
						required
					/>
				</label>

				{#if error}
					<p class="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{error}</p>
				{/if}

				<button
					class="mt-2 rounded-lg bg-sky-500 px-4 py-2.5 font-semibold text-slate-950 hover:bg-sky-400 disabled:opacity-60"
					type="submit"
					disabled={busy}
				>
					{mode === 'login' ? 'Entrar' : 'Criar conta'}
				</button>
			</form>

			<p class="mt-5 text-center text-sm">
				{#if mode === 'login'}
					<button class="text-sky-300 underline-offset-2 hover:underline" type="button" onclick={() => switchMode('register')}>
						Criar conta
					</button>
				{:else}
					<button class="text-sky-300 underline-offset-2 hover:underline" type="button" onclick={() => switchMode('login')}>
						Já tenho conta
					</button>
				{/if}
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
