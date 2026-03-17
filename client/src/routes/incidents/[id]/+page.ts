import type { PageLoad } from './$types';
import type { Action, Incident } from '$lib/types';

export const load: PageLoad = async ({ fetch, params }) => {
	const [incidentRes, actionsRes] = await Promise.all([
		fetch(`/api/incidents/${params.id}`),
		fetch(`/api/actions?incident_id=${encodeURIComponent(params.id)}`)
	]);

	const incidentText = await incidentRes.text();
	const actionsText = await actionsRes.text();

	return {
		incident: incidentRes.ok ? (JSON.parse(incidentText) as Incident) : null,
		actions: actionsRes.ok ? (JSON.parse(actionsText) as Action[]) : [],
		error: incidentRes.ok ? null : incidentText
	};
};
