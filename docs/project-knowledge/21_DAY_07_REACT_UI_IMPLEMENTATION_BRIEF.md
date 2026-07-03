# Day 7 Implementation Brief — React Operational UI

## Purpose

Day 7 turns the working backend into a usable internal consultant workspace. Build only pages that use live, already-implemented APIs. Do not add fake metrics, mocked scanner data, an upload endpoint, AI, RAG, dashboard aggregation, or Azure work in this task.

The primary user journey is:

```text
Login as an assigned Consultant
  → see authorised Assessments
  → open an Assessment
  → view Assets, Imports, Scanner Observations and Findings
  → confirm an Observation
  → promote it to a Finding
  → open the created Finding
```

The frontend is an enterprise-style operational tool, not a marketing website. It should look calm, compact, clear, and trustworthy.

---

## Start conditions

Before making React changes:

1. Confirm Day 6 is committed and pushed.
2. Confirm the backend suite remains green:

```bash
docker compose exec backend python manage.py test
```

3. Do not modify existing backend security or parser behaviour unless a real frontend integration bug proves it is necessary.
4. Read these project-knowledge files first:

```text
02_PRODUCT_AND_ARCHITECTURE.md
03_DIRECTORY_STRUCTURE.md
04_SECURITY_AND_RBAC.md
08_CODEX_WORKING_CONTRACT.md
11_CURRENT_AND_FUTURE_API.md
21_DAY_07_REACT_UI_IMPLEMENTATION_BRIEF.md
22_UX_UI_DESIGN_SYSTEM.md
```

---

## Scope

### In scope

- Vite + React frontend scaffold.
- Material UI application shell.
- Axios API client and typed endpoint modules.
- Login using the existing JWT endpoint.
- In-memory JWT session only.
- Protected routes and role-aware navigation.
- Assessment list.
- Assessment workspace with tabs:
  - Overview
  - Assets
  - Imports
  - Scanner Observations
  - Findings
- Observation table with source/status filters.
- Observation detail drawer or page.
- Triage action form.
- Promote-confirmed-observation dialog.
- Finding detail page.
- Reusable loading, error, empty-state and confirmation components.
- Frontend smoke tests for critical user paths.

### Out of scope for Day 7

- Browser upload / import creation. Imports continue through the trusted management command.
- Dashboard metrics or charts; there is no dashboard API yet.
- Client/user-management UI.
- Asset create/edit UI.
- Finding create/edit UI beyond promotion output viewing.
- AI/RAG, CVE enrichment, risk scoring, reports, PDF export, Azure, CI/CD.
- Redux, Zustand, React Query, Tailwind, custom CSS framework, animations, dark mode, custom charting.

---

## Locked technology choices

```text
Frontend: React + Vite, JavaScript (not TypeScript for this sprint)
Routing: react-router-dom
UI: @mui/material + @mui/icons-material + @emotion/react + @emotion/styled
HTTP: axios
Tests: Vitest + React Testing Library + jsdom
State: React hooks and context only
Styling: Material UI `sx` and one central theme; almost no standalone CSS
```

Do not introduce Redux or a global state library. The app is small enough for `AuthContext`, API modules and component-local state.

---

## Required package installation

Create `frontend/` with Vite React, then add only the dependencies below.

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios react-router-dom @mui/material @mui/icons-material @emotion/react @emotion/styled
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Use the existing lockfile. Do not add packages that solve problems Material UI or React already solve.

---

## Required frontend structure

Create the following structure. It is deliberately smaller than the final directory guide because this is the Day 7 vertical slice.

