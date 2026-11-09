import type { ToastKind } from './toast.svelte';

export type RefreshSummary = { updated: number; failed: number };

const RETRY_HINT = 'Tentaremos de novo quando a nota for aberta.';

function passages(count: number): string {
	return count === 1 ? '1 passagem' : `${count} passagens`;
}

/** Aviso depois de tentar buscar de novo as passagens que faltavam; `null` quando nada mudou. */
export function refreshMessage({ updated, failed }: RefreshSummary): { kind: ToastKind; message: string } | null {
	if (failed === 0 && updated === 0) return null;
	if (failed === 0) return { kind: 'success', message: `Versículos atualizados: ${passages(updated)}.` };
	if (updated === 0) {
		return { kind: 'warning', message: `Não foi possível buscar ${passages(failed)}. ${RETRY_HINT}` };
	}
	return {
		kind: 'warning',
		message: `Versículos atualizados: ${passages(updated)}. Ainda sem texto: ${passages(failed)}. ${RETRY_HINT}`
	};
}

/** Aviso quando um salvamento ou a criação deixou passagens sem texto. */
export function saveFailureMessage(failed: number): string {
	return `Não foi possível buscar ${passages(failed)}. ${RETRY_HINT}`;
}
