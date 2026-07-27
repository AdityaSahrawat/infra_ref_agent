import type { RequestHandler } from './$types';
import { proxyToBackend } from '$lib/server/backend';

export const POST: RequestHandler = async (event) => {
	return proxyToBackend(event, '/demo/scenarios');
};
