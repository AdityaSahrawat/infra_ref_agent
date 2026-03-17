import type { RequestHandler } from './$types';
import { proxyToBackend } from '$lib/server/backend';

export const POST: RequestHandler = async (event) => {
	return proxyToBackend(event, `/incident/${event.params.id}/actions`);
};