```text
frontend/
├── src/
│   ├── api/
│   │   ├── client.js
│   │   ├── auth.js
│   │   ├── assessments.js
│   │   ├── assets.js
│   │   ├── imports.js
│   │   ├── observations.js
│   │   └── findings.js
│   ├── auth/
│   │   ├── AuthContext.jsx
│   │   └── ProtectedRoute.jsx
│   ├── components/
│   │   ├── AppPageHeader.jsx
│   │   ├── ConfirmDialog.jsx
│   │   ├── EmptyState.jsx
│   │   ├── ErrorState.jsx
│   │   ├── LoadingState.jsx
│   │   ├── SeverityChip.jsx
│   │   ├── SourceToolChip.jsx
│   │   ├── StatusChip.jsx
│   │   └── DataTableToolbar.jsx
│   ├── features/
│   │   ├── assessments/
│   │   │   ├── AssessmentWorkspace.jsx
│   │   │   ├── AssessmentOverviewTab.jsx
│   │   │   ├── AssetsTab.jsx
│   │   │   ├── ImportsTab.jsx
│   │   │   ├── ObservationsTab.jsx
│   │   │   └── FindingsTab.jsx
│   │   ├── observations/
│   │   │   ├── ObservationDetailDrawer.jsx
│   │   │   ├── ObservationTriageDialog.jsx
│   │   │   └── PromoteObservationDialog.jsx
│   │   └── findings/
│   │       └── FindingDetail.jsx
│   ├── layouts/
│   │   ├── AppShell.jsx
│   │   └── AuthLayout.jsx
│   ├── pages/
│   │   ├── LoginPage.jsx
│   │   ├── AssessmentsPage.jsx
│   │   ├── AssessmentDetailPage.jsx
│   │   ├── FindingDetailPage.jsx
│   │   └── NotFoundPage.jsx
│   ├── routes/
│   │   └── AppRoutes.jsx
│   ├── test/
│   │   ├── setup.js
│   │   └── renderWithProviders.jsx
│   ├── theme/
│   │   └── theme.js
│   ├── utils/
│   │   ├── apiError.js
│   │   ├── formatters.js
│   │   └── roleNavigation.js
│   ├── App.jsx
│   └── main.jsx
├── .env.example
├── Dockerfile                 # Optional Day 7 only if backend Docker setup is not disrupted
├── index.html
├── package.json
└── vite.config.js
```

### Placement rules

- `src/api/` only makes HTTP calls and normalises paginated responses.
- `src/auth/` only owns authenticated user/session state and route protection.
- `src/features/` owns domain-specific screens and interactions.
- `src/components/` owns reusable visual building blocks with no API calls.
- `src/pages/` assembles route-level views.
- `src/theme/theme.js` is the one place for visual tokens and MUI component defaults.
- Do not put fetch calls inside chips, rows, or generic components.

---

## API integration contract

Base API URL comes only from an environment variable:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Commit `frontend/.env.example`, never `.env`.

### Authentication

Use:

```text
POST /auth/token/
POST /auth/token/refresh/
GET  /auth/me/
```

### Token storage rule

Keep access and refresh tokens in JavaScript memory inside `AuthContext`.

- Do **not** use `localStorage`.
- Do **not** use `sessionStorage`.
- Do **not** put tokens in URLs.
- A browser refresh requires login again. This is intentional for the current backend setup.

Use an Axios request interceptor to attach:

```http
Authorization: Bearer <access-token>
```

On any `401` response, clear in-memory auth state and redirect to `/login`. Do not build automatic token refresh in Day 7.

### Existing endpoints to use

```text
GET/POST  /clients/
GET/POST  /assessments/
GET/POST  /assets/
GET/POST  /findings/
GET       /imports/
GET       /imports/{id}/observations/
GET       /observations/
POST      /observations/{id}/triage/
POST      /observations/{id}/promote/
```

Do not call endpoints that are only planned in the old API document.

### Pagination helper

The backend paginates list endpoints. API modules must return one simple shape:

```javascript
{
  items: response.data.results ?? response.data,
  count: response.data.count ?? response.data.length,
  next: response.data.next ?? null,
  previous: response.data.previous ?? null,
}
```

Do not assume a list response is always a raw array.

---

## Routes

