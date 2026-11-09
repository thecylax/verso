// See https://svelte.dev/docs/kit/types#app.d.ts
declare global {
	namespace App {
		interface PageState {
			/** A nota acabou de ser criada: a captura já foi tentada, não repetir ao abrir. */
			justCreated?: boolean;
		}
	}
}

export {};
