# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and uses repository tags as release identifiers.

## [Unreleased]

- No unreleased entries yet.

## [v0.0.1] - 2026-04-20

### Added

- Full rebuild from the original single-file script into a modular FastAPI application.
- Persistent SQLite-backed configuration, device snapshot storage, and notification audit history.
- Modern self-hosted web UI with dashboard, device management, webhook management, preview, logs, and settings.
- Discord theme system with built-in templates and preview rendering.
- Health endpoints, structured logging, Docker-first deployment, tests, and release workflow support.
- New brand-aligned SVG logo inspired by the visual direction of Mediastarr and alldebrid-client.

### Changed

- Project versioning reset to `v0.0.1` to mark the new foundation release.
- README rewritten with architecture notes, migration guidance, and deployment instructions.

### Fixed

- GitHub release workflow now normalizes GHCR image names to lowercase before publishing.
