<script lang="ts">
	import { dismissToast, toasts, type ToastKind } from '$lib/toast.svelte';

	const ACCENT: Record<ToastKind, string> = {
		info: 'border-l-sky-400',
		success: 'border-l-emerald-400',
		warning: 'border-l-amber-400',
		error: 'border-l-red-400'
	};
</script>

<div
	class="pointer-events-none fixed inset-x-0 z-50 flex flex-col items-center gap-2 px-4"
	style="top: calc(env(safe-area-inset-top) + 12px)"
	aria-live="polite"
>
	{#each toasts as toast (toast.id)}
		<div
			class={['glass pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-xl border-l-4 px-4 py-3 text-sm text-slate-100', ACCENT[toast.kind]]}
			role={toast.kind === 'error' || toast.kind === 'warning' ? 'alert' : 'status'}
		>
			<p class="flex-1">{toast.message}</p>
			<button
				class="-my-1 rounded px-1 text-slate-300 hover:text-white"
				type="button"
				aria-label="Fechar aviso"
				onclick={() => dismissToast(toast.id)}>×</button
			>
		</div>
	{/each}
</div>
