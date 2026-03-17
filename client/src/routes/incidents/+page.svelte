<script lang="ts">
	import type { Incident } from '$lib/types';

	let { data } = $props<{ data: { incidents: Incident[]; error: string | null } }>();

	let creating = $state(false);
	let createError = $state<string | null>(null);

	function toIso(d: Date) {
		return d.toISOString();
	}

	function sampleIncident(severity: 'critical' | 'warning' = 'critical') {
		const now = new Date();
		return {
			alert_name: 'HighCPUUsage',
			severity,
			instance: 'prod-server-01',
			status: 'firing',
			started_at: toIso(new Date(now.getTime() - 5 * 60 * 1000)),
			received_at: toIso(now),
			raw_alert: {
				labels: { alertname: 'HighCPUUsage', instance: 'prod-server-01', job: 'node-exporter' },
				annotations: {
					summary: 'CPU usage > 90% for 5m',
					description: 'Instance prod-server-01 CPU at 95%'
				}
			}
		};
	}

	async function createSample(severity: 'critical' | 'warning') {
		creating = true;
		createError = null;
		try {
			const res = await fetch('/api/incidents', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify(sampleIncident(severity))
			});
			if (!res.ok) {
				createError = await res.text();
				return;
			}
			// reload the page data
			location.reload();
		} finally {
			creating = false;
		}
	}

	function fmt(s?: string | null) {
		if (!s) return '';
		try {
			return new Date(s).toLocaleString();
		} catch {
			return s;
		}
	}
</script>

<h2>Incidents</h2>

{#if data.error}
	<div class="error">Failed to load incidents: {data.error}</div>
{/if}

<div class="toolbar">
	<button disabled={creating} onclick={() => createSample('critical')}>Create sample critical incident</button>
	<button class="secondary" disabled={creating} onclick={() => createSample('warning')}>Create sample warning incident</button>
	{#if createError}
		<div class="error">{createError}</div>
	{/if}
</div>

{#if data.incidents.length === 0}
	<p class="muted">No incidents yet.</p>
{:else}
	<table>
		<thead>
			<tr>
				<th>Alert</th>
				<th>Severity</th>
				<th>Instance</th>
				<th>Status</th>
				<th>Started</th>
				<th>LLM</th>
			</tr>
		</thead>
		<tbody>
			{#each data.incidents as i}
				<tr>
					<td><a href={`/incidents/${i.id}`}>{i.alert_name}</a></td>
					<td><span class={`pill ${i.severity}`}>{i.severity}</span></td>
					<td>{i.instance}</td>
					<td>{i.status}</td>
					<td>{fmt(i.started_at)}</td>
					<td>
						{#if i.llm_confidence !== undefined && i.llm_confidence !== null}
							{Math.round(i.llm_confidence * 100)}%
						{:else}
							—
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<style>
	.toolbar {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		flex-wrap: wrap;
		margin: 1rem 0;
	}
	button {
		background: #111;
		color: white;
		border: none;
		border-radius: 8px;
		padding: 0.5rem 0.8rem;
		font-weight: 600;
		cursor: pointer;
	}
	button.secondary {
		background: #f5f5f5;
		color: #111;
	}
	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.error {
		color: #b00020;
		font-size: 0.95rem;
	}
	.muted {
		color: #666;
	}
	table {
		width: 100%;
		border-collapse: collapse;
	}
	th,
	td {
		border-bottom: 1px solid #e5e5e5;
		padding: 0.6rem 0.4rem;
		text-align: left;
		vertical-align: top;
	}
	a {
		color: #111;
	}
	.pill {
		display: inline-block;
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		background: #f5f5f5;
	}
	.pill.critical {
		background: #ffe8e8;
	}
	.pill.warning {
		background: #fff6dc;
	}
</style>
