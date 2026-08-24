# Changelog

All notable changes to this project are documented in this file. Releases follow Semantic Versioning and are prepared by release-please from Conventional Commits.

## [0.2.0](https://github.com/Diegodepab/instagram-epic-tool/compare/v0.1.0...v0.2.0) (2026-08-24)


### Added

* add backend live scan service ([2eff840](https://github.com/Diegodepab/instagram-epic-tool/commit/2eff840e66368023feb8ef1a81fd85cb08d9e0a7))
* add live scan interface ([464573e](https://github.com/Diegodepab/instagram-epic-tool/commit/464573e635db22cf7454aef0d925e9430a0757b6))
* rebuild CircleScope as a secure web application ([a348a96](https://github.com/Diegodepab/instagram-epic-tool/commit/a348a96c627e50bcae8400cdbabac676bdab1d4c))

## [Unreleased]

### Added

- Safe parser for official Instagram GDPR ZIP and JSON-folder exports.
- Validation for archive traversal, links, encryption, size, compression ratio, encoding, and JSON structure.
- Tests for multipart follower exports, extracted directories, invalid formats, and unsafe archives.
- Guided import interface, community metrics dashboard, search, and interactive graph exploration.
- One-hour in-memory analysis sessions with explicit deletion.
- Non-root Docker images, private API proxy, health checks, and one-command Compose deployment.
- User, deployment, security, and privacy documentation.
- Fictional demo mode for evaluating the complete product without personal data.
- Paginated relationship lists with search, category filters, and CSV export.
- Balanced graph sampling for large accounts while retaining exact full-dataset metrics.
- Support for official exports up to 1 GiB while reading only relationship JSON files.
- Real upload progress, processing state, client-side size validation, and cancellation for large exports.
- Partial date-range diagnostics and adaptive collision-aware graph forces.
- DDD import pipeline with strict Pydantic boundaries, defensive partition discovery, pure set mathematics, and a direct `nodes`/`links` endpoint.
- Pull request, contribution, Conventional Commit, governance, and branch-protection guidance.
- Incremental merging of multiple expressly authorized Instagram JSON exports.
- Relationship timestamps, provenance and genuine expansion for profiles backed by imported data.
- A 12-step functional product guide that demonstrates filters, search, views and automatic demo cleanup.
- An isolated, disabled-by-default own-account connector based on the vendored `instagrapi` snapshot.
- A non-executing defensive assessment for the prohibited credential-attempt repository.
- Explicit disclaimer, third-party notices, security policy and dependency update automation.

### Fixed

- Use type-only TypeScript imports so Vite does not request erased interfaces at runtime.
- Make the React force-graph reference compatible with the current React and TypeScript versions.

### Changed

- Route local frontend API calls through the Vite development proxy.
- Document the web, API, and GDPR export processing architecture.
- Add baseline build and test automation.
- Remove obsolete proof-of-concept files and unused upstream examples, tests and automation from vendored sources.
