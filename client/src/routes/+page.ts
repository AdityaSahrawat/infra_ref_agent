import type { PageLoad } from './$types';
import type { Incident, Action } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
	const [incidentsRes, actionsRes] = await Promise.all([
		fetch('/api/incidents'),
		fetch('/api/actions')
	]);

	let incidents: Incident[] = [];
	let actions: Action[] = [];
	let incidentsError: string | null = null;
	let actionsError: string | null = null;

	if (!incidentsRes.ok) {
		incidentsError = await incidentsRes.text();
	} else {
		incidents = await incidentsRes.json();
	}

	if (!actionsRes.ok) {
		actionsError = await actionsRes.text();
	} else {
		actions = await actionsRes.json();
	}

	return {
		incidents,
		actions,
		incidentsError,
		actionsError
	};
};
