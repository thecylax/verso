<script lang="ts">
	import { markdown } from '@codemirror/lang-markdown';
	import { oneDark } from '@codemirror/theme-one-dark';
	import { EditorView, basicSetup } from 'codemirror';
	import { onMount } from 'svelte';

	let { value = $bindable('') }: { value: string } = $props();

	let host: HTMLDivElement;

	onMount(() => {
		const view = new EditorView({
			parent: host,
			doc: value,
			extensions: [
				basicSetup,
				markdown(),
				oneDark,
				EditorView.lineWrapping,
				EditorView.contentAttributes.of({ 'aria-label': 'Texto da nota em Markdown' }),
				EditorView.theme({
					'&': { height: '100%', fontSize: '16px' },
					'.cm-scroller': {
						fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
						paddingBottom: 'env(safe-area-inset-bottom)'
					}
				}),
				EditorView.updateListener.of((update) => {
					if (update.docChanged) value = update.state.doc.toString();
				})
			]
		});
		return () => view.destroy();
	});
</script>

<div bind:this={host} class="h-full min-h-0"></div>
