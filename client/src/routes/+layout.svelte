<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app">
	<header class="header">
		<div class="brand">
			<div class="title">Infra Ref Agent</div>
			<div class="subtitle">Incidents · Actions</div>
		</div>
		<nav class="nav">
			<a href="/">Home</a>
			<a href="/incidents">Incidents</a>
			<a href="/actions">Actions</a>
		</nav>
	</header>

	<main class="main">
		{@render children()}
	</main>
</div>

<style>
	.app {
		max-width: 1000px;
		margin: 0 auto;
		padding: 1.25rem;
		font-family: system-ui, -apple-system, sans-serif;
		color: #111;
	}
	.header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 1rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #e5e5e5;
		margin-bottom: 1.25rem;
	}
	.brand .title {
		font-size: 1.25rem;
		font-weight: 700;
	}
	.brand .subtitle {
		font-size: 0.9rem;
		color: #666;
	}
	.nav {
		display: flex;
		gap: 0.9rem;
	}
	.nav a {
		color: #111;
		text-decoration: none;
		padding: 0.25rem 0.4rem;
		border-radius: 6px;
	}
	.nav a:hover {
		background: #f5f5f5;
	}
	.main {
		min-height: 70vh;
	}
</style>
