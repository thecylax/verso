<script lang="ts">
	import { beforeNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onDestroy, onMount, untrack } from 'svelte';
	import { api, ApiError, countPending, type VersoDocument } from '$lib/api';
	import { refreshMessage, saveFailureMessage, type RefreshSummary } from '$lib/passageStatus';
	import { dismissToast, showToast } from '$lib/toast.svelte';
	import MarkdownEditor from '$lib/components/MarkdownEditor.svelte';
	import ModeToggle from '$lib/components/ModeToggle.svelte';
	import Presentation from '$lib/components/Presentation.svelte';
	import ReadingPane from '$lib/components/ReadingPane.svelte';
	import { session } from '$lib/session.svelte';

	const SAVE_DELAY = 800;
	const STATUS_TEXT = { idle: '', saving: 'Salvando…', saved: 'Salvo', error: 'Erro ao salvar' } as const;

	const id = page.params.id as string;

	let doc = $state<VersoDocument | null>(null);
	let missing = $state(false);
	let title = $state('');
	let content = $state('');
	let mode = $state<'edit' | 'view'>('view');
	let presenting = $state(false);
	let status = $state<keyof typeof STATUS_TEXT>('idle');

	const backHref = $derived(doc?.folder_id ? `/app/pastas/${doc.folder_id}` : '/app');
	const accountVersion = $derived(session.user?.bible_version ?? 'nvi');

	let lastSent = { title: '', content: '' };
	let timer: ReturnType<typeof setTimeout> | undefined;
	let inflight = false;
	let queued = false;
	let refreshing = false;

	const PASSAGES_TOAST = 'passages';

	onMount(async () => {
		try {
			const loaded = await api<VersoDocument>(`/documents/${id}`);
			title = loaded.title;
			content = loaded.content_md;
			lastSent = { title, content };
			mode = content.trim() ? 'view' : 'edit';
			doc = loaded;
			if (loaded.passages_pending && !page.state.justCreated) refreshPassages();
		} catch (error) {
			if (error instanceof ApiError && error.status === 404) missing = true;
			else throw error;
		}
	});

	async function refreshPassages() {
		refreshing = true;
		showToast('info', 'Buscando versículos que faltaram…', { id: PASSAGES_TOAST, timeout: 0 });
		try {
			const response = await api<{ document: VersoDocument; refresh: RefreshSummary }>(
				`/documents/${id}/passages/refresh`,
				'POST'
			);
			if (doc) doc.passages = response.document.passages;
			const outcome = refreshMessage(response.refresh);
			if (outcome) showToast(outcome.kind, outcome.message, { id: PASSAGES_TOAST, timeout: 8000 });
			else dismissToast(PASSAGES_TOAST);
		} catch {
			showToast('error', 'Não foi possível atualizar os versículos agora.', { id: PASSAGES_TOAST, timeout: 8000 });
		} finally {
			refreshing = false;
			if (queued) {
				queued = false;
				flush();
			}
		}
	}

	$effect(() => {
		const changed = title !== lastSent.title || content !== lastSent.content;
		if (!doc || !changed) return;
		untrack(schedule);
	});

	function schedule() {
		clearTimeout(timer);
		timer = setTimeout(flush, SAVE_DELAY);
	}

	async function flush() {
		timer = undefined;
		if (inflight || refreshing) {
			queued = true;
			return;
		}
		const body = { title, content_md: content };
		if (body.title === lastSent.title && body.content_md === lastSent.content) return;
		inflight = true;
		status = 'saving';
		try {
			const saved = await api<VersoDocument>(`/documents/${id}`, 'PATCH', body);
			lastSent = { title: body.title, content: body.content_md };
			if (doc) {
				const pendingBefore = countPending(doc.passages);
				const pendingAfter = countPending(saved.passages);
				doc.title = saved.title;
				doc.passages = saved.passages;
				if (pendingAfter > pendingBefore) {
					showToast('warning', saveFailureMessage(pendingAfter), { id: PASSAGES_TOAST, timeout: 8000 });
				}
			}
			status = 'saved';
		} catch {
			status = 'error';
		} finally {
			inflight = false;
			if (queued) {
				queued = false;
				flush();
			}
		}
	}

	function flushPending() {
		if (timer !== undefined) {
			clearTimeout(timer);
			flush();
		}
	}

	beforeNavigate(flushPending);
	onDestroy(flushPending);

	function present() {
		mode = 'view';
		presenting = true;
	}

	function stopPresenting() {
		presenting = false;
		mode = 'view';
	}

	async function remove() {
		if (!confirm('Apagar esta nota? A exclusão é definitiva.')) return;
		clearTimeout(timer);
		timer = undefined;
		try {
			await api(`/documents/${id}`, 'DELETE');
			await goto(backHref, { replaceState: true });
		} catch (error) {
			alert(error instanceof Error ? error.message : 'Não foi possível apagar a nota.');
		}
	}
</script>

{#if missing}
	<div class="flex min-h-dvh flex-col items-center justify-center gap-4 px-4">
		<p class="text-slate-300">Nota não encontrada.</p>
		<a class="btn" href="/app">Voltar para o início</a>
	</div>
{:else if doc}
	<div class="flex h-dvh flex-col" style="padding-top: env(safe-area-inset-top)">
		<header class="flex flex-col gap-2 border-b border-white/10 px-4 py-3 lg:flex-row lg:items-center">
			<div class="flex items-center justify-between gap-2">
				<a class="text-sm text-sky-300 hover:underline" href={backHref}>← Voltar</a>
				<span class="text-sm text-slate-400 lg:hidden" aria-live="polite">{STATUS_TEXT[status]}</span>
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
				<span class={['hidden min-w-24 text-sm lg:inline', status === 'error' ? 'text-red-300' : 'text-slate-400']} aria-live="polite">
					{STATUS_TEXT[status]}
				</span>
				<ModeToggle bind:mode />
				<button class="btn btn-primary" type="button" onclick={present}>Apresentar</button>
				<button class="btn btn-danger" type="button" onclick={remove}>Apagar</button>
			</div>
		</header>

		{#if mode === 'edit'}
			<div class="min-h-0 flex-1">
				<MarkdownEditor bind:value={content} />
			</div>
		{:else}
			<ReadingPane markdown={content} passages={doc.passages} {accountVersion} controls={!presenting} />
		{/if}
	</div>

	{#if presenting}
		<Presentation markdown={content} passages={doc.passages} {accountVersion} onclose={stopPresenting} />
	{/if}
{/if}
