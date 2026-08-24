# Contributing

## Development Setup

Follow the local development instructions in [README.md](README.md). Keep product code under `src/backend` or `src/frontend`, tests under `tests`, and product-specific documentation under `docs`.

Never commit an Instagram export, relationship CSV, credential, access token, username list, or other personal data. Use the fictional demo generator and synthetic fixtures in tests.

## Workflow

1. Create a short-lived branch from `main`.
2. Make one focused change and add proportionate tests.
3. Run the verification commands documented in the pull request template.
4. Update `CHANGELOG.md` and relevant documentation when behavior changes.
5. Open a pull request. Its title must follow Conventional Commits.
6. Validate merged changes in `Apolo_Dev` before production deployment.

## Conventional Commits

Use `<type>(optional-scope): imperative description`, without a final period.

Examples:

```text
feat(import): support large official exports
fix(graph): preserve node coordinates
docs: explain private deployment
test(parser): reject traversal paths
```

Use `feat!:` or a `BREAKING CHANGE:` footer for incompatible changes. `feat` creates a minor release and `fix` creates a patch release through release-please.

To validate commit messages locally:

```bash
pip install pre-commit
pre-commit install --hook-type commit-msg
```

## Review Expectations

- Preserve the credential-free official-export flow. Any optional connector must remain isolated, disabled by default, restricted to an authenticated owned or authorized account, bounded and non-persistent.
- Parse archives without extracting them.
- Do not weaken upload, archive, session, container, or browser security controls.
- Keep the interface understandable without technical knowledge.
- Explain data limitations honestly; never imply that unknown Instagram relationships were discovered.
