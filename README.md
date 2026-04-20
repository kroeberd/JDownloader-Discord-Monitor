<div align="center">

<img src="https://raw.githubusercontent.com/kroeberd/JDownloader-Discord-Monitor/main/logos/logo.svg" width="128" alt="JDownloader Monitor logo"/>

# JDownloader Monitor

[![Version](https://img.shields.io/badge/version-v0.0.2-ff7b32)](https://github.com/kroeberd/jdownloader-discord-monitor/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/kroeberd/jdownloader-docker-monitor?style=flat-square&color=3b82f6)](https://hub.docker.com/r/kroeberd/jdownloader-docker-monitor)
[![Discord](https://img.shields.io/badge/Discord-Join-5865f2?logo=discord&logoColor=white)](https://discord.gg/8Vb9cj4ksv)
[![License](https://img.shields.io/badge/license-GPL--3.0-4e8dff)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Support-ffdd00?logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/kroeberd)

</div>

`v0.0.2` continues the clean rebuilt foundation of the original monitor with stronger webhook safety checks, Docker Hub README sync, a refreshed UI, and version-aware Discord footer rendering.

## Existing Repository Analysis

The previous implementation was a compact proof of concept:

- Runtime flow: `app.py` loaded env vars, logged into MyJDownloader, polled device links in a loop, derived a few counters, and posted a Discord embed on every cycle.
- Strengths worth preserving: the product idea, Docker-first distribution, MyJDownloader integration, multilingual intent, and a simple self-hosting story.
- Major weaknesses: all logic in one file, no persistence, no GUI, direct network calls without proper retry discipline, no structured logging, no health endpoints, no webhook dedupe across restarts, no config validation, and no clear extension point for templates or multiple webhook layouts.
- Reliability risks: token expiry only handled in one narrow path, no timeout strategy around Discord calls, no backoff policy, no audit trail, no quiet hours or throttling, and startup state loss causing duplicate notifications after restart.
- UX limitations: env vars only, no onboarding, no preview, no webhook management, no device overview, no logs page, and no operator-friendly validation.

That analysis led to a clean rebuild instead of an incremental refactor.

## Architecture

The new structure separates concerns into testable layers:

- `jd_monitor/services/myjd.py`: MyJDownloader integration and normalization.
- `jd_monitor/services/poller.py`: background polling, defensive retry/backoff behavior, and event classification.
- `jd_monitor/services/themes.py`: Discord rendering and preview generation for built-in themes.
- `jd_monitor/services/notifications.py`: webhook delivery, dedupe, retry handling, and audit persistence.
- `jd_monitor/repo_utils.py` + `jd_monitor/db.py`: SQLite-backed config, device state, and notification history.
- `jd_monitor/api.py`: FastAPI routes for GUI, preview, test-send, logs, dashboard data, and health.
- `jd_monitor/templates` + `jd_monitor/static`: server-rendered modern web UI.

### Why FastAPI + server-rendered UI

FastAPI gives typed models, clean API boundaries, and lightweight async background work. The frontend is server-rendered HTML with custom JS/CSS instead of a Node build pipeline because this keeps Docker deployment smaller and simpler for self-hosters while still delivering a modern interactive GUI.

## Features

- Dashboard with health, device status, and audit history
- Persistent config storage in SQLite
- Multiple devices and multiple Discord webhooks
- Per-webhook theme selection
- Built-in themes: `minimal`, `modern`, `compact`, `detailed`, `status-card`, `high-contrast`, `homelab`
- Discord preview before saving
- Test-send button
- Structured JSON logging
- Health endpoints for container orchestration
- Legacy env-var bootstrap for first-run migration
- Docker and Docker Compose deployment

## GUI Pages

The rebuilt UI includes:

- Dashboard/home
- Device management
- Webhook/theme management
- Preview/test-send workspace
- Logs view
- Settings and connection page

## Quick Start

### Docker Compose

```yaml
services:
  jd-monitor:
    build: .
    ports:
      - "8080:8080"
    environment:
      JD_MONITOR_DATA_DIR: /data
      MYJD_EMAIL: me@example.com
      MYJD_PASSWORD: change-me
      MYJD_DEVICES: HomeJD,ServerJD
      WEBHOOK_URL: https://discord.com/api/webhooks/xxx/yyy
      INTERVAL: "300"
      LANG: en
    volumes:
      - ./data:/data
    restart: unless-stopped
```

Open [http://localhost:8080](http://localhost:8080).

### Local Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
uvicorn jd_monitor.main:app --reload --port 8080
```

## Configuration

- Persistent app config is stored in SQLite under `JD_MONITOR_DATA_DIR`.
- A typed example config is available at `examples/config.example.json`.
- On first run, old env vars like `WEBHOOK_URL`, `MYJD_EMAIL`, `MYJD_PASSWORD`, `MYJD_DEVICES`, `INTERVAL`, and `LANG` are imported into the new config automatically.

## Health and Observability

- `GET /health/live`
- `GET /health/ready`
- JSON logs written to `/data/app.log`
- Notification audit stored in SQLite and surfaced in the dashboard

## Migration Notes

From the old version to `v2`:

1. Keep your existing `MYJD_EMAIL`, `MYJD_PASSWORD`, `MYJD_DEVICES`, `WEBHOOK_URL`, `INTERVAL`, and `LANG` variables for the first startup.
2. Start the new container once; the app will create a default typed configuration from those values.
3. Open the GUI and refine devices, webhooks, themes, and notification behavior.
4. After saving in the UI, you can gradually move away from env-only configuration.

## Major Decisions

- Rebuild instead of refactor: the previous code was too coupled to evolve safely into a production app.
- SQLite for self-hosting: simple, durable, and easy to back up.
- Server-rendered frontend: modern enough for this product, but much simpler to deploy than a separate Node build stack.
- Webhook themes as data-driven renderers: new templates can be added without touching the poller core.
- Persistent audit and dedupe: avoids restart spam and improves operability.

## Quality

Run checks locally with:

```bash
python -m compileall jd_monitor
pytest
```

## Community

- Discord: [discord.gg/8Vb9cj4ksv](https://discord.gg/8Vb9cj4ksv)
- Docker Hub: [kroeberd/jdownloader-docker-monitor](https://hub.docker.com/r/kroeberd/jdownloader-docker-monitor)
- Buy Me a Coffee: [buymeacoffee.com/kroeberd](https://buymeacoffee.com/kroeberd)

## Docker Hub README

The repository README is synced to Docker Hub automatically from `main` via GitHub Actions so Docker Hub always shows the current project documentation.
