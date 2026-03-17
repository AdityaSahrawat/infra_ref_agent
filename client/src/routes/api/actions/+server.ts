import type { RequestHandler } from './$types';
import { proxyToBackend } from '$lib/server/backend';

export const GET: RequestHandler = async (event) => {
	return proxyToBackend(event, `/incident/actions${event.url.search}`);
};
