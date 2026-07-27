<script lang="ts">
	import type { Incident, Action } from '$lib/types';

	let { data } = $props<{
		data: {
			incidents: Incident[];
			actions: Action[];
			incidentsError: string | null;
			actionsError: string | null;
		};
	}>();

	let creating = $state(false);
	let createError = $state<string | null>(null);
	let processingMessage = $state<string | null>(null);

	let executing = $state<string | null>(null);
	let execError = $state<string | null>(null);

	let expandedIncidents = $state<Record<string, boolean>>({});
	let expandedActions = $state<Record<string, boolean>>({});

	function toggleIncident(id: string) {
		expandedIncidents[id] = !expandedIncidents[id];
	}

	function toggleAction(id: string) {
		expandedActions[id] = !expandedActions[id];
	}

	function toIso(d: Date) {
		return d.toISOString();
	}

	function sampleAlert(severity: 'critical' | 'warning' = 'critical') {
		const now = new Date();
		return {
			status: 'firing',
			labels: {
				alertname: 'HighCPUUsage',
				severity,
				instance: 'prod-server-01',
				service: 'api',
				job: 'node-exporter'
			},
			annotations: {
				summary: 'CPU usage > 90% for 5m',
				description: 'Instance prod-server-01 CPU at 95%'
			},
			startsAt: toIso(new Date(now.getTime() - 5 * 60 * 1000)),
			endsAt: null,
			generatorURL: 'http://localhost:9090/graph'
		};
	}

	function parseDate(s?: string | null): Date {
		if (!s) return new Date(NaN);
		const normalized = s.endsWith('Z') || s.includes('+') ? s : s + 'Z';
		return new Date(normalized);
	}

	function sleep(milliseconds: number) {
		return new Promise((resolve) => setTimeout(resolve, milliseconds));
	}

	async function waitForProcessedAlert(startedAt: string) {
		const expectedStart = parseDate(startedAt).getTime();

		for (let attempt = 0; attempt < 30; attempt += 1) {
			await sleep(1000);
			const response = await fetch('/api/incidents');
			if (!response.ok) continue;

			const incidents = (await response.json()) as Incident[];
			const processed = incidents.some((incident) => {
				const actualStart = parseDate(incident.started_at).getTime();
				return (
					incident.alert_name === 'HighCPUUsage' &&
					incident.service === 'api' &&
					Math.abs(actualStart - expectedStart) < 2000 &&
					incident.llm_confidence !== undefined &&
					incident.llm_confidence !== null
				);
			});

			if (processed) {
				location.reload();
				return;
			}
		}

		processingMessage = 'The alert is still processing. Refresh this page shortly.';
	}

	async function sendSampleAlert(severity: 'critical' | 'warning') {
		creating = true;
		createError = null;
		processingMessage = null;
		const alert = sampleAlert(severity);
		try {
			const res = await fetch('/api/alerts', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify(alert)
			});
			if (!res.ok) {
				createError = await res.text();
				return;
			}

			processingMessage = 'Alert accepted. Waiting for embedding and LLM analysis…';
			await waitForProcessedAlert(alert.startsAt);
		} catch (error) {
			createError = error instanceof Error ? error.message : 'Unable to send alert';
		} finally {
			creating = false;
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

	let runningDemo = $state(false);

	async function runDemoScenarios() {
		runningDemo = true;
		createError = null;
		processingMessage = 'Executing Kubernetes Demo Scenarios (Scaling, Self-Healing & Crash Remediation)...';
		try {
			const res = await fetch('/api/demo/scenarios', { method: 'POST' });
			if (!res.ok) {
				createError = await res.text();
				return;
			}
			await sleep(1000);
			location.reload();
		} catch (error) {
			createError = error instanceof Error ? error.message : 'Unable to run demo scenarios';
		} finally {
			runningDemo = false;
			processingMessage = null;
		}
	}

	function fmt(s?: string | null) {
		if (!s) return '—';
		try {
			const d = parseDate(s);
			return isNaN(d.getTime()) ? s : d.toLocaleString();
		} catch {
			return s;
		}
	}
</script>

<svelte:head>
	<title>Autonomous Infrastructure Maintainer - Dashboard</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</svelte:head>

<div class="dashboard">
	<!-- Top summary/simulator panel -->
	<header class="dashboard-header">
		<div class="header-info">
			<h1>System Overview</h1>
			<p class="subtitle">Real-time status of server incidents and automated mitigation actions.</p>
		</div>
		<div class="simulator-card">
			<h3>Alert Simulator</h3>
			<div class="simulator-buttons">
				<button class="btn btn-critical" disabled={creating || runningDemo} onclick={() => sendSampleAlert('critical')}>
					{creating ? 'Sending...' : 'Trigger Critical Alert'}
				</button>
				<button class="btn btn-warning" disabled={creating || runningDemo} onclick={() => sendSampleAlert('warning')}>
					{creating ? 'Sending...' : 'Trigger Warning Alert'}
				</button>
				<button class="btn btn-demo" disabled={creating || runningDemo} onclick={runDemoScenarios}>
					{runningDemo ? 'Running...' : '⚡ Run K8s Demos'}
				</button>
			</div>
			{#if createError}
				<div class="error-toast">{createError}</div>
			{/if}
			{#if processingMessage}
				<div class="processing-toast">
					<div class="spinner"></div>
					{processingMessage}
				</div>
			{/if}
		</div>
	</header>

	<!-- Main grid of Incidents & Actions -->
	<div class="dashboard-grid">
		<!-- Left: Incidents -->
		<section class="panel incidents-panel">
			<div class="panel-header">
				<h2>Incidents</h2>
				<span class="count-badge">{data.incidents.length}</span>
			</div>
			
			{#if data.incidentsError}
				<div class="error-toast">Failed to load incidents: {data.incidentsError}</div>
			{/if}

			{#if data.incidents.length === 0}
				<div class="empty-state">
					<p>No active incidents.</p>
					<span>All systems are healthy.</span>
				</div>
			{:else}
				<div class="table-container">
					<table>
						<thead>
							<tr>
								<th class="chevron-col"></th>
								<th>Alert</th>
								<th>Severity</th>
								<th>Service</th>
								<th>Instance</th>
								<th>Status</th>
								<th>Started</th>
							</tr>
						</thead>
						<tbody>
							{#each data.incidents as i}
								{@const incidentActions = data.actions.filter((act: Action) => act.incident_id === i.id)}
								<tr class="clickable-row" class:active-row={expandedIncidents[i.id]} onclick={() => toggleIncident(i.id)}>
									<td class="chevron-col"><span class="chevron"></span></td>
									<td>
										<a class="incident-link" href={`/incidents/${i.id}`} onclick={(e) => e.stopPropagation()}>{i.alert_name}</a>
									</td>
									<td>
										<span class={`pill ${i.severity}`}>{i.severity}</span>
									</td>
									<td><code>{i.service}</code></td>
									<td><code>{i.instance}</code></td>
									<td>
										<span class={`status-dot ${i.status}`}></span> {i.status}
									</td>
									<td>{fmt(i.started_at)}</td>
								</tr>
								{#if expandedIncidents[i.id]}
									<tr class="detail-row expanded">
										<td colspan="7">
											<div class="detail-content">
												<div class="detail-grid">
													<div class="detail-section">
														<h4>LLM Diagnostics</h4>
														{#if i.root_cause || i.recommended_action}
															<div class="diagnostic-item">
																<span class="diagnostic-label">Possible Root Cause:</span>
																<p class="diagnostic-text">{i.root_cause || 'Analyzing...'}</p>
															</div>
															<div class="diagnostic-item">
																<span class="diagnostic-label">Recommended Action:</span>
																<p class="diagnostic-text">{i.recommended_action || 'None'}</p>
															</div>
															<div class="diagnostic-item">
																<span class="diagnostic-label">LLM Confidence:</span>
																<span class="confidence-badge">
																	{#if i.llm_confidence !== undefined && i.llm_confidence !== null}
																		{Math.round(i.llm_confidence * 100)}%
																	{:else}
																		—
																	{/if}
																</span>
															</div>
														{:else}
															<p class="muted">No LLM analysis available yet.</p>
														{/if}
													</div>

													<div class="detail-section">
														<h4>Incident Metadata</h4>
														<div class="metadata-grid">
															<span class="meta-label">ID:</span>
															<span class="meta-val"><code>{i.id}</code></span>
															
															<span class="meta-label">Received:</span>
															<span class="meta-val">{fmt(i.received_at)}</span>
															
															<span class="meta-label">Ended:</span>
															<span class="meta-val">{fmt(i.ended_at)}</span>
															
															<span class="meta-label">Embedding:</span>
															<span class="meta-val">{i.embedding ? `${i.embedding.length} dims` : 'None'}</span>
														</div>

														{#if i.metrics_summary}
															<div class="metrics-block">
																<h5>Metrics Snapshot</h5>
																<pre class="metrics-pre">{i.metrics_summary}</pre>
															</div>
														{/if}
													</div>
												</div>

												<!-- Associated actions for this incident -->
												<div class="associated-actions">
													<h4>Mitigation Actions</h4>
													{#if incidentActions.length === 0}
														<p class="muted">No mitigation actions associated with this incident.</p>
													{:else}
														<div class="sub-table-container">
															<table class="sub-table">
																<thead>
																	<tr>
																		<th>Type</th>
																		<th>Status</th>
																		<th>Executed At</th>
																		<th>Control</th>
																	</tr>
																</thead>
																<tbody>
																	{#each incidentActions as a}
																		<tr>
																			<td><strong>{a.action_type}</strong></td>
																			<td><span class={`pill status-${a.status}`}>{a.status}</span></td>
																			<td>{fmt(a.executed_at)}</td>
																			<td>
																				{#if a.status !== 'executed'}
																					<button class="btn-execute" disabled={executing === a.id} onclick={(e) => { e.stopPropagation(); executeAction(a.id); }}>
																						{executing === a.id ? 'Running...' : 'Execute'}
																					</button>
																				{:else}
																					<span class="check-mark">✓ Done</span>
																				{/if}
																			</td>
																		</tr>
																	{/each}
																</tbody>
															</table>
														</div>
													{/if}
												</div>
											</div>
										</td>
									</tr>
								{/if}
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</section>

		<!-- Right: Actions -->
		<section class="panel actions-panel">
			<div class="panel-header">
				<h2>Actions</h2>
				<span class="count-badge">{data.actions.length}</span>
			</div>

			{#if data.actionsError}
				<div class="error-toast">Failed to load actions: {data.actionsError}</div>
			{/if}
			{#if execError}
				<div class="error-toast">{execError}</div>
			{/if}

			{#if data.actions.length === 0}
				<div class="empty-state">
					<p>No actions run yet.</p>
					<span>Mitigation steps will appear here.</span>
				</div>
			{:else}
				<div class="table-container">
					<table>
						<thead>
							<tr>
								<th class="chevron-col"></th>
								<th>Type</th>
								<th>Status</th>
								<th>Time</th>
								<th>Control</th>
							</tr>
						</thead>
						<tbody>
							{#each data.actions as a}
								<tr class="clickable-row" class:active-row={expandedActions[a.id]} onclick={() => toggleAction(a.id)}>
									<td class="chevron-col"><span class="chevron"></span></td>
									<td class="action-type-cell">
										<strong>{a.action_type}</strong>
									</td>
									<td>
										<span class={`pill status-${a.status}`}>{a.status}</span>
									</td>
									<td>{fmt(a.executed_at ?? null)}</td>
									<td>
										{#if a.status !== 'executed'}
											<button class="btn-execute" disabled={executing === a.id} onclick={(e) => { e.stopPropagation(); executeAction(a.id); }}>
												{executing === a.id ? 'Running...' : 'Execute'}
											</button>
										{:else}
											<span class="check-mark">✓ Done</span>
										{/if}
									</td>
								</tr>
								{#if expandedActions[a.id]}
									<tr class="detail-row expanded">
										<td colspan="5">
											<div class="detail-content">
												<div class="detail-grid-actions">
													<div class="detail-section">
														<h4>Action Details</h4>
														<div class="metadata-grid">
															<span class="meta-label">Action ID:</span>
															<span class="meta-val"><code>{a.id}</code></span>

															<span class="meta-label">Incident ID:</span>
															<span class="meta-val">
																{#if a.incident_id}
																	<code>{a.incident_id}</code>
																{:else}
																	<em>Orphan action</em>
																{/if}
															</span>
														</div>
													</div>

													<div class="detail-section">
														<h4>Payload Parameters</h4>
														{#if a.action_payload && Object.keys(a.action_payload).length > 0}
															<div class="payload-list">
																{#each Object.entries(a.action_payload) as [key, val]}
																	<div class="payload-item">
																		<span class="payload-key">{key}:</span>
																		<code class="payload-val">{typeof val === 'object' ? JSON.stringify(val) : val}</code>
																	</div>
																{/each}
															</div>
														{:else}
															<p class="muted">No payload parameters.</p>
														{/if}
													</div>
												</div>

												{#if a.error_message}
													<div class="error-banner">
														<strong>Execution Error:</strong>
														<pre>{a.error_message}</pre>
													</div>
												{/if}
											</div>
										</td>
									</tr>
								{/if}
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</section>
	</div>
	
	<footer class="hint-footer">
		<p>
			If data doesn’t load, ensure the backend is running and set <code>BACKEND_URL</code> in <code>client/.env</code>.
		</p>
	</footer>
</div>

<style>
	:global(body) {
		background-color: #f8fafc !important;
		font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
	}

	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 2rem;
		padding: 0.5rem 0;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
		background: linear-gradient(135deg, #1e293b, #0f172a);
		color: #ffffff;
		padding: 2rem;
		border-radius: 16px;
		box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
	}

	@media (max-width: 900px) {
		.dashboard-header {
			flex-direction: column;
			align-items: stretch;
		}
	}

	.header-info {
		flex: 1;
	}

	.dashboard-header h1 {
		font-family: 'Outfit', sans-serif;
		font-size: 2.25rem;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(to right, #38bdf8, #818cf8);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.subtitle {
		margin-top: 0.5rem;
		color: #94a3b8;
		font-size: 1.05rem;
		line-height: 1.5;
	}

	.simulator-card {
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		padding: 1.25rem;
		border-radius: 12px;
		min-width: 320px;
		backdrop-filter: blur(8px);
	}

	.simulator-card h3 {
		font-family: 'Outfit', sans-serif;
		margin: 0 0 0.75rem 0;
		font-size: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #38bdf8;
	}

	.simulator-buttons {
		display: flex;
		gap: 0.75rem;
	}

	.btn {
		flex: 1;
		font-family: 'Plus Jakarta Sans', sans-serif;
		font-weight: 600;
		font-size: 0.875rem;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		border: none;
		cursor: pointer;
		transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.btn:hover {
		transform: translateY(-1px);
	}

	.btn:active {
		transform: translateY(0);
	}

	.btn-critical {
		background: #ef4444;
		color: white;
	}
	.btn-critical:hover {
		background: #dc2626;
		box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
	}

	.btn-warning {
		background: #f59e0b;
		color: white;
	}
	.btn-warning:hover {
		background: #d97706;
		box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
	}

	.btn-demo {
		background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
		color: white;
	}
	.btn-demo:hover {
		background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
		box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
	}

	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
		box-shadow: none;
	}

	.error-toast {
		background: #fef2f2;
		color: #991b1b;
		border: 1px solid #fee2e2;
		padding: 0.75rem;
		border-radius: 8px;
		margin-top: 0.75rem;
		font-size: 0.875rem;
	}

	.processing-toast {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #f0f9ff;
		color: #0284c7;
		border: 1px solid #e0f2fe;
		padding: 0.75rem;
		border-radius: 8px;
		margin-top: 0.75rem;
		font-size: 0.875rem;
	}

	.spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid #0284c7;
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.dashboard-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 2rem;
	}

	@media (min-width: 1024px) {
		.dashboard-grid {
			grid-template-columns: 1.1fr 0.9fr;
		}
	}

	.panel {
		background: #ffffff;
		border-radius: 16px;
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
		border: 1px solid #f1f5f9;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-bottom: 2px solid #f1f5f9;
		padding-bottom: 0.75rem;
	}

	.panel-header h2 {
		font-family: 'Outfit', sans-serif;
		font-size: 1.5rem;
		font-weight: 600;
		margin: 0;
		color: #1e293b;
	}

	.count-badge {
		background: #f1f5f9;
		color: #475569;
		font-size: 0.85rem;
		font-weight: 700;
		padding: 0.25rem 0.6rem;
		border-radius: 999px;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 4rem 2rem;
		text-align: center;
		background: #f8fafc;
		border: 2px dashed #e2e8f0;
		border-radius: 12px;
		color: #64748b;
	}

	.empty-state p {
		margin: 0 0 0.25rem 0;
		font-weight: 600;
		font-size: 1.05rem;
		color: #334155;
	}

	.empty-state span {
		font-size: 0.9rem;
	}

	.table-container {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		text-align: left;
	}

	th {
		font-size: 0.75rem;
		font-weight: 700;
		text-transform: uppercase;
		color: #64748b;
		padding: 0.75rem 0.5rem;
		border-bottom: 1px solid #e2e8f0;
		letter-spacing: 0.05em;
	}

	td {
		padding: 0.875rem 0.5rem;
		border-bottom: 1px solid #f1f5f9;
		color: #334155;
		font-size: 0.925rem;
		vertical-align: middle;
	}

	.clickable-row {
		cursor: pointer;
		transition: background-color 0.15s ease;
	}

	.clickable-row:hover {
		background-color: #f8fafc;
	}

	.incident-link {
		color: #1e293b;
		font-weight: 600;
		text-decoration: none;
		transition: color 0.15s ease;
	}

	.incident-link:hover {
		color: #3b82f6;
		text-decoration: underline;
	}

	code {
		background: #f1f5f9;
		color: #0f172a;
		padding: 0.15rem 0.35rem;
		border-radius: 4px;
		font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
		font-size: 0.85em;
	}

	.pill {
		display: inline-flex;
		align-items: center;
		padding: 0.25rem 0.6rem;
		border-radius: 999px;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.pill.critical {
		background: #fef2f2;
		color: #991b1b;
		border: 1px solid #fee2e2;
	}

	.pill.warning {
		background: #fffbeb;
		color: #92400e;
		border: 1px solid #fef3c7;
	}

	.pill.status-pending {
		background: #eff6ff;
		color: #1e40af;
		border: 1px solid #dbeafe;
	}

	.pill.status-executed {
		background: #ecfdf5;
		color: #065f46;
		border: 1px solid #d1fae5;
	}

	.status-dot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		margin-right: 0.35rem;
	}

	.status-dot.firing {
		background-color: #ef4444;
		box-shadow: 0 0 8px #ef4444;
		animation: pulse 2s infinite;
	}

	.status-dot.resolved {
		background-color: #10b981;
	}

	@keyframes pulse {
		0% {
			transform: scale(0.95);
			box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
		}
		70% {
			transform: scale(1);
			box-shadow: 0 0 0 6px rgba(239, 68, 68, 0);
		}
		100% {
			transform: scale(0.95);
			box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
		}
	}

	.action-type-cell {
		font-family: inherit;
	}

	.btn-execute {
		background: #0f172a;
		color: white;
		border: none;
		border-radius: 6px;
		padding: 0.4rem 0.75rem;
		font-weight: 600;
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.btn-execute:hover {
		background: #1e293b;
		transform: translateY(-1px);
	}

	.btn-execute:active {
		transform: translateY(0);
	}

	.btn-execute:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	.check-mark {
		color: #059669;
		font-weight: 600;
		font-size: 0.85rem;
	}

	.hint-footer {
		margin-top: 2rem;
		padding-top: 1rem;
		border-top: 1px solid #e2e8f0;
		text-align: center;
	}

	.hint-footer p {
		color: #64748b;
		font-size: 0.875rem;
		margin: 0;
	}

	/* Expanding row styles */
	.detail-row {
		background-color: #f8fafc;
	}

	.detail-content {
		padding: 1.25rem;
		border-left: 4px solid #3b82f6;
		background: #ffffff;
		border-bottom: 1px solid #e2e8f0;
	}

	.detail-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1.5rem;
		margin-bottom: 1.25rem;
	}

	@media (min-width: 768px) {
		.detail-grid {
			grid-template-columns: 1.2fr 0.8fr;
		}
	}

	.detail-grid-actions {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1.5rem;
	}

	@media (min-width: 768px) {
		.detail-grid-actions {
			grid-template-columns: 1fr 1fr;
		}
	}

	.detail-section h4 {
		margin: 0 0 0.75rem 0;
		font-family: 'Outfit', sans-serif;
		font-size: 1rem;
		color: #1e293b;
		border-bottom: 1px solid #f1f5f9;
		padding-bottom: 0.25rem;
	}

	.diagnostic-item {
		margin-bottom: 0.75rem;
	}

	.diagnostic-label {
		display: block;
		font-size: 0.8rem;
		font-weight: 600;
		color: #64748b;
		margin-bottom: 0.15rem;
	}

	.diagnostic-text {
		margin: 0;
		font-size: 0.9rem;
		color: #334155;
		line-height: 1.4;
	}

	.confidence-badge {
		background: #e0e7ff;
		color: #4338ca;
		padding: 0.15rem 0.5rem;
		border-radius: 4px;
		font-weight: 700;
		font-size: 0.8rem;
		display: inline-block;
	}

	.metadata-grid {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 0.5rem 1rem;
		font-size: 0.875rem;
		align-items: baseline;
	}

	.meta-label {
		color: #64748b;
		font-weight: 600;
	}

	.meta-val {
		color: #334155;
		word-break: break-all;
	}

	.metrics-block {
		margin-top: 1rem;
	}

	.metrics-block h5 {
		margin: 0 0 0.5rem 0;
		font-size: 0.8rem;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.metrics-pre {
		background: #0f172a;
		color: #38bdf8;
		padding: 0.75rem;
		border-radius: 6px;
		font-size: 0.8rem;
		overflow-x: auto;
		margin: 0;
	}

	.associated-actions {
		border-top: 1px solid #f1f5f9;
		padding-top: 1rem;
		margin-top: 1rem;
	}

	.associated-actions h4 {
		margin: 0 0 0.75rem 0;
		font-family: 'Outfit', sans-serif;
		font-size: 1rem;
		color: #1e293b;
	}

	.sub-table-container {
		background: #f8fafc;
		border-radius: 8px;
		padding: 0.5rem;
		border: 1px solid #e2e8f0;
		overflow-x: auto;
	}

	.sub-table {
		width: 100%;
		border-collapse: collapse;
	}

	.sub-table th {
		border-bottom: 1px solid #e2e8f0;
		padding: 0.5rem;
		background: transparent;
		font-size: 0.7rem;
	}

	.sub-table td {
		border-bottom: 1px solid #e2e8f0;
		padding: 0.5rem;
		font-size: 0.85rem;
	}

	.sub-table tr:last-child td {
		border-bottom: none;
	}

	.payload-list {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.payload-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
	}

	.payload-key {
		font-weight: 600;
		color: #64748b;
	}

	.payload-val {
		background: #f1f5f9;
		color: #1e293b;
		padding: 0.1rem 0.4rem;
		border-radius: 4px;
	}

	.error-banner {
		background: #fef2f2;
		border-left: 4px solid #ef4444;
		color: #991b1b;
		padding: 0.75rem;
		border-radius: 6px;
		margin-top: 1rem;
		font-size: 0.875rem;
	}

	.error-banner pre {
		margin: 0.5rem 0 0 0;
		overflow-x: auto;
		font-size: 0.8rem;
		background: rgba(0,0,0,0.02);
		padding: 0.5rem;
		border-radius: 4px;
	}

	/* Chevron indicator */
	.chevron {
		display: inline-block;
		width: 6px;
		height: 6px;
		border-right: 2px solid #64748b;
		border-bottom: 2px solid #64748b;
		transform: rotate(-45deg);
		transition: transform 0.2s ease;
		vertical-align: middle;
	}

	.clickable-row.active-row .chevron {
		transform: rotate(45deg);
	}

	.chevron-col {
		width: 2rem;
		text-align: center;
		padding-right: 0 !important;
	}
</style>
