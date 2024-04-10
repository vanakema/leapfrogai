import { type Readable, readable } from 'svelte/store';
import type { Navigation, Page } from '@sveltejs/kit';
import { fakeConversations } from '../../testUtils/fakeData';
import { faker } from '@faker-js/faker';
import {vi} from "vitest";
import stores from "$app/stores";

type GetStoresOverrides = {
	url: string;
	params: Record<string, string>;
};
export const getStores = (
	options: GetStoresOverrides = { url: 'http://localhost', params: {} }
) => {
	const navigating = readable<Navigation | null>(null);
	const page = readable<Page>({
		url: new URL(options.url),
		params: options.params,
		route: { id: null },
		status: 200,
		error: null,
		// TODO - the profile and session types are incompletely mocked out
		data: {
			conversations: fakeConversations,
			profile: {},
			session: { user: { id: faker.string.uuid() } }
		},
		state: {},
		form: null
	});
	const updated: Readable<boolean> & { check(): Promise<boolean> } = {
		subscribe: readable(false).subscribe,
		check: () => Promise.resolve(false)
	};

	return { navigating, page, updated };
};

export const mockAppStore = ({
								 activeConversationId,
							 }: {
	activeConversationId: string;
}) =>
	vi.mock('$app/stores', (): typeof stores => {
		const page: typeof stores.page = {
			subscribe(fn) {
				return getStores({
					url: `http://localhost/chat/${fakeConversations[0].id}`,
					params: { conversation_id: activeConversationId }
				}).page.subscribe(fn);
			}
		};
		const navigating: typeof stores.navigating = {
			subscribe(fn) {
				return getStores().navigating.subscribe(fn);
			}
		};
		const updated: typeof stores.updated = {
			subscribe(fn) {
				return getStores().updated.subscribe(fn);
			},
			check: () => Promise.resolve(false)
		};

		return {
			getStores,
			navigating,
			page,
			updated
		};
	});
