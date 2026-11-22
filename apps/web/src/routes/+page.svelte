<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api, ApiError, type User } from '$lib/api';
	import { session } from '$lib/session.svelte';

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

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		error = '';
		busy = true;
		try {
			session.user = await api<User>('/auth/login', 'POST', { email, password });
			await goto('/app');
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Algo deu errado. Tente de novo.';
		} finally {
			busy = false;
		}
	}
</script>

<main class="login-bg relative flex min-h-dvh items-center justify-center px-4 py-10">
	<div class="absolute left-4 top-4 flex items-center gap-2 sm:left-6 sm:top-6" aria-label="Verso">
		<img class="h-11 w-11 rounded-xl border border-white/10 shadow-lg sm:h-12 sm:w-12" src="/icon-192.png" alt="" />
		<span class="text-xl font-bold tracking-tight text-slate-100 sm:text-2xl">Verso</span>
	</div>
	{#if !checking}
		<div class="glass w-full max-w-sm rounded-2xl p-6 text-slate-100 sm:p-8">
			<h1 class="mb-1 text-3xl font-bold tracking-tight">Login</h1>

			<form class="flex flex-col gap-4" onsubmit={submit} novalidate>
				<label class="flex flex-col gap-1 text-sm">
					E-mail
					<input class="field" type="email" autocomplete="email" bind:value={email} required />
				</label>
				<label class="flex flex-col gap-1 text-sm">
					Senha
					<input class="field" type="password" autocomplete="current-password" bind:value={password} required />
				</label>

				{#if error}
					<p class="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{error}</p>
				{/if}

				<button
					class="mt-2 rounded-lg bg-sky-500 px-4 py-2.5 font-semibold text-slate-950 hover:bg-sky-400 disabled:opacity-60"
					type="submit"
					disabled={busy}
				>
					Entrar
				</button>
			</form>
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
