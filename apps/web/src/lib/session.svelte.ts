import type { User } from './api';

export const session = $state<{ user: User | null }>({ user: null });
