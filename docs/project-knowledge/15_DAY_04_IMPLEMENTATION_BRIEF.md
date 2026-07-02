# Day 4 Implementation Brief: ZAP JSON Import and Observation Triage

## Starting point

Day 3 is complete, committed and pushed. The working tree should be clean before implementation begins.

Day 3 already provides:

- `apps/imports` and the generic import service.
- `ScanImport`, `ScannerObservation`, `ScanImportObservation`, and `FindingSource` models.
- Safe Nmap XML import through `import_scan`.
- Tenant-scoped read APIs for imports and observations.
- Asset matching, observation deduplication, and re-observation history.
- A strict rule that imported observations do not automatically create Findings.

Run these first:

```bash
git status
git log --oneline -6
git diff --check
docker compose exec backend python manage.py test
```

Do not modify Day 1–3 behaviour except where a change is explicitly required below.

---

## Objective

Add a second importer for **OWASP ZAP Traditional JSON Reports** and implement the first complete analyst workflow:

```text
Authorised Consultant imports ZAP JSON
        ↓
SARP creates or matches a web Application Asset
        ↓
SARP creates canonical ScannerObservations
        ↓
Consultant reviews and triages each observation
        ↓
Confirmed observation is promoted into one tracked Finding
        ↓
FindingSource preserves the link back to the ZAP observation
```

This gives SARP its first end-to-end flow from a scanner report to a real risk-management Finding.

---

## Scope

### Build today

1. `ZapJsonImporter` for the **Traditional JSON Report** format only.
2. Extend `import_scan` so it accepts `--tool zap`.
3. A fictional ZAP Traditional JSON fixture.
4. URL-based web asset matching/creation.
5. Observation triage service and write endpoints.
6. Promotion service and endpoint that creates a Finding from a confirmed observation.
7. Tests for parsing, privacy controls, tenant permissions, triage and promotion.

### Explicit exclusions

- No browser upload endpoint or React page.
- No direct scanner execution, target entry or scanner scheduling.
- No ZAP SARIF, XML or `traditional-json-plus` support.
- No Nessus or Burp parser.
- No RAG, AI, CVE enrichment, Azure, background jobs or audit-log model today.
- No automatic false-positive decision, duplicate merging or automatic Finding creation.
- No raw HTTP requests, responses, cookies, tokens, passwords, attack payloads or scanner report bytes stored in SARP.
- No Accepted Risk approval workflow today. That needs an approver and a documented rationale, so defer it.

---

## ZAP input contract

Support only the ZAP **Traditional JSON Report** structure:

```text
site[]
  └── alerts[]
        └── instances[]
```

The parser must use these documented fields when present:

| ZAP field | SARP mapping |
|---|---|
| `site.@name`, `@host`, `@port`, `@ssl` | web Application Asset candidate |
| `alert` / `name` | `NormalisedObservation.title` |
| `pluginid` / `alertRef` | `scanner_plugin_id` / stable external ID |
| `riskcode`, `riskdesc` | `raw_severity` |
| `confidence` | `confidence` |
| `desc` | sanitised `description` |
| `solution` | sanitised `suggested_remediation` |
| `reference` | sanitised, length-bounded references text/list |
| `cweid` | `cwe_ids` |
| `instances[].uri` | canonical observation URL/location |
| `instances[].param` | location/fingerprint component |
| `instances[].method` | safe evidence summary component |
| `instances[].nodeName` | safe evidence summary component |

### One observation per alert instance

A ZAP alert can contain multiple affected URLs/parameters. Create one `NormalisedObservation` for each instance, not one per alert. This preserves the real affected location and makes deduplication accurate.

### Severity mapping

Use ZAP's documented risk values as a **raw scanner severity only**:

```text
0 → INFORMATIONAL
1 → LOW
2 → MEDIUM
3 → HIGH
```

If `riskcode` is unavailable, infer the first recognised label from `riskdesc` (`Informational`, `Low`, `Medium`, `High`). Never invent `CRITICAL` for a ZAP alert.

The final SARP Finding severity remains server-derived from a consultant-supplied CVSS score during promotion. Do not let ZAP risk overwrite the existing Finding severity rule.

---

## Privacy and security rules

ZAP reports can contain payloads, query values and, in extended formats, raw HTTP messages. Treat them as sensitive.

### Must store

- Alert title, plugin ID and raw severity.
- Canonicalised web URL: scheme, host, optional port and path.
- Parameter name only, when available.
- HTTP method and safe node name, length-bounded.
- Sanitised description, remediation and reference information.
- CWE IDs where present.

### Must not store

- `attack` field.
- `evidence` field.
- `otherinfo` field.
- Raw HTTP request or response data.
- Query-string values, fragments, cookies, bearer tokens, credentials or payloads.
- Raw JSON report bytes.

### Required protections

