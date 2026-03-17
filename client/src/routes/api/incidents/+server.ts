import type { RequestHandler } from './$types';
import { proxyToBackend } from '$lib/server/backend';

export const GET: RequestHandler = async (event) => {
	return proxyToBackend(event, '/incident/');
};

export const POST: RequestHandler = async (event) => {
	return proxyToBackend(event, '/incident/');
};
