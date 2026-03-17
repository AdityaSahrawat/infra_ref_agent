<script lang="ts">
	import type { Action } from '$lib/types';

	let { data } = $props<{ data: { actions: Action[]; error: string | null } }>();

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

<h2>Actions</h2>

{#if data.error}
	<div class="error">Failed to load actions: {data.error}</div>
{/if}

{#if execError}
	<div class="error">{execError}</div>
{/if}

{#if data.actions.length === 0}
	<p class="muted">No actions yet.</p>
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

<style>
	.muted {
		color: #666;
	}
	.error {
		color: #b00020;
		margin: 0.5rem 0;
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
</style>
