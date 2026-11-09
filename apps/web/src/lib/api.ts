export type User = {
	id: string;
	name: string;
	email: string;
	bible_version: string;
};

export type Folder = {
	id: string;
	name: string;
	parent_id: string | null;
	created_at: string;
};

export type Crumb = { id: string; name: string };

export type DocumentSummary = {
	id: string;
	title: string;
	folder_id: string | null;
	created_at: string;
	updated_at: string;
};

export type Verse = { number: number; text: string };

export type Passage = {
	version: string;
	abbrev: string;
	chapter: number;
	start: number | null;
	end: number | null;
	book_name: string;
	verses: Verse[];
	error: string | null;
};

export type VersoDocument = DocumentSummary & {
	content_md: string;
	passages: Passage[];
	passages_pending: boolean;
};

const RETRYABLE_ERRORS = new Set(['upstream_unavailable', 'rate_limited', 'bible_not_configured']);

export function countPending(passages: Passage[]): number {
	return passages.filter((passage) => passage.error !== null && RETRYABLE_ERRORS.has(passage.error)).length;
}

export class ApiError extends Error {
	constructor(
		readonly status: number,
		readonly code: string,
		message: string
	) {
		super(message);
	}
}

type Method = 'GET' | 'POST' | 'PATCH' | 'DELETE';

export async function api<T>(path: string, method: Method = 'GET', body?: unknown): Promise<T> {
	let response: Response;
	try {
		response = await fetch(`/api${path}`, {
			method,
			credentials: 'include',
			headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
			body: body === undefined ? undefined : JSON.stringify(body)
		});
	} catch {
		throw new ApiError(0, 'network_error', 'Sem conexão com o servidor.');
	}
	if (response.status === 204) return undefined as T;
	const data = await response.json().catch(() => null);
	if (!response.ok) {
		const error = data?.error;
		throw new ApiError(
			response.status,
			error?.code ?? 'http_error',
			error?.message ?? 'Algo deu errado. Tente de novo.'
		);
	}
	return data as T;
}

export const BIBLE_VERSIONS = ['nvi', 'acf', 'aa', 'ntlh', 'nvt', 'kjv'] as const;

const dateFormat = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });

export function formatDate(iso: string): string {
	return dateFormat.format(new Date(iso));
}