```text
/login
/assessments
/assessments/:assessmentId
/findings/:findingId
*
```

`/assessments/:assessmentId` uses query-string tabs so the state is shareable:

```text
/assessments/12?tab=observations
/assessments/12?tab=imports
/assessments/12?tab=findings
```

If a user attempts to open a forbidden resource, show the backend-safe outcome. Do not make a client-side guess that the user has access.

---

## Page requirements

### 1. Login page

Must include:

- Product name: `SARP`.
- One sentence: `Security Assessment & Risk Management Platform`.
- Email field.
- Password field with show/hide button.
- Primary `Sign in` button.
- Inline generic error alert for invalid login.
- Loading state that prevents double submission.
- Small fictional-data note.

Must not include:

- Sign-up, forgotten password, social login, “remember me”, marketing content, gradients or illustrations.

On success:

```text
POST /auth/token/
→ GET /auth/me/
→ store session in AuthContext
→ navigate to /assessments
```

### 2. Application shell

Desktop layout:

```text
Fixed left navigation rail
Top app bar
Scrollable main content
```

Navigation items:

```text
Assessments
```

Do not create Dashboard, Clients, AI or Reports menu items before those routes and APIs exist.

Bottom of the sidebar / top-right app bar:

```text
Current user name/email
Role chip
Sign out action
```

Hide navigation items for roles that should not see raw imports/observations. This is UX only; backend permissions remain the security boundary.

### 3. Assessments page

Show a paginated table or compact list of accessible assessments.

Columns:

```text
Assessment name | Client | Framework | Status | Dates | Open
```

Features:

- Clear page heading.
- One line explaining that all data is fictional demo data.
- Clicking a row or `Open` button goes to Assessment detail.
- Loading skeleton.
- Empty state.
- Error state with `Retry`.

Do not build create/edit forms unless the API contract is fully confirmed and tests stay green.

### 4. Assessment workspace

Header shows:

```text
Assessment name
Client name
Framework
Assessment status
Date range
```

Tabs:

```text
Overview | Assets | Imports | Scanner Observations | Findings
```

#### Overview tab

Use existing assessment data only:

- Scope summary.
- Framework.
- Dates.
- A short operational reminder: imported observations require consultant review before they become Findings.

No invented metrics.

#### Assets tab

Table fields:

```text
Name | Type | Host/IP/URL | Environment | Criticality | Internet exposed
```

#### Imports tab

Table fields:

```text
Imported at | Tool | Filename | Status | Created | Re-observed | Open observations
```

Show a non-interactive notice:

```text
Report ingestion is currently performed through the controlled import command.
```

Do not render an upload button that does not work.

#### Scanner Observations tab

Table fields:

```text
Title | Tool | Asset/location | Scanner severity | Triage status | Confidence | Observed | Actions
```

Filters:

```text
Source tool: All, Nmap, ZAP, Nessus, Burp
Triage: All, New, Confirmed, False Positive, Duplicate, Promoted
```

Use server-side/source-tool filtering where the API supports it; otherwise filter the current loaded page locally and do not claim it searches all observations.

Clicking a row opens the detail drawer.

#### Findings tab

Table fields:

```text
Title | Asset | CVSS | Severity | Status | Owner | Due date | Open
```

Rows link to `/findings/:findingId`.

### 5. Observation detail drawer

Use a right-side MUI `Drawer` on desktop, full-screen or bottom sheet on narrow screens.

Show only safe stored data:

```text
Title
Source tool
Asset/location
Scanner severity
Confidence
CVE/CWE IDs if present
Safe evidence summary
Suggested remediation
Import timestamp
Triage status and note
```

Never display raw imported data, raw XML/JSON, payloads, full HTTP messages, tokens, cookies, credentials or raw scanner report text.

Actions for authorised Admin/Consultant only:

```text
Confirm
Mark false positive
Mark duplicate
Promote to Finding
```

