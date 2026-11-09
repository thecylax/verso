export type ToastKind = 'info' | 'success' | 'warning' | 'error';

export type Toast = { id: string; kind: ToastKind; message: string };

const DEFAULT_TIMEOUT = 5000;

export const toasts = $state<Toast[]>([]);
const timers = new Map<string, ReturnType<typeof setTimeout>>();
let counter = 0;

/** Mostra um aviso. Com o mesmo `id`, substitui o anterior em vez de empilhar. `timeout: 0` fica até ser trocado. */
export function showToast(kind: ToastKind, message: string, options: { id?: string; timeout?: number } = {}): string {
	const id = options.id ?? `toast-${++counter}`;
	const existing = toasts.findIndex((toast) => toast.id === id);
	if (existing >= 0) toasts[existing] = { id, kind, message };
	else toasts.push({ id, kind, message });

	clearTimeout(timers.get(id));
	timers.delete(id);
	const timeout = options.timeout ?? DEFAULT_TIMEOUT;
	if (timeout > 0) timers.set(id, setTimeout(() => dismissToast(id), timeout));
	return id;
}

export function dismissToast(id: string): void {
	clearTimeout(timers.get(id));
	timers.delete(id);
	const index = toasts.findIndex((toast) => toast.id === id);
	if (index >= 0) toasts.splice(index, 1);
}
