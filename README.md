# Observstory

**A living control center for shared repositories.**

Observstory turns repository activity into a project view that answers:

- What changed?
- Who is working on what?
- Which parts of the project are moving?
- Where are parallel efforts colliding?
- What is waiting for review or integration?
- What does the project look like right now?

It is designed for hackathons and other fast, AI-assisted team builds where each contributor may be working in a separate coding-agent loop.

## Product idea

A shared repository already contains a large part of the coordination signal: commits, pull requests, issues, changed files, checks, contributors and timestamps. Observstory continuously interprets those signals into **typed project lanes** and builds a dashboard from them.

```text
GitHub events + periodic reconciliation
                  |
                  v
            state collector
                  |
                  v
          typed project model
                  |
          +-------+--------+
          |                |
          v                v
     dashboard          MCP/API
     for humans        for agents
```

### The important boundary

**MCP is not the collector.**

For the installable product:

1. **GitHub Action (now)** — easiest repo-native MVP. Add one workflow and Observstory builds a dashboard.
2. **GitHub App (next)** — install once; webhooks + scheduled reconciliation build project state without copying code into every repo.
3. **MCP server (later)** — exposes the same typed state to coding agents and LLMs.

That means humans and agents see the same project model.

## Quick start

Create `.github/workflows/observstory.yml` in the repository you want to observe:

```yaml
name: Observstory

on:
  push:
  pull_request:
    types: [opened, synchronize, reopened, closed]
  issues:
    types: [opened, edited, closed, reopened, labeled, unlabeled]
  workflow_dispatch:
  schedule:
    - cron: "*/10 * * * *"

permissions:
  contents: read
  pull-requests: read
  issues: read
  actions: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Observstory
        uses: blackmath88/observstory@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/configure-pages@v5

      - uses: actions/upload-pages-artifact@v3
        with:
          path: observstory

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4
```

Then enable **Settings → Pages → Source: GitHub Actions**.

GitHub scheduled workflows are best-effort rather than a hard realtime clock; pushes, PRs and issues update immediately, while the ten-minute schedule acts as reconciliation.

## Configuration

Optional `observstory.config.json`:

```json
{
  "title": "Project Observatory",
  "window_hours": 48,
  "lanes": [
    {"id": "intent", "label": "Intent", "paths": ["README.md", "docs/", "research/"]},
    {"id": "build", "label": "Build", "paths": ["src/", "app/", "lib/", "packages/"]},
    {"id": "verify", "label": "Verify", "paths": ["test/", "tests/", "evals/"]},
    {"id": "ship", "label": "Ship", "paths": [".github/", "Dockerfile", "deploy/"]}
  ]
}
```

Anything not matching a configured path lands in **Other**. Coordination signals (PRs/issues) are shown separately rather than forced into a code lane.

## Current MVP

The Action builds:

- repository health summary
- contributor activity
- recent commits
- open and recently changed PRs
- open and recently changed issues
- file activity grouped into typed lanes
- likely overlap/collision signals when multiple contributors touch the same paths
- a machine-readable `observstory/data/snapshot.json`
- a static `observstory/index.html`

The dashboard is intentionally generated from a typed snapshot rather than directly from arbitrary API responses. That snapshot becomes the contract for future UI modules, storage, APIs and MCP tools.

## Roadmap

See [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md).

## Why this exists

AI-assisted development makes individual creation extremely fast, but can make collaboration less visible: contributors can disappear into private agent conversations and return with large finished artifacts. Observstory focuses on the missing coordination layer — shared situational awareness while the work is happening.
