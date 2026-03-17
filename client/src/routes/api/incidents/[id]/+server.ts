import type { RequestHandler } from './$types';
import { proxyToBackend } from '$lib/server/backend';

export const GET: RequestHandler = async (event) => {
	return proxyToBackend(event, `/incident/${event.params.id}`);
};

export const PATCH: RequestHandler = async (event) => {
	return proxyToBackend(event, `/incident/${event.params.id}`);
};
