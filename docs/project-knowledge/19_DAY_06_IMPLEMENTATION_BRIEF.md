# Day 6 Implementation Brief: Burp Suite XML Issue Import

## Starting point

Day 5 is complete, committed, pushed and verified. The project currently has:

- Dockerised Django + PostgreSQL/pgvector, JWT authentication, health endpoint and passing tests.
- Client-scoped tenancy with Admin, Consultant, Manager and Client-user roles.
- Assessments, Assets, Findings and server-derived Finding severity from CVSS.
- A shared scan-import architecture: `BaseImporter → NormalisedObservation → import service`.
- Safe Nmap XML import, ZAP Traditional JSON import and native Nessus `.nessus` XML import.
- Tenant-scoped read APIs for imports and observations.
- Shared observation triage (`NEW`, `CONFIRMED`, `FALSE_POSITIVE`, `DUPLICATE`, `PROMOTED`).
- Promotion of confirmed observations into Findings with `FindingSource` traceability.
- 71 passing backend tests at the end of Day 5.

Run this before changing code:

```bash
git status
git log --oneline -10
git diff --check
docker compose exec backend python manage.py test
```

Do not start implementation unless the working tree is clean and the baseline suite passes.

---

## Objective

Add support for importing an **authorised Burp Suite Professional XML “Export Issue Data” report**.

```text
Authorised Consultant exports selected Burp issues as XML
        ↓
SARP safely parses only allowed issue metadata
        ↓
SARP creates or reuses an in-scope web application Asset
        ↓
SARP creates or re-observes deduplicated Burp ScannerObservations
        ↓
Consultant uses the existing triage workflow
        ↓
Confirmed observation uses the existing promotion workflow
        ↓
FindingSource preserves the link to the Burp observation
```

SARP does not run Burp, accept Burp project files, execute attacks, or store raw HTTP traffic.

---

## Why Burp needs a slightly different XML strategy

The existing Nmap and Nessus importers use `defusedxml` and reject DOCTYPE declarations. Keep that unchanged.

Burp’s XML issue-data export includes an **internal DTD**. Therefore, using the existing “reject every DOCTYPE” rule would reject normal Burp exports. For Burp only, use a hardened `lxml` parser configuration that:

```python
etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
    dtd_validation=False,
    huge_tree=False,
    recover=False,
    remove_comments=True,
)
```

Add `lxml` as a backend dependency using the project’s existing requirements style.

### Required safeguards

Before parsing, inspect the XML declaration/DOCTYPE safely and reject input containing:

- An external DTD reference (`SYSTEM` or `PUBLIC`).
- Entity declarations (`<!ENTITY`).
- Parameter entity declarations or references.
- A non-`issues` root document.
- Oversized files, malformed XML, or a document with no `<issue>` records.

Accept only Burp’s expected internal structural DTD declarations; do not load, validate, fetch, resolve or expand any DTD content.

Use streaming parsing (`iterparse`) or element clearing so completed `<issue>` elements are released promptly. Never log raw XML, parse errors containing report data, or HTTP messages.

---

## Strict scope

### Build today

1. `BurpXmlImporter` for Burp XML issue-data exports only.
2. Add `burp` as a supported `--tool` value to the existing `import_scan` command.
3. Add a fictional Burp XML fixture.
4. Match or create web application Assets from canonical origins, scoped to the selected Assessment.
5. Extract safe metadata into `ScannerObservation` records.
6. Add Burp-specific deduplication and re-observation coverage.
7. Reuse the existing Day 4 triage and promotion workflow exactly as it is.
8. Add parser, privacy, service, command, tenancy, deduplication and regression tests.
9. Update source-tool documentation/API labels only where necessary.

### Explicit exclusions

- No browser upload endpoint, React page, direct Burp execution, scanner scheduling or scanner credentials.
- No Burp project-file import (`.burp`) and no Logger CSV import.
- No HTML/PDF report parsing.
- No Nmap, ZAP or Nessus behaviour change except adding `burp` to the shared tool registry.
- No raw request, raw response, base64 HTTP message, cookie, authorization header, bearer token, password, API key, body, screenshot, Collaborator data or payload storage.
- No direct CVE enrichment, RAG, AI, Azure, audit model, background worker, report export or external calls.
- No automatic Finding creation, triage decision, duplicate merge, risk acceptance, remediation action or closure.
- No raw XML persistence or raw report download endpoint.

---

## Supported input contract

Support only Burp’s XML **Export Issue Data** report, normally generated from Burp Suite Professional.

Expected high-level shape:

```text
issues
  └── issue (one or more)
        ├── type
        ├── name
        ├── host
        ├── path
        ├── location
        ├── severity
        ├── confidence
        ├── issueBackground
        ├── remediationBackground
        └── requestresponse (must be ignored)
```

Field names may vary in casing across compatible Burp exports. Parse by local tag name safely and tolerate absent optional fields.

### Store only these safe fields

