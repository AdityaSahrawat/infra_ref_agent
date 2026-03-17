import type { RequestHandler } from './$types';
import { proxyToBackend } from '$lib/server/backend';

export const GET: RequestHandler = async (event) => {
	return proxyToBackend(event, `/incident/actions/${event.params.id}`);
};

export const PATCH: RequestHandler = async (event) => {
	return proxyToBackend(event, `/incident/actions/${event.params.id}`);
};
