<section class="hero">
	<h1>Autonomous Infrastructure Maintainer</h1>
	<p class="subtitle">UI for incidents and actions backed by FastAPI.</p>

	<div class="cta">
		<a class="button" href="/incidents">Open Incidents</a>
		<a class="button secondary" href="/actions">Open Actions</a>
	</div>

	<p class="hint">
		If data doesn’t load, ensure the backend is running and set `BACKEND_URL` in `client/.env`.
	</p>
</section>

<style>
	.hero {
		padding: 1rem 0;
	}
	h1 {
		margin: 0;
		font-size: 2rem;
	}
	.subtitle {
		margin-top: 0.5rem;
		color: #666;
	}
	.cta {
		display: flex;
		gap: 0.75rem;
		margin-top: 1rem;
		flex-wrap: wrap;
	}
	.button {
		display: inline-block;
		background: #111;
		color: white;
		text-decoration: none;
		padding: 0.55rem 0.9rem;
		border-radius: 8px;
		font-weight: 600;
	}
	.button.secondary {
		background: #f5f5f5;
		color: #111;
	}
	.hint {
		margin-top: 1rem;
		color: #666;
		font-size: 0.95rem;
	}
</style>