| Burp source | SARP use |
|---|---|
| `type` | `scanner_plugin_id` when present; otherwise use normalised issue name |
| `name` | Observation title |
| `host` | Canonical application origin candidate |
| `path` | Canonical path/location component |
| `location` | Parameter/location metadata after sanitisation |
| `severity` | `raw_severity` only |
| `confidence` | Safe source metadata for analyst review |
| `issueBackground` | Sanitised description, length-bounded |
| `remediationBackground` | Sanitised suggested remediation, length-bounded |
| `references` or classification text | Sanitised optional metadata if current model supports it |

### Never store or expose these fields

| Burp source | Rule |
|---|---|
| `requestresponse` | Ignore completely; do not load into normalised data |
| `request` / `response` | Ignore completely |
| `raw`, `base64`, encoded content | Ignore completely |
| HTTP headers/cookies/authentication | Ignore completely |
| Request and response body content | Ignore completely |
| Payloads, credentials, session IDs, tokens, PII | Ignore completely |

A source file may contain HTTP message data. SARP must neither persist nor return that data. The imported report remains under the local operator’s control; SARP stores only its derived safe records.

---

## URL and Asset handling

Burp findings are web-application findings. Use the existing `Asset` model, scoped to the selected Assessment.

### Canonical origin

Create a safe canonical origin:

```text
scheme://hostname[:non-default-port]
```

Examples:

```text
https://portal.example.test
https://portal.example.test:8443
http://10.10.10.20:8080
```

Do not include a query string, fragment, user-info section, credentials or path in the Asset base URL.

### Canonical path

For the ScannerObservation’s safe location, retain only:

```text
HTTP method if present + path + safe parameter/location name
```

Examples:

```text
GET /api/invoices/{id}
POST /account/reset [email]
/api/users/{id} [id]
```

Rules:

- Strip query strings and fragments.
- Reject/omit malformed hosts or unsupported URL schemes.
- Treat `http` and `https` as distinct origins.
- Reuse an existing Asset by exact canonical `base_url` within the selected Assessment.
- Never match or create Assets outside the selected Assessment.
- When no usable origin can be formed, reject that individual issue with a counted safe error; do not crash the whole report unless every issue is unusable.

---

## Normalised observation contract

Reuse the existing `NormalisedObservation` structure. Add optional safe metadata only when the current codebase needs it, with defaults so Nmap, ZAP and Nessus remain compatible.

Recommended Burp output from the parser:

```python
NormalisedObservation(
    source_tool="BURP",
    external_id="burp:<origin>:<path>:<plugin_or_name>:<location>",
    title=issue_name,
    raw_severity=normalised_burp_severity,
    description=sanitised_issue_background,
    suggested_remediation=sanitised_remediation_background,
    evidence_summary=generated_safe_summary,
    scanner_plugin_id=issue_type_or_normalised_name,
    affected_location=canonical_path_location,
    asset_base_url=canonical_origin,
    source_metadata={"confidence": normalised_confidence},
)
```

Adapt field names to the established codebase. Parsers return structured data only; they never write database records.

### Severity and confidence

Map Burp severity to raw scanner severity only:

```text
High         → HIGH
Medium       → MEDIUM
Low          → LOW
Information  → INFORMATIONAL
Unknown/blank → INFORMATIONAL or existing safe default
```

Store Burp confidence only as non-authoritative metadata:

```text
Certain / Firm / Tentative / Unknown
```

Burp severity and confidence must never automatically set the final Finding’s reviewed CVSS score, final severity, remediation state or business impact.

### Safe evidence summary

Generate a short deterministic summary from safe fields. Do not copy a raw request or response.

Example:

```text
Burp reported "Insecure direct object references" at https://portal.example.test/api/invoices/{id} with High severity and Firm confidence.
```

---

## Deduplication and re-import rules

Build a Burp-specific stable fingerprint from:

```text
assessment ID
+ source tool BURP
+ canonical origin
+ canonical path
+ scanner plugin/type (or normalised issue name)
+ normalised location/parameter
```

Rules:

- Same fingerprint in the same Assessment: re-observe existing `ScannerObservation`; do not create another one.
- Re-import must update import history/last-seen information without resetting `triage_status`, notes, duplicate links or promoted state.
- Same issue in another Assessment is independent.
- Same issue against another origin/host is independent.
- An observation promoted to a Finding must not create another Finding on re-import.
- Reuse the shared import service and its existing `ScanImportObservation` history records.

Do not automatically merge Burp observations into ZAP observations. Cross-tool similarity can become a later analyst-assistance feature; today the Consultant remains responsible for any merge decision.

---

## Permission and API rules

Reuse existing tenant selectors and permissions.

| Action | Admin | Assigned Consultant | Assigned Manager | Client user |
|---|---:|---:|---:|---:|
| Import Burp XML with management command | Yes | Yes | No | No |
| List Burp imports/observations | Yes | Yes | Read-only if existing policy permits | No raw visibility |
| Triage Burp observation | Yes | Yes | No | No |
| Promote confirmed Burp observation | Yes | Yes | No | No |

