<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api, ApiError, countPending, type VersoDocument } from '$lib/api';
	import { saveFailureMessage } from '$lib/passageStatus';
	import { showToast } from '$lib/toast.svelte';
	import MarkdownEditor from '$lib/components/MarkdownEditor.svelte';
	import ModeToggle from '$lib/components/ModeToggle.svelte';
	import ReadingPane from '$lib/components/ReadingPane.svelte';
	import { session } from '$lib/session.svelte';

	const folderId = page.url.searchParams.get('pasta') || null;
	const storageKey = `verso.draft:${folderId ?? 'root'}`;
	const backHref = folderId ? `/app/pastas/${folderId}` : '/app';

	function readDraft(): { title: string; content_md: string } {
		try {
			const stored = JSON.parse(localStorage.getItem(storageKey) ?? 'null');
			if (stored && typeof stored.title === 'string' && typeof stored.content_md === 'string') return stored;
		} catch {
			// rascunho corrompido: começa do zero
		}
		return { title: '', content_md: '' };
	}

	const initial = readDraft();
	let title = $state(initial.title);
	let content = $state(initial.content_md);
	let mode = $state<'edit' | 'view'>('edit');
	let busy = $state(false);
	let error = $state('');

	$effect(() => {
		localStorage.setItem(storageKey, JSON.stringify({ title, content_md: content }));
	});

	async function create() {
		busy = true;
		error = '';
		try {
			const created = await api<VersoDocument>('/documents', 'POST', {
				folder_id: folderId,
				title,
				content_md: content
			});
			localStorage.removeItem(storageKey);
			const failed = countPending(created.passages);
			if (failed > 0) showToast('warning', saveFailureMessage(failed), { id: 'passages', timeout: 8000 });
			await goto(`/app/notas/${created.id}`, { replaceState: true, state: { justCreated: true } });
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Não foi possível criar a nota.';
			busy = false;
		}
	}
</script>

<div class="flex h-dvh flex-col" style="padding-top: env(safe-area-inset-top)">
	<header class="flex flex-col gap-2 border-b border-white/10 px-4 py-3 lg:flex-row lg:items-center">
		<div class="flex items-center justify-between gap-2">
			<a class="text-sm text-sky-300 hover:underline" href={backHref}>← Voltar</a>
			<span class="text-sm text-slate-400 lg:hidden">Rascunho</span>
		</div>
		<input
			class="field min-w-0 flex-1 text-lg font-semibold"
			type="text"
			placeholder="Sem título"
			aria-label="Título"
			maxlength="160"
			bind:value={title}
		/>
		<div class="flex flex-wrap items-center gap-2">
			<span class="hidden text-sm text-slate-400 lg:inline">Rascunho</span>
			<ModeToggle bind:mode />
			<button class="btn btn-primary" type="button" onclick={create} disabled={busy}>Criar nota</button>
		</div>
		{#if error}
			<p class="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{error}</p>
		{/if}
	</header>

	{#if mode === 'edit'}
		<div class="min-h-0 flex-1">
			<MarkdownEditor bind:value={content} />
		</div>
	{:else}
		<ReadingPane markdown={content} accountVersion={session.user?.bible_version ?? 'nvi'} />
	{/if}
</div>
