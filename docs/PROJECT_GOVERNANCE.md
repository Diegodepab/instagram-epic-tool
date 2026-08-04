# Project Governance

## Repository Standards

- Source code is organized under `src/`.
- Architecture, deployment, security, and user documentation live under `docs/`.
- CI runs on pull requests and pushes to `main`.
- release-please maintains Semantic Versioning, tags, GitHub releases, and `CHANGELOG.md` from Conventional Commits.
- The project has an explicit MIT license. Apache 2.0 is the organizational default for projects without a chosen license; changing an existing license requires owner and organization approval.

## Required GitHub Settings

These controls cannot be committed as repository files and must be configured in GitHub.

### Actions

In **Settings → Actions → General → Workflow permissions**:

1. Enable read and write permissions for workflows.
2. Allow GitHub Actions to create and approve pull requests so release-please can open release PRs.

### Main Branch Protection

Create a branch ruleset for `main` with:

- pull requests required before merge;
- at least one approval;
- stale approvals dismissed after new commits;
- frontend and backend CI jobs required;
- branch required to be up to date;
- conversation resolution required;
- force pushes and branch deletion disabled.

## Release Flow

```mermaid
flowchart LR
    Branch[Feature branch] --> PR[Pull request]
    PR --> CI[Lint, build and tests]
    CI --> Review[Review and approval]
    Review --> Main[main]
    Main --> ReleasePR[release-please PR]
    ReleasePR --> Tag[Version tag and GitHub release]
```

Only real project history counts toward organizational activity indicators. Commits and tags must never be fabricated to satisfy a KPI. During active development, review the changelog at least every two weeks.

## Deployment Approval

Every deployment must be tested in the private `Apolo_Dev` environment before production. Public IPs and concrete internal addresses are not committed. Follow [DEPLOYMENT.md](DEPLOYMENT.md) and record deployment evidence in the relevant pull request or release process.