- Reuse `MAX_IMPORT_FILE_SIZE_BYTES` from Day 3; reject oversized input before parsing.
- Only accept `.json` files for ZAP today.
- Decode as UTF-8 and convert decoding/JSON errors to `ImportValidationError` with safe messages.
- Require a top-level JSON object with a `site` list; reject structurally invalid reports safely.
- Reject reports containing raw request/response message fields associated with the `traditional-json-plus` format. The safe error should say that reports with raw HTTP messages are unsupported.
- Strip HTML tags from `desc`, `solution` and `reference`; do not render scanner text as HTML.
- Use existing evidence-length/sanitisation helpers where appropriate. Create a focused utility only if none exists.
- Do not log report content or parser exceptions.

### URL canonicalisation

For a URL such as:

```text
https://training-web.local:8443/search?q=<payload>#fragment
```

store and fingerprint using:

```text
https://training-web.local:8443/search
```

Keep the parameter name separately (`q`) if supplied. Query values and fragments must not be stored.

---

## Asset matching

Use the existing `Asset` model. Do not redesign its schema unnecessarily.

For each ZAP site:

1. Build a canonical base URL from `@name` when valid; otherwise from `@ssl`, `@host` and `@port`.
2. Match an existing Asset in the same Assessment by canonical `base_url`.
3. If none exists, create a web-application Asset using the project’s existing asset-type choice. Use a clear display name based on the host.
4. Never match or create an Asset outside the selected Assessment.

The same ZAP site imported twice must reuse the same Asset.

---

## Fingerprint and external ID

Use a stable ZAP fingerprint based on:

```text
assessment ID + source tool + canonical URL path + alert/plugin ID + parameter name
```

Example conceptual input:

```text
assessment=12 | tool=ZAP | url=https://training-web.local/search | alert=40012 | param=q
```

Hash it using the existing Day 3 fingerprint approach.

`external_id` must be human-readable and stable, for example:

```text
zap:40012:https://training-web.local/search:param:q
```

Re-importing the same observation must create a new `ScanImport`, update the canonical observation’s `last_seen_at` and `last_seen_import`, and create a `ScanImportObservation` history record. It must not create a duplicate observation or Asset.

---

## Triage model changes

Extend `ScannerObservation` only as needed for the first review workflow.

### Supported statuses today

```text
NEW             Imported but not reviewed.
CONFIRMED       Consultant verified it needs risk tracking.
FALSE_POSITIVE  Consultant determined it is not a real issue in context.
DUPLICATE       It is represented by another observation in the same Assessment.
PROMOTED        A confirmed observation has been converted into a Finding.
```

Do not enable `ACCEPTED_RISK` yet.

### Required metadata

Add fields only if missing:

```text
triage_note          nullable, safe, length-bounded text
triaged_by           nullable User FK
triaged_at           nullable datetime
duplicate_of         nullable self-FK
```

### State rules

- `NEW` can become `CONFIRMED`, `FALSE_POSITIVE` or `DUPLICATE`.
- `DUPLICATE` requires a `duplicate_of_id` for an observation in the same Assessment; it cannot point to itself.
- `FALSE_POSITIVE` requires a non-empty review note.
- `CONFIRMED` may be promoted.
- `PROMOTED` cannot be triaged again through this endpoint.
- No automatic duplicate selection or merge occurs.

Use a service layer, not view logic, to validate and perform transitions.

---

## Promotion to Finding

Create a `promote_observation_to_finding(...)` service. It must only promote a `CONFIRMED` observation.

### Endpoint

```text
POST /api/v1/observations/{id}/promote/
```

### Required request body

```json
{
  "cvss_score": 7.5,
  "business_impact": "An attacker could execute script in a user session.",
  "remediation_owner": "Web Platform Team",
  "due_date": "2026-07-20"
}
```

### Optional request fields

```json
{
  "title": "Optional consultant-edited title",
  "description": "Optional consultant-edited description",
  "remediation": "Optional consultant-edited remediation"
}
```

### Promotion rules

- Require an affected Asset. ZAP imports should have one; otherwise fail safely.
- Create a new Finding under the observation’s Assessment.
- Use the supplied CVSS score. The existing model/service must derive final Finding severity server-side from that score.
- Use safe observation fields as defaults:
  - title → observation title
  - description → observation description
  - remediation → suggested remediation
  - asset → observation asset
- Set `created_by` to the authenticated actor.
- Create one `FindingSource` linking the new Finding and the ScannerObservation.
- Set observation status to `PROMOTED`, set `triaged_by`/`triaged_at`, and retain the original observation.
- Promotion must be atomic. A failure must not leave an orphan Finding or a partly-updated observation.
- Reject second promotion attempts safely; do not create a duplicate Finding.

This preserves the Day 2 rule: scanner risk is evidence, but a Consultant owns the final CVSS and business-context decision.

---

## API endpoints

Keep existing read-only endpoints intact. Add these write actions:

```text
POST /api/v1/observations/{id}/triage/
POST /api/v1/observations/{id}/promote/
```

