import adapter from '@sveltejs/adapter-static';
import tailwindcss from '@tailwindcss/vite';
import { withPwa } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vitest/config';

const apiTarget = process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000';
const proxy = {
	'/api': { target: apiTarget, changeOrigin: false }
};

export default defineConfig({
	plugins: [
		tailwindcss(),
		withPwa(
			{
				adapter: adapter({ fallback: 'index.html' })
			},
			{
				registerType: 'autoUpdate',
				injectRegister: false,
				manifest: {
					name: 'Verso',
					short_name: 'Verso',
					lang: 'pt-BR',
					start_url: '/app',
					scope: '/',
					display: 'standalone',
					theme_color: '#0f172a',
					background_color: '#0f172a',
					icons: [
						{ src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
						{ src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
						{ src: '/icon-maskable-192.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
						{ src: '/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
					]
				},
				generateSW: {
					globPatterns: ['client/**/*.{js,css,html,png,svg,ico,webmanifest}'],
					// O plugin sempre acrescenta prerendered/**, que fica vazio numa SPA sem prerender.
					globStrict: false,
					navigateFallbackDenylist: [/^\/api\//],
					runtimeCaching: []
				},
				kit: {
					adapterFallback: 'index.html',
					spa: true
				}
			}
		)
	],
	server: {
		port: 5173,
		strictPort: true,
		proxy,
		watch: process.env.CHOKIDAR_USEPOLLING === 'true' ? { usePolling: true, interval: 300 } : undefined
	},
	preview: {
		port: 4173,
		proxy
	},
	test: {
		include: ['src/**/*.test.ts'],
		environment: 'node'
	}
});
