import type { PageLoad } from './$types';
import type { Action } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch('/api/actions');
	if (!res.ok) {
		return { actions: [] as Action[], error: await res.text() };
	}
	const actions = (await res.json()) as Action[];
	return { actions, error: null };
};