Promote remains disabled until the observation is `CONFIRMED`.

### 6. Triage dialog

Required controls:

- Triage action selector.
- Note textarea.
- Duplicate target selector/search only when action is `DUPLICATE`.
- Cancel and submit buttons.

Rules enforced in the UI for clarity, and always enforced by the API:

```text
FALSE_POSITIVE requires a note.
DUPLICATE requires a different Observation in the same Assessment.
PROMOTED observations cannot be triaged again.
```

After success, refresh Observation list and drawer state.

### 7. Promotion dialog

The user must confirm the following before promotion:

```text
Finding title
Consultant-reviewed CVSS score
Business impact
Remediation owner
Due date
```

Do not ask for final severity. The backend derives severity from reviewed CVSS.

After success:

```text
Show success message
Refresh observation
Navigate to new finding detail or provide an explicit `View finding` action
```

### 8. Finding detail page

Show:

```text
Title
CVSS score and derived severity
Assessment and Client
Affected asset
Description
Business impact
Remediation
Owner and due date
Status
Source observation(s)
```

Keep it read-only in Day 7 unless there is a confirmed safe edit endpoint with a verified serializer/API contract.

---

## UX, visual and accessibility requirements

Follow `22_UX_UI_DESIGN_SYSTEM.md` exactly.

Minimum requirements:

- Material UI `CssBaseline` and central `ThemeProvider`.
- No raw browser alert dialogs for normal actions.
- All pages have loading, empty and error states.
- All API errors use a safe human-readable message; never display raw backend JSON or stack traces.
- Use semantic labels on all form fields and icon buttons.
- Table rows are keyboard reachable where they navigate.
- Do not use colour as the only meaning for severity/status.
- Keep focus visible.
- Use `aria-live="polite"` for success/error feedback where appropriate.

---

## Tests

Use Vitest and React Testing Library. Do not make network calls in component tests.

Minimum tests:

1. Login page renders email/password fields and sign-in action.
2. Invalid login displays a generic error.
3. Protected route redirects to `/login` without authenticated user state.
4. Assessment list displays API data.
5. Assessment list renders an empty state.
6. Observation table renders source/status chips.
7. Promote action is disabled until observation status is `CONFIRMED`.
8. Triage dialog requires a note for false positive.
9. App shell hides raw-observation navigation/actions for a Client role.

Use mocked API modules or Axios adapter mocks. Do not test Material UI internals.

---

## Manual verification

After implementation:

```bash
cd frontend
npm run lint        # only if a lint script is configured
npm run test -- --run
npm run build
npm run dev
```

Then manually verify in the browser:

1. Login as `consultant@sarp.local`.
2. Open an accessible Assessment.
3. Navigate through Assets, Imports, Observations and Findings.
4. Filter observations to `ZAP` and then `Nessus`.
5. Open an Observation, confirm it, then promote it.
6. Confirm the created Finding detail loads.
7. Sign out and confirm protected routes return to Login.
8. Test a Manager and Client user if seeded; confirm UI is less permissive, while direct API access remains protected server-side.

Run backend regression tests as well:

```bash
docker compose exec backend python manage.py test
```

---

## Definition of done

Day 7 is done when:

- A clean frontend install builds successfully.
- All frontend smoke tests pass.
- Existing backend tests still pass.
- A Consultant can complete the supported workflow using live API data:

```text
Login → Assessment → Observation → Confirm → Promote → Finding
```

- The app does not expose tokens, raw scanner reports, raw Burp traffic, or technical error details.
- The UI has consistent loading, empty, error, success and disabled states.
- The design is simple, professional and responsive.

---

## Commit plan

Create small, reviewable commits:

```text
feat: scaffold react material ui application shell
feat: add jwt login and protected assessment workspace
feat: add observation triage and finding promotion interface
test: add frontend auth and workflow smoke tests
```

Do not commit frontend `.env`, `node_modules`, test coverage output, or generated build artifacts.
