import { redirect } from '@sveltejs/kit';
import { api, ApiError, type User } from '$lib/api';
import { session } from '$lib/session.svelte';

export async function load() {
	try {
		const user = await api<User>('/auth/me');
		session.user = user;
		return { user };
	} catch (error) {
		if (error instanceof ApiError && error.status === 401) {
			session.user = null;
			redirect(307, '/');
		}
		throw error;
	}
}
