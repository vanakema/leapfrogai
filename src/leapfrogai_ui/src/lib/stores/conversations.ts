import { writable } from 'svelte/store';
import { MAX_LABEL_SIZE } from '$lib/constants';
import { goto } from '$app/navigation';
import { error } from '@sveltejs/kit';
import { toastStore } from '$stores/index';

type ConversationsStore = {
	conversations: Conversation[];
};

const defaultValues: ConversationsStore = {
	conversations: []
};

const createConversation = async (input: NewConversationInput) => {
	const newConversationInput = {
		...input,
		label: input.label.substring(0, MAX_LABEL_SIZE)
	};
	const res = await fetch('/api/conversations/new', {
		method: 'POST',
		body: JSON.stringify(newConversationInput),
		headers: {
			'Content-Type': 'application/json'
		}
	});
	if (!res.ok) return res.json();

	return error(500, 'Error creating conversation');
};

const createMessage = async (input: NewMessageInput) => {
	const res = await fetch('/api/messages/new', {
		method: 'POST',
		body: JSON.stringify({
			...input
		}),
		headers: {
			'Content-Type': 'application/json'
		}
	});
	if (res.ok) return res.json();
	return error(500, 'Error saving message');
};

// TODO - test error handling
const createConversationsStore = () => {
	const { subscribe, set, update } = writable<ConversationsStore>({ ...defaultValues });
	return {
		subscribe,
		set,
		update,
		setConversations: (conversations: Conversation[]) => {
			update((old) => ({ ...old, conversations }));
		},
		changeConversation: async (newId: string | null) => {
			await goto(`/chat/${newId}`);
		},
		newConversation: async (label: string) => {
			try {
				const newConversation = await createConversation({
					label: label.substring(0, MAX_LABEL_SIZE)
				});
				if (newConversation) {
					newConversation.messages = [];
					update((old) => {
						return {
							...old,
							conversations: [...old.conversations, newConversation]
						};
					});
					await goto(`/chat/${newConversation.id}`);
				}
			} catch {
				toastStore.addToast({
					kind: 'error',
					title: 'Error',
					subtitle: `Error saving conversation.`
				});
			}
		},

		newMessage: async (message: NewMessageInput) => {
			try {
				const newMessage = await createMessage(message);
				if (newMessage) {
					update((old) => {
						const updatedConversations = [...old.conversations];
						const conversationIndex = old.conversations.findIndex(
							(c) => c.id === newMessage.conversation_id
						);
						const oldConversation = old.conversations[conversationIndex];

						updatedConversations[conversationIndex] = {
							...oldConversation,
							messages: [...oldConversation.messages, newMessage]
						};
						return {
							...old,
							conversations: updatedConversations
						};
					});
				}
			} catch {
				toastStore.addToast({
					kind: 'error',
					title: 'Error',
					subtitle: `Error creating message.`
				});
			}
		},
		// TODO - the api call in chatsidebar should be moved to here in the store, then error handle following pattern
		deleteConversation: async (id: string) => {
			update((old) => ({
				...old,
				conversations: old.conversations.filter((c) => c.id !== id)
			}));
			await goto('/chat');
		},
		// TODO - the api call in chatsidebar should be moved to here in the store, then error handle following pattern
		updateConversationLabel: (id: string, newLabel: string) =>
			update((old) => {
				const updatedConversationIndex = old.conversations.findIndex((c) => c.id === id);
				const updatedConversation = { ...old.conversations[updatedConversationIndex] };
				updatedConversation.label = newLabel;

				const updatedConversations = [...old.conversations];
				updatedConversations[updatedConversationIndex] = updatedConversation;

				return {
					...old,
					conversations: updatedConversations
				};
			}),
		importConversations: async (data: Conversation[]) => {
			const newConversations: Conversation[] = [];
			for (const conversation of data) {
				try {
					const createdConversation = await createConversation({
						id: conversation.id,
						label: conversation.label,
						inserted_at: conversation.inserted_at
					});
					createdConversation.messages = [];

					const { messages } = conversation;
					for (const message of messages) {
						const createdMessage = await createMessage({
							id: message.id,
							role: message.role,
							content: message.content,
							conversation_id: createdConversation.id,
							inserted_at: message.inserted_at
						});
						createdConversation.messages.push(createdMessage);
					}
					newConversations.push({ ...conversation });
				} catch (e) {
					toastStore.addToast({
						kind: 'error',
						title: 'Error',
						subtitle: `Error importing conversation: ${conversation.label}`
					});
				}
			}

			update((old) => {
				// TODO - should the UI overwrite old conversations with the new versions, or skip those? (handle here)
				return {
					...old,
					conversations: [...old.conversations, ...newConversations]
				};
			});
		}
	};
};

export default createConversationsStore();
