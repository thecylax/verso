<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import {
		api,
		ApiError,
		BIBLE_VERSIONS,
		formatDate,
		type Crumb,
		type DocumentSummary,
		type Folder,
		type User
	} from '$lib/api';
	import { session } from '$lib/session.svelte';

	let { folderId }: { folderId: string | null } = $props();

	let folders = $state<Folder[]>([]);
	let documents = $state<DocumentSummary[]>([]);
	let breadcrumb = $state<Crumb[]>([]);
	let loading = $state(true);
	let missing = $state(false);
	let notice = $state('');

	const newNoteHref = $derived(folderId ? `/app/notas/nova?pasta=${folderId}` : '/app/notas/nova');
	const isEmpty = $derived(!loading && folders.length === 0 && documents.length === 0);

	async function load() {
		try {
			const [folderList, documentList] = await Promise.all([
				api<{ folders: Folder[]; breadcrumb: Crumb[] }>(folderId ? `/folders?parent_id=${folderId}` : '/folders'),
				api<{ documents: DocumentSummary[] }>(folderId ? `/documents?folder_id=${folderId}` : '/documents')
			]);
			folders = folderList.folders;
			breadcrumb = folderList.breadcrumb;
			documents = documentList.documents;
		} catch (error) {
			if (error instanceof ApiError && error.status === 404) missing = true;
			else notice = error instanceof Error ? error.message : 'Não foi possível carregar.';
		} finally {
			loading = false;
		}
	}

	onMount(load);

	async function run(action: () => Promise<unknown>) {
		notice = '';
		try {
			await action();
			await load();
		} catch (error) {
			notice = error instanceof Error ? error.message : 'Algo deu errado.';
		}
	}

	function newFolder() {
		const name = prompt('Nome da nova pasta');
		if (name === null || !name.trim()) return;
		run(() => api('/folders', 'POST', { name, parent_id: folderId }));
	}

	function renameFolder(folder: Folder) {
		const name = prompt('Novo nome da pasta', folder.name);
		if (name === null || !name.trim() || name.trim() === folder.name) return;
		run(() => api(`/folders/${folder.id}`, 'PATCH', { name }));
	}

	function deleteFolder(folder: Folder) {
		if (!confirm(`Apagar a pasta “${folder.name}”?`)) return;
		run(() => api(`/folders/${folder.id}`, 'DELETE'));
	}

	async function changeVersion(event: Event) {
		const bible_version = (event.currentTarget as HTMLSelectElement).value;
		notice = '';
		try {
			session.user = await api<User>('/auth/me', 'PATCH', { bible_version });
		} catch (error) {
			notice = error instanceof Error ? error.message : 'Não foi possível mudar a versão.';
		}
	}

	async function logout() {
		try {
			await api('/auth/logout', 'POST');
		} finally {
			session.user = null;
			await goto('/', { replaceState: true });
		}
	}
</script>

<div class="mx-auto flex min-h-dvh max-w-6xl flex-col px-4 pt-4 pb-10 sm:px-6" style="padding-top: max(1rem, env(safe-area-inset-top))">
	<header class="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
		<nav aria-label="Trilha" class="min-w-0 flex-1">
			<ol class="flex flex-wrap items-center gap-1 text-lg">
				<li>
					{#if folderId}
						<a class="font-bold text-sky-300 hover:underline" href="/app">Verso</a>
					{:else}
						<span class="font-bold">Verso</span>
					{/if}
				</li>
				{#each breadcrumb as crumb, i (crumb.id)}
					<li aria-hidden="true" class="text-slate-500">/</li>
					<li class="min-w-0 truncate">
						{#if i === breadcrumb.length - 1}
							<span aria-current="page">{crumb.name}</span>
						{:else}
							<a class="text-sky-300 hover:underline" href="/app/pastas/{crumb.id}">{crumb.name}</a>
						{/if}
					</li>
				{/each}
			</ol>
		</nav>

		<div class="flex items-center gap-2">
			<label class="flex items-center gap-2 text-sm text-slate-300">
				Versão bíblica
				<select
					class="rounded-lg border border-white/15 bg-slate-900 px-2 py-1.5 text-slate-100"
					value={session.user?.bible_version ?? 'nvi'}
					onchange={changeVersion}
				>
					{#each BIBLE_VERSIONS as version (version)}
						<option value={version}>{version.toUpperCase()}</option>
					{/each}
				</select>
			</label>
			<button class="btn" type="button" onclick={logout}>Sair</button>
		</div>
	</header>

	{#if missing}
		<div class="py-16 text-center">
			<p class="mb-4 text-slate-300">Pasta não encontrada.</p>
			<a class="btn" href="/app">Voltar para o início</a>
		</div>
	{:else}
		<div class="flex flex-wrap gap-2 py-4">
			<button class="btn" type="button" onclick={newFolder}>Nova pasta</button>
			<a class="btn btn-primary" href={newNoteHref}>Nova nota</a>
		</div>

		{#if notice}
			<p class="mb-4 rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{notice}</p>
		{/if}

		{#if isEmpty}
			<div class="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-white/15 py-16 text-center">
				<p class="text-slate-300">Nada por aqui ainda.</p>
				<div class="flex gap-2">
					<button class="btn" type="button" onclick={newFolder}>Nova pasta</button>
					<a class="btn btn-primary" href={newNoteHref}>Nova nota</a>
				</div>
			</div>
		{:else if !loading}
			<ul class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="grade">
				{#each folders as folder (folder.id)}
					<li class="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-900/70 p-3 hover:border-sky-400/50">
						<a class="flex min-w-0 flex-1 items-center gap-3 py-1" href="/app/pastas/{folder.id}">
							<span aria-hidden="true" class="text-xl">📁</span>
							<span class="truncate font-medium">{folder.name}</span>
						</a>
						<button class="btn px-2 py-1 text-xs" type="button" onclick={() => renameFolder(folder)} aria-label="Renomear pasta {folder.name}">
							Renomear
						</button>
						<button class="btn btn-danger px-2 py-1 text-xs" type="button" onclick={() => deleteFolder(folder)} aria-label="Apagar pasta {folder.name}">
							Apagar
						</button>
					</li>
				{/each}
				{#each documents as document (document.id)}
					<li>
						<a
							class="flex h-full flex-col gap-1 rounded-xl border border-white/10 bg-slate-900/40 p-4 hover:border-sky-400/50"
							href="/app/notas/{document.id}"
						>
							<span class="line-clamp-2 font-semibold text-slate-100">{document.title}</span>
							<time class="text-sm text-slate-400" datetime={document.created_at}>{formatDate(document.created_at)}</time>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</div>
