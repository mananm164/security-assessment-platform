# CI, E2E and Security Quality Gate

Day 12 adds a non-deploying quality gate for SARP. It runs on pushes to `main` and pull requests to `main`. It does not log in to Azure, push container images, deploy, run scanners, or contact external client systems.

## Workflows

### `.github/workflows/ci.yml`

Jobs:

- `backend`: installs `backend/requirements/dev.txt`, runs Django checks, verifies migrations are committed, applies migrations to a PostgreSQL/pgvector service, runs the full Django test suite, then runs `ruff check apps config` and `ruff format --check apps config`. Ruff excludes generated migrations and tests to avoid noisy generated-code formatting churn while still gating maintained backend source.
- `frontend`: uses Node 24, runs `npm ci`, `npm run lint`, `npm run test -- --run`, and `npm run build`. Existing Vite bundle-size and oxlint warnings are not suppressed.
- `e2e`: installs Playwright Chromium and starts a disposable local Docker Compose backend/database stack using `docker-compose.e2e.yml`. It migrates the database, runs `seed_e2e_data`, and executes Chromium-only browser tests from `frontend/e2e`. The stack is always removed with volumes.
- `security-dependencies`: runs `pip-audit -r backend/requirements/base.txt` and `npm audit --omit=dev --audit-level=high`. There are no blanket ignores or `continue-on-error` settings. Any exception must be recorded in `docs/security/vulnerability-exceptions.md`.
- `docker-build`: builds backend and frontend images with `docker compose build backend frontend` but does not log in to a registry or push.

All jobs have `timeout-minutes`, read-only `contents: read` permissions, and concurrency cancellation for superseded branch/PR runs.

### `.github/workflows/codeql.yml`

CodeQL runs for Python and JavaScript/TypeScript on pushes, pull requests and a weekly schedule. The workflow grants `security-events: write` only to the CodeQL job, as required by the CodeQL action. It uses build mode `none`, which GitHub documents as appropriate for interpreted languages.

CodeQL availability and result display depend on repository settings and plan. If code scanning is unavailable, keep the workflow file but do not require it in branch protection until GitHub shows successful runs.

### `.github/workflows/dependency-review.yml`

Dependency Review runs only on pull requests. It fails on newly introduced high or critical vulnerabilities. It does not enforce a license policy yet because SARP has not defined one. GitHub documents that dependency review is available for public repositories and for private repositories with GitHub Advanced Security; if unavailable, keep `security-dependencies` as the mandatory audit gate and do not require this check until the repository supports it.

## E2E Data Policy

`python manage.py seed_e2e_data` refuses to run unless `E2E_TEST_MODE=1`. It creates only fictional `@sarp.example` users, a fictional client, memberships, one assessment and one finding. It never creates a superuser. The password comes from `E2E_TEST_PASSWORD` and the CI workflow uses a run-scoped test-only value.

The browser import test uses the fictional Nmap XML fixture. The fixture includes `E2E_FAKE_SECRET_DO_NOT_RENDER` in raw Nmap command metadata so the test can assert that raw command metadata is not exposed in the UI. SARP still does not retain raw reports.

## Artifact Policy

Playwright screenshots, video and traces are retained only on failure/retry. CI uploads only `frontend/playwright-report/` and `frontend/test-results/` when the E2E job fails, with 7-day retention. The workflows do not upload raw scanner reports, `.env`, Docker volumes, database dumps or backend logs.

## Local Commands

Baseline product checks:

```bash
docker compose up --build -d
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test
cd frontend && npm run lint && npm run test -- --run && npm run build
```

Backend quality checks:

```bash
cd backend
ruff check apps config
ruff format --check apps config
python manage.py makemigrations --check --dry-run
```

Disposable local E2E run:

```bash
export POSTGRES_DB=sarp_e2e
export POSTGRES_USER=sarp_e2e
export POSTGRES_PASSWORD=sarp_e2e_password
export E2E_TEST_MODE=1
export E2E_TEST_PASSWORD=sarp-e2e-local-test-only
export VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1

docker compose -f docker-compose.yml -f docker-compose.e2e.yml up -d --build db backend
for attempt in $(seq 1 60); do curl -fsS http://127.0.0.1:8000/api/v1/health/ && break || sleep 2; done
docker compose -f docker-compose.yml -f docker-compose.e2e.yml exec backend python manage.py migrate --noinput
docker compose -f docker-compose.yml -f docker-compose.e2e.yml exec backend python manage.py seed_e2e_data
cd frontend
npm run e2e
cd ..
docker compose -f docker-compose.yml -f docker-compose.e2e.yml down -v --remove-orphans
```

Security checks:

```bash
cd backend && pip-audit -r requirements/base.txt
cd ../frontend && npm audit --omit=dev --audit-level=high
cd .. && detect-secrets scan --baseline .secrets.baseline
```

Docker build check:

```bash
POSTGRES_DB=sarp_build POSTGRES_USER=sarp_build POSTGRES_PASSWORD=sarp_build_password docker compose build backend frontend
```

## Secret Baseline

`.secrets.baseline` is a reviewed detect-secrets baseline. Do not baseline real credentials. Updates to the baseline are security-sensitive review changes. `.env` and `.env.*` remain ignored and must not be committed.

## Known Limitations

- CI and CodeQL do not prove absence of vulnerabilities. They are guardrails for known classes of regressions.
- Browser E2E tests prove critical user journeys and UI boundaries; backend API permission tests remain the security proof.
- Dependency Review and CodeQL result visibility may depend on GitHub repository settings/plan.
- Azure deployment is intentionally out of scope for Day 12 and begins later.

## Reference Sources

- Playwright CI guidance: https://playwright.dev/docs/ci-intro
- GitHub secure Actions guidance: https://docs.github.com/en/actions/reference/security/secure-use
- CodeQL action guidance: https://github.com/github/codeql-action
- Dependency Review action guidance: https://github.com/actions/dependency-review-action
- detect-secrets baseline workflow: https://github.com/Yelp/detect-secrets
