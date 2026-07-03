# Day 7 Codex Prompt — React Operational UI

Read these files before coding:

```text
docs/project-knowledge/02_PRODUCT_AND_ARCHITECTURE.md
docs/project-knowledge/03_DIRECTORY_STRUCTURE.md
docs/project-knowledge/04_SECURITY_AND_RBAC.md
docs/project-knowledge/08_CODEX_WORKING_CONTRACT.md
docs/project-knowledge/11_CURRENT_AND_FUTURE_API.md
docs/project-knowledge/21_DAY_07_REACT_UI_IMPLEMENTATION_BRIEF.md
docs/project-knowledge/22_UX_UI_DESIGN_SYSTEM.md
```

You are implementing Day 7 of SARP: the React operational UI.

## Current verified backend state

- JWT email login, refresh and `/auth/me/` work.
- Tenant-scoped Clients, Assessments, Assets and Findings exist.
- Nmap XML, ZAP Traditional JSON, Nessus `.nessus` XML and Burp XML imports exist.
- Import list and ScannerObservation list APIs exist.
- Observation triage and promotion APIs exist.
- Backend suite currently passes 84 tests.
- Backend is the security boundary. Do not replace server-side security with UI checks.

## Goal

Build a simple, professional Material UI frontend that lets an assigned Consultant:

```text
Login
→ view authorised Assessments
→ open one Assessment
→ view Assets, Imports, Scanner Observations and Findings
→ confirm an Observation
→ promote it to a Finding
→ view the Finding
```

## Hard rules

- Do not modify unrelated backend files.
- Do not change importer, triage, promotion, tenant-security or parser behaviour unless a real integration defect requires it. Explain any required backend change before making it.
- Use React + Vite + Material UI + Axios + React Router only.
- Use JavaScript, not TypeScript, for this sprint.
- Do not use Redux, Zustand, React Query, Tailwind, Bootstrap, chart libraries, animation libraries, dark mode or custom design frameworks.
- Use a central MUI theme and `CssBaseline`.
- Follow `22_UX_UI_DESIGN_SYSTEM.md` exactly.
- Keep JWT access and refresh tokens in memory inside AuthContext. Do not use localStorage, sessionStorage or URL parameters.
- On API 401: clear session and navigate to `/login`. Do not add automatic refresh in this task.
- Do not call a fake or planned endpoint. Use only endpoints that actually exist in the current backend.
- Do not build a browser upload UI because report ingestion is currently controlled by the management command.
- Do not show a dashboard, charts, AI, CVE enrichment, reports, admin UI or non-working menu items.
- Never render or log raw scanner files, raw Burp traffic, tokens, cookies, credentials, query strings, payloads, or raw error objects.
- Handle API errors with safe human-readable messages.
- Add frontend tests for critical flows.

## Required routes

```text
/login
/assessments
/assessments/:assessmentId
/findings/:findingId
*
```

Use `?tab=` on assessment detail for:

```text
overview
assets
imports
observations
findings
```

## Required UI

1. Login page with email/password, generic error, loading state and fictional-data note.
2. AuthContext and ProtectedRoute.
3. App shell with restrained sidebar/top bar and user role/sign-out area.
4. Assessment list using live API data.
5. Assessment workspace with tabs for Overview, Assets, Imports, Scanner Observations and Findings.
6. Observations table with source-tool and triage-status filters.
7. Observation detail drawer using only safe persisted fields.
8. Triage dialog with frontend validation:
   - false positives require a note;
   - duplicates require a different observation in same assessment;
   - promoted observations cannot be triaged.
9. Promotion dialog that collects reviewed CVSS, business impact, remediation owner and due date. Do not let the frontend submit a final severity; backend derives it.
10. Finding detail page.
11. Shared LoadingState, EmptyState, ErrorState, Confirmation Dialog, SeverityChip, StatusChip and SourceToolChip.
12. Frontend smoke tests using Vitest + React Testing Library.

## Required file structure

Follow `21_DAY_07_REACT_UI_IMPLEMENTATION_BRIEF.md` exactly for the Day 7 frontend tree.

## Required output before code

First respond with:

1. The files you will create or modify.
2. A 5–8 bullet implementation plan.
3. Any backend endpoint/API mismatch you identify.
4. The exact commands you will run after changes.

Then implement in small logical steps.

## Verification requirements

Run and report:

```bash
cd frontend
npm run test -- --run
npm run build

docker compose exec backend python manage.py test
git diff --check
```

Also give manual browser verification steps for the full Consultant workflow.

## Commit guidance

Use small commits only after checks pass:

```text
feat: scaffold react material ui application shell
feat: add jwt login and protected assessment workspace
feat: add observation triage and finding promotion interface
test: add frontend auth and workflow smoke tests
```
