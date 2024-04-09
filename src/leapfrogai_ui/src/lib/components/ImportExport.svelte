<script lang="ts">
	import { Download, Export } from 'carbon-icons-svelte';
	import { Button } from 'carbon-components-svelte';
	import LFFileUploader from '$components/LFFileUploader.svelte';
	import { conversationsStore } from '$stores';

	export let rail = false;

	const onUpload = (files: FileList) => {
		console.log(files);
	};

	const onExport = () => {
		const dataStr =
			'data:text/json; charset=utf-8,' +
			encodeURIComponent(JSON.stringify($conversationsStore.conversations));
		const downloadAnchorNode = document.createElement('a');


		downloadAnchorNode.setAttribute('href', dataStr);
		downloadAnchorNode.setAttribute('download', 'conversations.json');
		document.body.appendChild(downloadAnchorNode);
		downloadAnchorNode.click();
		downloadAnchorNode.remove();

	};
</script>

<!--TODO - can we change system upload modal button to say import?-->
<div class="import-export-btns-container">
	{#if rail}
		<Button kind="ghost" icon={Download} iconDescription="Import conversations" />
		<Button kind="ghost" icon={Export} />
	{:else}
		<LFFileUploader
			accept={['application/json']}
			icon={Download}
			labelText="Import data"
			{onUpload}
		/>
		<Button
			id="export-btn"
			kind="ghost"
			icon={Export}
			iconDescription="Export conversations"
			on:click={onExport}>Export data</Button
		>
	{/if}
</div>

<style lang="scss">
	.import-export-btns-container {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		:global(.bx--btn) {
			width: 100%;
			color: themes.$text-secondary;
			font-weight: bold;
		}
	}
</style>
