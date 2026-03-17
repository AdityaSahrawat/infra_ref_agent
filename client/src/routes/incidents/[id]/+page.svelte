<script lang="ts">
	import type { Action, Incident } from '$lib/types';

	let { data } = $props<{
		data: { incident: Incident | null; actions: Action[]; error: string | null };
	}>();

	let executing = $state<string | null>(null);
	let execError = $state<string | null>(null);

	function fmt(s?: string | null) {
		if (!s) return '—';
		try {
			return new Date(s).toLocaleString();
		} catch {
			return s;
		}
	}

	async function executeAction(actionId: string) {
		executing = actionId;
		execError = null;
		try {
			const res = await fetch(`/api/actions/${actionId}`, { method: 'PATCH' });
			if (!res.ok) {
				execError = await res.text();
				return;
			}
			location.reload();
		} finally {
			executing = null;
		}
	}
</script>

{#if data.error}
	<div class="error">Failed to load incident: {data.error}</div>
{:else if !data.incident}
	<p class="muted">Incident not found.</p>
{:else}
	<h2>Incident</h2>
	<div class="card">
		<div class="row"><span class="k">ID</span><span class="v">{data.incident.id}</span></div>
		<div class="row"><span class="k">Alert</span><span class="v">{data.incident.alert_name}</span></div>
		<div class="row"><span class="k">Severity</span><span class={`v pill ${data.incident.severity}`}>{data.incident.severity}</span></div>
		<div class="row"><span class="k">Instance</span><span class="v">{data.incident.instance}</span></div>
		<div class="row"><span class="k">Status</span><span class="v">{data.incident.status}</span></div>
		<div class="row"><span class="k">Started</span><span class="v">{fmt(data.incident.started_at)}</span></div>
		<div class="row"><span class="k">Received</span><span class="v">{fmt(data.incident.received_at)}</span></div>
		<div class="row"><span class="k">Ended</span><span class="v">{fmt(data.incident.ended_at)}</span></div>
	</div>

	<h3>LLM Analysis</h3>
	<div class="card">
		<div class="row"><span class="k">Root cause</span><span class="v">{data.incident.root_cause ?? '—'}</span></div>
		<div class="row"><span class="k">Recommended action</span><span class="v">{data.incident.recommended_action ?? '—'}</span></div>
		<div class="row">
			<span class="k">Confidence</span>
			<span class="v">
				{#if data.incident.llm_confidence !== undefined && data.incident.llm_confidence !== null}
					{Math.round(data.incident.llm_confidence * 100)}%
				{:else}
					—
				{/if}
			</span>
		</div>
	</div>

	<h3>Actions</h3>
	{#if execError}
		<div class="error">{execError}</div>
	{/if}
	{#if data.actions.length === 0}
		<p class="muted">No actions for this incident yet. Create a critical incident with high confidence to auto-create one.</p>
	{:else}
		<table>
			<thead>
				<tr>
					<th>Type</th>
					<th>Status</th>
					<th>Executed</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				{#each data.actions as a}
					<tr>
						<td>{a.action_type}</td>
						<td>{a.status}</td>
						<td>{fmt(a.executed_at ?? null)}</td>
						<td>
							{#if a.status !== 'executed'}
								<button disabled={executing === a.id} onclick={() => executeAction(a.id)}>
									Execute
								</button>
							{:else}
								—
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
{/if}

<style>
	.card {
		border: 1px solid #e5e5e5;
		border-radius: 10px;
		padding: 0.8rem;
		margin: 0.75rem 0 1rem;
		background: #fff;
	}
	.row {
		display: grid;
		grid-template-columns: 160px 1fr;
		gap: 0.75rem;
		padding: 0.25rem 0;
	}
	.k {
		color: #666;
		font-size: 0.95rem;
	}
	.v {
		word-break: break-word;
	}
	.muted {
		color: #666;
	}
	.error {
		color: #b00020;
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
	button {
		background: #111;
		color: white;
		border: none;
		border-radius: 8px;
		padding: 0.45rem 0.7rem;
		font-weight: 600;
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.pill {
		display: inline-block;
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		background: #f5f5f5;
		width: fit-content;
	}
	.pill.critical {
		background: #ffe8e8;
	}
	.pill.warning {
		background: #fff6dc;
	}
</style>
