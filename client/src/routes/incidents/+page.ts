import type { PageLoad } from './$types';
import type { Incident } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch('/api/incidents');
	if (!res.ok) {
		return { incidents: [] as Incident[], error: await res.text() };
	}
	const incidents = (await res.json()) as Incident[];
	return { incidents, error: null };
};