For the local management command, `--actor-email` is acceptable because the command runs in a trusted local/container context. A future browser upload endpoint must derive the actor from `request.user`, never a client-supplied email.

Existing APIs must remain tenant-scoped. A user must never retrieve an Import, Observation, linked Asset, or promoted Finding belonging to another Client by changing an ID.

---

## Required fixture

Create a fictional fixture:

```text
backend/fixtures/burp/sample-issues.xml
```

The fixture must be safe and fictional, and include:

1. A High-confidence or Firm-confidence IDOR-style issue at a fictional HTTPS application URL.
2. A second, distinct low/medium issue at another path on the same origin.
3. A query string and fragment in an input URL to prove canonicalisation removes them.
4. A `requestresponse` section containing clearly fake unsafe values, for example:

```text
Authorization: Bearer should-not-persist
Cookie: session=should-not-persist
password=should-not-persist
```

5. An internal DTD consistent with exported Burp issue-data XML, but no external DTD and no entity declaration.

Tests must prove that none of the fake sensitive strings are stored in `ScannerObservation`, `ScanImport`, API output or logs.

---

## Test plan

### Parser tests

- Valid Burp XML returns the expected number of `NormalisedObservation` values.
- Internal structural DTD is accepted without network access or entity resolution.
- External `SYSTEM`/`PUBLIC` DTD references are rejected.
- Entity declarations and parameter entities are rejected.
- Blank, malformed, oversized, wrong-root and no-issue reports fail with safe `ImportValidationError` messages.
- Query strings/fragments are removed from canonical locations.
- Request/response sections, base64 strings and fake tokens are never included in parser output.
- HTML is stripped, whitespace collapsed and text limits enforced.
- Parser itself never persists database records.

### Import service tests

- Burp import creates/reuses one application Asset for multiple issues on the same origin.
- Two valid fixture issues create two Burp ScannerObservations.
- Re-import creates history/re-observations, not duplicate Assets or Observations.
- Triage state is preserved across re-import.
- A promoted observation does not create another Finding during re-import.
- Existing Nmap, ZAP and Nessus behaviour remains unchanged.

### Privacy tests

- Fake Authorization header, Cookie, token, password and response body strings are absent from every persisted model field and API serializer response.
- Raw XML is never persisted.
- `requestresponse` is ignored rather than copied as evidence.

### Permission/regression tests

- An unassigned Consultant cannot import into another Client’s Assessment.
- Manager and Client user cannot import, triage or promote.
- Client user cannot list raw Burp observations/imports.
- Existing triage validation remains enforced:
  - false positives require a note;
  - duplicates refer to an observation in the same Assessment;
  - self-duplicates are rejected;
  - promoted observations cannot be triaged or promoted again.

---

## Manual smoke test

Create or use a fictional assessment assigned to `consultant@sarp.local`.

```bash
docker compose exec backend python manage.py import_scan \
  --assessment-id 1 \
  --tool burp \
  --file fixtures/burp/sample-issues.xml \
  --actor-email consultant@sarp.local
```

Confirm:

1. The import completes successfully.
2. Two Burp observations are created.
3. One web application Asset is created/reused.
4. No fake token/cookie/password appears in the API output.
5. An authorised Consultant can confirm one observation and promote it through the existing endpoint.
6. Promotion creates one Finding with consultant-reviewed CVSS and server-derived severity.
7. Re-import reports observations as re-observed; it creates no duplicate Asset, Observation or Finding.

Do not print JWTs or real credentials in terminal output or documentation.

---

## Required commands

```bash
docker compose up --build -d
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations imports
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py test apps.imports apps.findings
docker compose exec backend python manage.py test
git diff --check
```

Run focused tests while implementing, then the full suite before committing.

---

## Definition of done

Day 6 is complete only when:

- A fictional Burp XML issue-data export imports through the existing management command with `--tool burp`.
- Internal Burp structural DTD input is accepted safely without entity/network resolution.
- External DTDs, entities, malformed XML, oversized files and wrong formats fail safely.
- Safe application Assets and deduplicated Burp `ScannerObservation` records are created within the selected Assessment only.
- Raw HTTP messages, headers, cookies, tokens, passwords, payloads and response bodies are never persisted or exposed.
- Existing triage/promotion logic works without a Burp-specific rewrite.
- Re-import preserves triage state and does not duplicate Findings.
- Tenant isolation remains enforced.
- Nmap, ZAP, Nessus and full backend tests still pass.
- The working tree is clean after commits and changes are pushed.

---

## Suggested commits

```text
feat: add secure burp issue xml importer
feat: support burp web asset matching and observation deduplication
test: cover burp xml privacy and import workflow
```

---

## Reference note

Burp Suite Professional supports XML issue-data export for importing issue information into other tools. Its XML output includes an internal DTD and can include Base64-encoded request/response data; SARP deliberately ignores all HTTP message material and stores only safe derived metadata.

Official reference:

- https://portswigger.net/burp/documentation/desktop/running-scans/reporting/report-settings
