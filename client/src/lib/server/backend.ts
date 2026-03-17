import type { RequestEvent } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

function getBackendBaseUrl(): string {
	return env.BACKEND_URL || 'http://127.0.0.1:8000';
}

function joinUrl(base: string, path: string): string {
	const baseTrimmed = base.replace(/\/+$/, '');
	const pathTrimmed = path.startsWith('/') ? path : `/${path}`;
	return `${baseTrimmed}${pathTrimmed}`;
}

export async function proxyToBackend(event: RequestEvent, backendPathWithQuery: string): Promise<Response> {
	const backendUrl = joinUrl(getBackendBaseUrl(), backendPathWithQuery);

	const method = event.request.method;
	const isBodyAllowed = method !== 'GET' && method !== 'HEAD';
	const body = isBodyAllowed ? await event.request.text() : undefined;

	const upstream = await fetch(backendUrl, {
		method,
		headers: {
			// forward content-type; avoid forwarding host/origin
			'content-type': event.request.headers.get('content-type') ?? 'application/json'
		},
		body
	});

	return new Response(await upstream.text(), {
		status: upstream.status,
		headers: {
			'content-type': upstream.headers.get('content-type') ?? 'application/json'
		}
	});
}
