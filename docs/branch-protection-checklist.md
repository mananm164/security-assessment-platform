# Branch Protection Checklist

Apply these settings after the Day 12 workflows have run successfully at least once. Do not require checks that are unavailable for this repository.

## Required checks for `main`

Require these checks before merge once they are green:

- `backend`
- `frontend`
- `e2e`
- `security-dependencies`
- `docker-build`

Require these only after GitHub confirms they run in this repository:

- `codeql-python`
- `codeql-javascript-typescript`
- `dependency-review`

## Pull request controls

- Require pull request review before merging where appropriate for the team.
- Require branches to be up to date before merge if the project starts seeing frequent merge conflicts.
- Dismiss stale approvals when new commits are pushed if using formal review.
- Require conversation resolution before merge.

## Main branch protections

- Block force pushes to `main`.
- Block deletion of `main`.
- Restrict direct pushes to trusted maintainers if the repository policy allows it.
- Do not allow bypassing required checks except for a documented emergency process.

## Repository security settings

Enable when available for the repository plan/settings:

- Dependabot alerts.
- Dependabot security updates.
- GitHub Secret Scanning.
- Push protection.
- Code scanning alerts for CodeQL.

## Day 12 non-goals

Do not configure Azure deployment, registry push, release automation or production credentials as part of this checklist.
