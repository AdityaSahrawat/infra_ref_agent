<div class="container">
	<header>
		<h1>🤖 Autonomous Infrastructure Maintainer</h1>
		<p class="subtitle">Monitor · Detect · Act</p>
	</header>

	<main>
		<section class="overview">
			<h2>System Overview</h2>
			<p>Basic autonomous DevOps agent that monitors system metrics, detects issues, and performs maintenance actions automatically.</p>
		</section>

		<div class="features">
			<div class="feature-card">
				<h3>📊 Monitor</h3>
				<p>Collect system metrics (CPU, memory, uptime)</p>
			</div>
			<div class="feature-card">
				<h3>🔍 Detect</h3>
				<p>Identify issues using threshold rules</p>
			</div>
			<div class="feature-card">
				<h3>⚡ Act</h3>
				<p>Execute maintenance actions automatically</p>
			</div>
		</div>
	</main>
</div>

<style>
	.container {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
		font-family: system-ui, -apple-system, sans-serif;
	}

	header {
		text-align: center;
		margin-bottom: 3rem;
	}

	h1 {
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
		color: #333;
	}

	.subtitle {
		font-size: 1.2rem;
		color: #666;
		margin: 0;
	}

	.overview {
		background: #f5f5f5;
		padding: 1.5rem;
		border-radius: 8px;
		margin-bottom: 2rem;
	}

	.overview h2 {
		margin-top: 0;
		color: #333;
	}

	.features {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
	}

	.feature-card {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
		text-align: center;
		transition: transform 0.2s;
	}

	.feature-card:hover {
		transform: translateY(-4px);
		border-color: #4a90e2;
	}

	.feature-card h3 {
		margin-top: 0;
		font-size: 1.5rem;
		color: #333;
	}

	.feature-card p {
		color: #666;
		margin-bottom: 0;
	}
</style>
