# Changelog

All notable changes to this project will be documented in this file.

The release workflow reads the section matching the value in `VERSION` and publishes it as the GitHub release body.

## [Unreleased]

### Added

- No unreleased entries yet.

## [0.0.1] - 2026-04-20

### Added

- Full rebuild from the original single-file script into a modular FastAPI application.
- Persistent SQLite-backed configuration, device snapshot storage, and notification audit history.
- Modern self-hosted web UI with dashboard, device management, webhook management, preview, logs, and settings.
- Discord theme system with built-in templates and preview rendering.
- Health endpoints, structured logging, Docker-first deployment, tests, and release workflow support.
- New brand-aligned SVG logo inspired by the visual direction of Mediastarr and alldebrid-client.
- Dedicated release workflow with GitHub Release, GHCR publishing, Docker Hub publishing, and build cache support.

### Changed

- Project versioning now uses `VERSION` as the single release source of truth.
- Git tag format remains `v<version>`, while changelog headings use `[<version>]`.
- README rewritten with architecture notes, migration guidance, and deployment instructions.

### Fixed

- Release notes are now taken directly from the matching changelog section for the active version.
- GHCR publishing no longer depends on mixed-case repository names.
