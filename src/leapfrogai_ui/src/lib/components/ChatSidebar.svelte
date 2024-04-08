<script lang="ts">
	import {
		Button,
		Modal,
		OverflowMenu,
		OverflowMenuItem,
		SideNav,
		SideNavDivider,
		SideNavItems,
		SideNavLink,
		SideNavMenu,
		SideNavMenuItem,
		TextInput
	} from 'carbon-components-svelte';
	import {
		AddComment,
		Download,
		Export,
		WatsonHealthTextAnnotationToggle
	} from 'carbon-icons-svelte';
	import { dates } from '$helpers';
	import { MAX_LABEL_SIZE } from '$lib/constants';
	import { conversationsStore, toastStore } from '$stores';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';

	export let isSideNavOpen: boolean;

	let deleteModalOpen = false;
	let editConversationId: string | null = null;
	let editLabelText: string | undefined = undefined;
	let inputDisabled = false;
	let disableScroll = false;
	let editMode = false;

	$: editMode =
		!!$page.params.conversation_id && editConversationId === $page.params.conversation_id;

	let sideNavIsHovered = false;

	$: activeConversation = $conversationsStore.conversations.find(
		(conversation) => conversation.id === $page.params.conversation_id
	);

	$: organizedConversations = dates.organizeConversationsByDate($conversationsStore.conversations);

	$: dateCategories = Array.from(
		new Set([
			'Today',
			'Yesterday',
			'This Month',
			...dates.sortMonthsReverse(
				Object.keys(organizedConversations).filter((item) => item !== 'Old')
			),
			'Old'
		])
	);

	const resetEditMode = () => {
		disableScroll = false;
		editConversationId = null;
		editLabelText = undefined;
		inputDisabled = false;
	};

	const saveNewLabel = async () => {
		if (editConversationId && editLabelText) {
			inputDisabled = true;
			const response = await fetch('/api/conversations/update/label', {
				method: 'PUT',
				body: JSON.stringify({ id: editConversationId, label: editLabelText }),
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (response.ok) {
				conversationsStore.updateConversationLabel(editConversationId, editLabelText);
			} else {
				toastStore.addToast({
					kind: 'error',
					title: 'Error',
					subtitle: 'Error updating label'
				});
			}
			resetEditMode();
		}
	};

	const handleEdit = async (e: KeyboardEvent | FocusEvent) => {
		if (e.type === 'blur') {
			await saveNewLabel();
		}
		if (e.type === 'keydown') {
			const keyboardEvent = e as KeyboardEvent;
			if (keyboardEvent.key === 'Escape') {
				resetEditMode();
				return;
			}

			if (keyboardEvent.key === 'Enter' || keyboardEvent.key === 'Tab') {
				await saveNewLabel();
			}
		}
	};

	const handleDelete = async () => {
		if (activeConversation?.id) {
			// A constraint on messages table will cascade delete all messages when the conversation is deleted
			const res = await fetch('/api/conversations/delete', {
				method: 'DELETE',
				body: JSON.stringify({ conversationId: activeConversation.id }),
				headers: {
					'Content-Type': 'application/json'
				}
			});
			if (res.ok) {
				conversationsStore.deleteConversation(activeConversation.id);
			} else {
				toastStore.addToast({
					kind: 'error',
					title: 'Error',
					subtitle: 'Error deleting conversation'
				});
			}
		}

		deleteModalOpen = false;
	};

	const handleMouseEnter = () => {
		sideNavIsHovered = true;
	};
	const handleMouseExit = () => {
		sideNavIsHovered = false;
	};

	let activeConversationRef: HTMLElement | null;
	let scrollBoxRef: HTMLElement;
	let overflowMenuButtonRef: HTMLButtonElement;

	const handleActiveConversationChange = (id: string) => {
		conversationsStore.changeConversation(id);
		activeConversationRef = document.getElementById(`side-nav-menu-item-${id}`);
	};

	let overflowMenuOpen = false;
	let menuOffset = 0;
	let scrollOffset = 0;
	$: if (browser && activeConversationRef) {
		menuOffset = activeConversationRef?.offsetTop;
		scrollOffset = scrollBoxRef.scrollTop;
	}

	// TODO - edit is highlighted on click, normal?
</script>

<SideNav
	aria-label="side navigation"
	bind:isOpen={isSideNavOpen}
	style="background-color: g90;"
	rail={!isSideNavOpen}
>
	<div on:mouseenter={handleMouseEnter} on:mouseleave={handleMouseExit} style="height: 100%">
		{#if (!isSideNavOpen && sideNavIsHovered) || isSideNavOpen}
			<SideNavItems>
				<div class="side-nav-items-container">
					<div class="new-chat-container">
						<Button
							kind="secondary"
							size="small"
							icon={AddComment}
							class="new-chat-btn"
							id="new-chat-btn"
							on:click={() => handleActiveConversationChange('')}>New</Button
						>
						<TextInput light size="sm" placeholder="Search..." />
						<SideNavDivider />
					</div>

					<div
						class:noScroll={disableScroll || editMode}
						bind:this={scrollBoxRef}
						class="conversations"
						data-testid="conversations"
					>
						{#each dateCategories as category}
							<SideNavMenu text={category} expanded data-testid="side-nav-menu">
								{#if organizedConversations[category]}
									{#each organizedConversations[category] as conversation}
										<SideNavMenuItem
											data-testid="side-nav-menu-item-{conversation.label}"
											id="side-nav-menu-item-{conversation.id}"
											isSelected={activeConversation?.id === conversation.id}
											on:click={() => handleActiveConversationChange(conversation.id)}
										>
											<div class="menu-content">
												{#if editMode && activeConversation?.id === conversation.id}
													<TextInput
														bind:value={editLabelText}
														size="sm"
														class="edit-conversation"
														on:keydown={(e) => handleEdit(e)}
														on:blur={(e) => {
															handleEdit(e);
														}}
														autofocus
														maxlength={MAX_LABEL_SIZE}
														readonly={inputDisabled}
														aria-label="edit conversation"
													/>
												{:else}
													<div data-testid="conversation-label-{conversation.id}" class="menu-text">
														{conversation.label}
													</div>
													<div>
														<OverflowMenu
															id={`overflow-menu-${conversation.id}`}
															bind:buttonRef={overflowMenuButtonRef}
															on:close={() => {
																overflowMenuOpen = false;
																disableScroll = false;
															}}
															on:click={(e) => {
																e.stopPropagation();
																overflowMenuOpen = true;
																handleActiveConversationChange(conversation.id);
																disableScroll = true;
															}}
															data-testid="overflow-menu-{conversation.label}"
															style={overflowMenuOpen && activeConversation?.id === conversation.id
																? `position: fixed; top: 0; left: 0; transform: translate(224px, ${menuOffset - scrollOffset + 48}px)`
																: ''}
														>
															<OverflowMenuItem
																text="Edit"
																on:click={() => {
																	disableScroll = true;
																	editConversationId = conversation.id;
																	editLabelText = conversation.label;
																}}
															/>
															<OverflowMenuItem
																text="Delete"
																on:click={() => (deleteModalOpen = true)}
																data-testid="overflow-menu-delete-{conversation.label}"
															/>
														</OverflowMenu>
													</div>
												{/if}
											</div>
										</SideNavMenuItem>
									{/each}
								{/if}
							</SideNavMenu>
						{/each}
					</div>
					<div>
						<SideNavDivider />
						<div class="bottom-side-nav-icons-container">
							<SideNavLink>Import Data<slot name="icon"><Download /></slot></SideNavLink>
							<SideNavLink>Export Data<slot name="icon"><Export /></slot></SideNavLink>
						</div>
					</div>
				</div>
			</SideNavItems>
		{:else}
			<SideNavItems>
				<div class="side-nav-items-container">
					<div>
						<Button icon={WatsonHealthTextAnnotationToggle} size="small" kind="secondary" />
					</div>

					<div>
						<SideNavDivider />
						<div class="bottom-side-nav-icons-container-rail">
							<Download />
							<Export />
						</div>
					</div>
				</div>
			</SideNavItems>
		{/if}

		<Modal
			danger
			bind:open={deleteModalOpen}
			modalHeading="Delete Chat"
			primaryButtonText="Delete"
			secondaryButtonText="Cancel"
			on:click:button--secondary={() => (deleteModalOpen = false)}
			on:open
			on:close
			on:submit={handleDelete}
			>Are you sure you want to delete your <strong
				>{activeConversation?.label.substring(0, MAX_LABEL_SIZE)}</strong
			> chat?</Modal
		>
	</div>
</SideNav>

<!-- NOTE - Carbon Components Svelte does not yet support theming of the UI Shell components so several
properties had to be manually overridden.
https://github.com/carbon-design-system/carbon-components-svelte/issues/892
-->
<style lang="scss">
	.noScroll {
		overflow-y: hidden !important;
	}
	.side-nav-items-container {
		height: 100%;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding: 0 0 layout.$spacing-05 0;
		:global(.bx--side-nav__divider) {
			margin: layout.$spacing-03 0 0 0;
			background-color: themes.$border-subtle-01;
		}
	}

	.bottom-side-nav-icons-container-rail {
		display: flex;
		align-items: center;
		flex-direction: column;
		gap: layout.$spacing-05;
		padding: layout.$spacing-03 0;
	}

	.bottom-side-nav-icons-container {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding: layout.$spacing-03 0;
	}

	.new-chat-container {
		display: flex;
		flex-direction: column;
		gap: layout.$spacing-03;
		padding: layout.$spacing-05;
		:global(button.new-chat-btn) {
			width: 100%;
		}
	}

	.menu-content {
		width: 100% !important;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 208px;
		.menu-text {
			width: 192px;
			overflow: hidden;
			text-overflow: ellipsis;
			color: themes.$text-secondary;
		}

		:global(.bx--overflow-menu) {
			width: 16px;
			height: 32px;
			z-index: 1;
		}
	}

	// The following overflow: visible !important overrides allow the OverflowMenu component
	// to display correctly. There may be a better way to do this, but just realize you have
	// to override things at several levels to get results.
	// The !important is necessary for the changes to work in production builds.
	.conversations {
		flex-grow: 1;
		scrollbar-width: none;
		overflow-y: auto;
	}

	:global(.bx--overflow-menu-options) {
		left: 20px !important;
	}

	:global(.bx--side-nav__navigation) {
		overflow: visible !important;
		:global(.bx--side-nav__item) {
			overflow: visible !important;
		}
	}

	:global(.bx--side-nav__link) {
		&:hover {
			background-color: #4d4d4d !important;
		}
	}

	:global(.bx--side-nav__link[aria-current='page']) {
		background-color: #4d4d4d !important;
	}

	:global(.bx--side-nav__link-text) {
		position: relative;
		display: flex;
		flex-grow: 1;
		justify-content: space-between;
		text-align: left;
		overflow: visible !important;
		color: themes.$text-secondary !important;
	}

	:global(.bx--side-nav__navigation) {
		background-color: themes.$layer-01 !important;
		list-style: none;
		height: calc(100vh - var(--header-height)) !important;
		color: themes.$text-secondary !important;
	}

	// Override default behavior of fly out when using rail sidenav
	// Use this instead if you don't want the rail to stay skinny on hover and not expand
	// remove on:mousenter and on:mouseexit code
	//:global(.bx--side-nav--rail) {
	//	&:hover {
	//		width: 3rem !important;
	//	}
	//}
	//
	:global(.bx--side-nav__items) {
		text-align: center;
		overflow: visible !important;
		height: 100%;
	}

	:global(.bx--side-nav__submenu) {
		color: themes.$text-secondary !important;
		:global(svg) {
			stroke: themes.$text-secondary;
		}
		&:hover {
			background-color: #4d4d4d !important;
		}
	}

	.label-edit-mode {
		:global(.bx--side-nav__link) {
			padding: 0 layout.$spacing-05 0 layout.$spacing-07;
		}
		:global(.bx--side-nav__link[aria-current='page']) {
			background-color: themes.$layer-01 !important;
		}
		:global(input) {
			height: 1.5rem;
		}
		:global(.bx--text-input) {
			border-bottom: none;
		}
	}
</style>
