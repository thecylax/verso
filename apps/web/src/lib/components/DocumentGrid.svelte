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
	import FolderDialog from '$lib/components/FolderDialog.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import InviteDialog from '$lib/components/InviteDialog.svelte';
	import { session } from '$lib/session.svelte';
	import { faFileLines, faFolder, faPen, faTrashCan, faUserPlus } from '@fortawesome/free-solid-svg-icons';

	let { folderId }: { folderId: string | null } = $props();

	let folders = $state<Folder[]>([]);
	let documents = $state<DocumentSummary[]>([]);
	let breadcrumb = $state<Crumb[]>([]);
	let loading = $state(true);
	let missing = $state(false);
	let notice = $state('');
	let dialog = $state<
		{ mode: 'create' } | { mode: 'rename'; folder: Folder } | { mode: 'delete'; folder: Folder } | null
	>(null);
	let dialogBusy = $state(false);
	let dialogError = $state('');
	let inviteOpen = $state(false);

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

	function openDialog(next: NonNullable<typeof dialog>) {
		dialogError = '';
		dialogBusy = false;
		dialog = next;
	}

	async function submitDialog(name: string) {
		if (!dialog || dialogBusy) return;
		const current = dialog;
		if (current.mode === 'rename' && name === current.folder.name) {
			dialog = null;
			return;
		}
		dialogError = '';
		dialogBusy = true;
		try {
			if (current.mode === 'create') {
				await api('/folders', 'POST', { name, parent_id: folderId });
			} else if (current.mode === 'rename') {
				await api(`/folders/${current.folder.id}`, 'PATCH', { name });
			} else {
				await api(`/folders/${current.folder.id}`, 'DELETE');
			}
			dialog = null;
			await load();
		} catch (error) {
			dialogError = error instanceof Error ? error.message : 'Algo deu errado.';
		} finally {
			dialogBusy = false;
		}
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

<div class="relative mx-auto flex min-h-dvh max-w-6xl flex-col px-4 pt-4 pb-10 sm:px-6" style="padding-top: max(1rem, env(safe-area-inset-top))">
	<img class="brand-mark" src="/icon-512.png" alt="" />
	<div class="relative z-10 flex min-h-0 flex-1 flex-col">
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
			{#if session.user?.can_invite}
				<button class="btn" type="button" onclick={() => (inviteOpen = true)}>
					<Icon icon={faUserPlus} />
					Convidar
				</button>
			{/if}
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
			<button class="btn" type="button" onclick={() => openDialog({ mode: 'create' })}>Nova pasta</button>
			<a class="btn btn-accent" href={newNoteHref}>Nova nota</a>
		</div>

		{#if notice}
			<p class="mb-4 rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200" role="alert">{notice}</p>
		{/if}

		{#if isEmpty}
			<div class="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-white/15 py-16 text-center">
				<p class="text-slate-300">Nada por aqui ainda.</p>
				<div class="flex gap-2">
					<button class="btn" type="button" onclick={() => openDialog({ mode: 'create' })}>Nova pasta</button>
					<a class="btn btn-accent" href={newNoteHref}>Nova nota</a>
				</div>
			</div>
		{:else if !loading}
			<ul class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="grade">
				{#each folders as folder (folder.id)}
					<li class="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-900/70 p-3 hover:border-sky-400/50">
						<a class="flex min-w-0 flex-1 items-center gap-3 py-1" href="/app/pastas/{folder.id}">
							<Icon class="text-xl text-sky-300" icon={faFolder} />
							<span class="truncate font-medium">{folder.name}</span>
						</a>
						<button class="btn h-9 w-9 p-0 text-sm" type="button" onclick={() => openDialog({ mode: 'rename', folder })} aria-label="Renomear pasta {folder.name}" title="Renomear">
							<Icon icon={faPen} />
						</button>
						<button class="btn btn-danger h-9 w-9 p-0 text-sm" type="button" onclick={() => openDialog({ mode: 'delete', folder })} aria-label="Apagar pasta {folder.name}" title="Apagar">
							<Icon icon={faTrashCan} />
						</button>
					</li>
				{/each}
				{#each documents as document (document.id)}
					<li>
						<a
							class="flex h-full items-start gap-3 rounded-xl border border-white/10 bg-slate-900/40 p-4 hover:border-sky-400/50"
							href="/app/notas/{document.id}"
						>
							<Icon class="mt-0.5 text-xl text-sky-300" icon={faFileLines} />
							<span class="flex min-w-0 flex-col gap-1">
								<span class="line-clamp-2 font-semibold text-slate-100">{document.title}</span>
								<time class="text-sm text-slate-400" datetime={document.created_at}>{formatDate(document.created_at)}</time>
							</span>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
	</div>
</div>

{#if inviteOpen}
	<InviteDialog onclose={() => (inviteOpen = false)} />
{/if}

{#if dialog}
	<FolderDialog
		mode={dialog.mode}
		initialName={dialog.mode === 'create' ? '' : dialog.folder.name}
		busy={dialogBusy}
		error={dialogError}
		onclose={() => (dialog = null)}
		onsubmit={submitDialog}
	/>
{/if}

<style>
	.brand-mark {
		position: fixed;
		top: 50%;
		left: 50%;
		z-index: 0;
		width: min(78vmin, 34rem);
		transform: translate(-50%, -50%);
		opacity: 0.55;
		pointer-events: none;
		user-select: none;
	}
</style>
