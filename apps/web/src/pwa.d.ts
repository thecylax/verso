declare module 'virtual:pwa-register' {
	export function registerSW(options?: { immediate?: boolean }): () => Promise<void>;
}

declare module 'virtual:pwa-info' {
	export const pwaInfo: { webManifest: { href: string; linkTag: string } } | undefined;
}