### Triage request examples

Confirm:

```json
{
  "triage_status": "CONFIRMED",
  "triage_note": "Reproduced in the authorised training application."
}
```

False positive:

```json
{
  "triage_status": "FALSE_POSITIVE",
  "triage_note": "The header is added by the production reverse proxy."
}
```

Duplicate:

```json
{
  "triage_status": "DUPLICATE",
  "duplicate_of_id": 42,
  "triage_note": "Same alert and URL as the existing observation."
}
```

### Authorisation

- Admin: may import, triage and promote for any Client.
- Assigned Consultant: may import, triage and promote only in assigned Clients.
- Manager: read-only. Must receive `403` for triage and promotion.
- Client user: cannot view raw imports/observations or use actions. Existing read behaviour remains blocked.
- Unauthenticated: `401`.
- Unauthorised detail access: normally `404` through scoped querysets.

Never use a client-supplied actor email in browser endpoints. Use `request.user`.

---

## Required files

Expected additions/changes include:

```text
backend/
├── apps/imports/
│   ├── parsers/zap.py
│   ├── services/import_service.py
│   ├── services/triage_service.py
│   ├── services/promotion_service.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── tests/
│       ├── test_parser_zap.py
│       ├── test_import_service.py
│       ├── test_triage_service.py
│       ├── test_promotion_service.py
│       └── test_api_permissions.py
├── fixtures/zap/traditional-report.json
└── docs/project-knowledge/
    └── 15_DAY_04_IMPLEMENTATION_BRIEF.md
```

Adapt names if the Day 3 layout already has a consistent alternative. Do not replace unrelated modules.

---

## Required tests

### ZAP parser tests

- Valid fictional traditional JSON report parses expected sites, alerts and instances.
- One alert with two instances creates two `NormalisedObservation` objects.
- Invalid JSON, wrong extension, blank content and missing/invalid `site` list fail with safe `ImportValidationError` messages.
- Oversized input is rejected using the configured limit.
- Traditional JSON Plus/raw HTTP message input is rejected safely.
- HTML is stripped from description, solution and reference content.
- Attack, evidence, other-info and query payload values are never present in a persisted observation.
- Query strings and fragments are removed from stored URLs/fingerprints.
- Parser writes no database records.

### Import and persistence tests

- Assigned Consultant imports ZAP fixture into an assigned Assessment.
- Matching web Asset is created once and reused on re-import.
- Correct plugin ID, CWE, raw severity, confidence, canonical URL and suggested remediation are stored.
- Re-import updates observation history and `last_seen_at` without creating duplicates.
- ZAP import never creates a Finding.
- Unassigned Consultant, Manager and Client user cannot import.

### Triage and promotion tests

- Assigned Consultant can confirm an observation.
- False positive requires a non-empty note.
- Duplicate requires a different observation in the same Assessment.
- Cross-assessment duplicate target is rejected.
- Manager and Client user cannot triage or promote.
- Confirmed observation can be promoted using a supplied CVSS score.
- Promotion creates one Finding and one FindingSource.
- The promoted Finding severity is derived from CVSS, not copied from ZAP severity.
- Promotion uses the observation Asset and safe defaults.
- Promotion is atomic and cannot run twice.
- Existing tenant-scoped list/detail API behaviour still passes.

---

## Manual smoke test

After migrations and fixtures are available:

```bash
docker compose exec backend python manage.py import_scan \
  --assessment-id 1 \
  --tool zap \
  --file fixtures/zap/traditional-report.json \
  --actor-email consultant@sarp.local
```

Then, using a valid JWT for an assigned Consultant:

```text
1. GET /api/v1/observations/?source_tool=ZAP
2. POST /api/v1/observations/{id}/triage/ with CONFIRMED
3. POST /api/v1/observations/{id}/promote/ with cvss_score and business impact
4. GET /api/v1/findings/{new_id}/
```

Expected result:

```text
ZAP report import → observation → confirmed → one Finding → FindingSource traceability
```

---

## Commands and acceptance criteria

Run at minimum:

```bash
docker compose up --build -d
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations imports
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py test apps.imports apps.findings
docker compose exec backend python manage.py test
git diff --check
```

Day 4 is done only when:

- Nmap import remains functional.
- ZAP Traditional JSON imports through the existing command.
- No raw ZAP payloads/messages are persisted.
- A Consultant can triage an observation through the API.
- A confirmed ZAP observation can be promoted exactly once into a Finding with consultant-provided CVSS.
- Tenant isolation tests pass.
- Full backend tests pass.
- Work is committed with a clean working tree.

### Suggested commits

```text
feat: add zap report import and observation triage
feat: promote confirmed scanner observations to findings
test: cover zap parsing privacy triage and promotion
```

---

## Reference note

The supported fixture must follow ZAP’s Traditional JSON Report shape: `site[]`, `alerts[]`, and alert `instances[]`. Do not implement other report shapes today.
