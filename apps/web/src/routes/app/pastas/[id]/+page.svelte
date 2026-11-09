<script lang="ts">
	import { page } from '$app/state';
	import DocumentGrid from '$lib/components/DocumentGrid.svelte';
</script>

{#key page.params.id}
	<DocumentGrid folderId={page.params.id ?? null} />
{/key}
