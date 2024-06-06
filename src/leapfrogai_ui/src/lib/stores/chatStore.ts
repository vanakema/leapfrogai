import { writable } from 'svelte/store';
import { type Message as AIMessage } from 'ai/svelte';
import { sortMessages } from '$helpers/chatHelpers';
import type { LFMessage } from '$lib/types/messages';

type ChatStore = {
  allStreamedMessages: Array<LFMessage>;
};

const defaultValues: ChatStore = {
  allStreamedMessages: []
};

const createChatStore = () => {
  const { subscribe, set, update } = writable<ChatStore>({ ...defaultValues });
  return {
    subscribe,
    set,
    update,
    setAllStreamedMessages: (newMessages: AIMessage[]) => {
      update((old) => ({ ...old, allStreamedMessages: sortMessages(newMessages) }));
    }
  };
};

export default createChatStore();
