# Day 5 Implementation Brief: Native Nessus `.nessus` Import

## Starting point

Day 4 is complete, committed, pushed, and verified. The working tree must be clean before new work begins.

Day 1–4 currently provide:

- Dockerised Django + PostgreSQL/pgvector, JWT authentication, health endpoint and tests.
- Client-scoped tenancy, roles, Assessments, Assets and Findings.
- Server-derived Finding severity from CVSS.
- `apps/imports` with safe parser/service separation.
- Safe Nmap XML import through `import_scan --tool nmap`.
- Safe OWASP ZAP Traditional JSON import through `import_scan --tool zap`.
- Tenant-scoped read APIs for imports and observations.
- Consultant triage (`NEW`, `CONFIRMED`, `FALSE_POSITIVE`, `DUPLICATE`, `PROMOTED`).
- Promotion of a confirmed observation into one Finding with a `FindingSource` link.
- 58 passing tests at the end of Day 4.

Run these commands before touching code:

```bash
git status
git log --oneline -8
git diff --check
docker compose exec backend python manage.py test
```

Do not change existing Day 1–4 behaviour unless a change is explicitly required below. Nmap and ZAP tests must continue passing.

---

## Objective

Add support for importing an **authorised native Tenable Nessus `.nessus` XML scan export**.

```text
Authorised Consultant imports `.nessus` file
        ↓
SARP parses host and ReportItem data safely
        ↓
SARP creates or matches an in-scope host Asset
        ↓
SARP creates or re-observes deduplicated Nessus ScannerObservations
        ↓
Consultant uses the existing triage flow
        ↓
Confirmed observation uses the existing promotion flow
        ↓
FindingSource preserves traceability to the Nessus observation
```

The Nessus importer must fit the existing `BaseImporter → NormalisedObservation → import service` architecture. It must not rewrite the existing Nmap or ZAP workflows.

---

## Strict scope

### Build today

1. `NessusXmlImporter` for native `.nessus` XML files only.
2. Add `nessus` as a supported `--tool` value to the existing `import_scan` command.
3. Add one fictional `.nessus` fixture covering a host and multiple ReportItems.
4. Match/create Assets by IP address and hostname within the selected Assessment only.
5. Extract safe, structured Nessus metadata into `ScannerObservation` records.
6. Add Nessus-specific deduplication and re-observation coverage.
7. Reuse the existing Day 4 triage and promotion workflow without redesigning it.
8. Add parser, import service, command, privacy, tenancy, deduplication and regression tests.
9. Update API documentation only where existing output has new fields required for Nessus visibility.

### Explicit exclusions

- No browser upload endpoint or React UI.
- No direct scanner execution, target entry, scheduling, scanner credentials or scanner API integration.
- No CSV, JSON, HTML or PDF Nessus/Tenable import today.
- No Burp importer.
- No new RAG, AI, CVE enrichment, Azure, audit-log model, background worker or report export.
- No automatic creation of Findings during import.
- No automatic false-positive decision, duplicate merge, risk acceptance or closure decision.
- No raw `.nessus` file persistence or raw report download.
- No storage of full `plugin_output`, credentials, tokens, passwords, hashes, cookies, raw requests/responses, or arbitrary scanner diagnostic content.
- No external network calls to Tenable, NVD, CISA or EPSS.

---

## Native `.nessus` input contract

Support native `.nessus` XML only.

Expected high-level structure:

```text
NessusClientData_v2
  └── Report
        └── ReportHost
              ├── HostProperties
              │     └── tag
              └── ReportItem
```

Relevant fields to parse when present:

| Nessus source | SARP use |
|---|---|
| `ReportHost@name` | hostname/display-name candidate |
| `HostProperties/tag[name="host-ip"]` | primary IPv4/IPv6 Asset identity candidate |
| `HostProperties/tag[name="host-fqdn"]` | hostname Asset identity candidate |
| `ReportItem@pluginID` | `scanner_plugin_id` and fingerprint component |
| `ReportItem@pluginName` | observation title |
| `ReportItem@severity` | `raw_severity` only |
| `ReportItem@port`, `@protocol`, `@svc_name` | safe location and fingerprint components |
| `ReportItem/cve` | normalised CVE IDs |
| `ReportItem/cwe` | normalised CWE IDs |
| `ReportItem/cvss3_base_score`, then `cvss_base_score` | candidate metadata only; never final Finding severity |
| `ReportItem/cvss3_vector`, then `cvss_vector` | optional safe metadata if the current model supports it; otherwise do not redesign today |
| `ReportItem/synopsis`, `description` | sanitised, length-bounded description |
| `ReportItem/solution` | sanitised, length-bounded suggested remediation |
| `ReportItem/see_also` | sanitised, length-bounded references metadata if supported |
| `ReportItem/plugin_output` | **do not persist raw content** |

The parser must handle absent optional fields. A missing CVE, CVSS, port, service or solution must not crash the import.

### Supported file validation

- Accept `.nessus` extension only, case-insensitively.
- Reuse `MAX_IMPORT_FILE_SIZE_BYTES`; reject before parsing.
- Use `defusedxml` only. Do not use `xml.etree.ElementTree`, `lxml`, or any unsafe XML parser for report input.
- Reject `DOCTYPE`, external entities, malformed XML and wrong root structures with `ImportValidationError` and a safe user-facing message.
- Require at least one `ReportHost` with at least one `ReportItem`; otherwise return a safe validation error.
- Never log raw XML content or parser stack traces.

---

## Safe Nessus data handling

Nessus reports can contain detailed diagnostic information. For this project, keep only safe operational metadata needed for triage.

### Store

- Host IP and/or hostname.
- Plugin ID, plugin name, raw severity, protocol, port and service name.
- CVE IDs, CWE IDs and candidate CVSS score when supplied.
- Sanitised synopsis/description and solution, subject to existing text limits.
- A generated safe evidence summary.
- A calculated location such as `10.10.10.15:443/tcp (https)`.

### Do not store

- Raw `plugin_output`.
- Credential-related tags, scan settings, target lists outside the selected assessment context, scanner host metadata, tokens, passwords, secrets, hashes or raw system command output.
- Raw XML bytes.
- Full nested diagnostic content simply because it appears in the report.

### Safe evidence summary

Generate a concise deterministic summary; do not copy raw `plugin_output`.

Example:

```text
Nessus plugin 42873 reported "SSL Medium Strength Cipher Suites Supported" on 10.10.10.15:443/tcp (https).
```

This is enough for a Consultant to triage the item while reducing the risk of retaining sensitive host diagnostics.

### Text sanitisation

Reuse existing sanitisation helpers where possible:

- Strip HTML tags.
- Collapse whitespace.
- Enforce length limits.
- Treat scanner text as untrusted plain text.
- Do not render it with `dangerouslySetInnerHTML` later.

---

## Asset matching and creation

Use the existing `Asset` model. Do not redesign the schema unless a current required field makes safe Nessus import impossible.

For every `ReportHost`, use this identity order within the selected Assessment:

1. Exact `ip_address` match from `host-ip`, when present.
2. Case-insensitive exact `hostname` match using `host-fqdn` or `ReportHost@name`.
3. If no match exists, create a host/server Asset with:
   - `ip_address` when valid.
   - `hostname` when safe and present.
   - `display_name` = hostname, otherwise IP address.
   - the existing host/server asset type choice.

Rules:

- Never match an Asset outside the selected Assessment.
- Never create a blank or unusable Asset.
- One report with multiple ReportItems for the same host must reuse one Asset.
- A re-import must reuse the same Asset.
- IPv6 addresses must not crash parsing or matching; support them if the existing `Asset.ip_address` field supports them, otherwise reject/skip the individual malformed identity safely and document the limitation.

---

## Normalised observation contract

Use the existing `NormalisedObservation` contract. Add optional fields only when required for Nessus, and give them safe defaults so Nmap and ZAP parsers remain backward compatible.

Recommended Nessus data supplied by the parser:

```python
NormalisedObservation(
    source_tool="NESSUS",
    external_id="nessus:<host>:<protocol>:<port>:<plugin_id>",
    title=plugin_name,
    raw_severity=normalised_nessus_severity,
    description=sanitised_description,
    suggested_remediation=sanitised_solution,
    evidence_summary=generated_safe_summary,
    scanner_plugin_id=plugin_id,
    cve_ids=[...],
    cwe_ids=[...],
    affected_location="10.10.10.15:443/tcp (https)",
    asset_hostname=...,
    asset_ip_address=...,
    protocol=...,
    port=...,
    service_name=...,
    candidate_cvss_score=...,
)
```

Adapt property names to the established codebase rather than duplicating fields. The important rule is that the parser returns structured data and does not save database records.

### Nessus severity mapping

Map the numeric `ReportItem@severity` to a scanner/raw severity only:

```text
0 → INFORMATIONAL
1 → LOW
2 → MEDIUM
3 → HIGH
4 → CRITICAL
```

If the numeric value is absent or unsupported, use a safe `UNKNOWN`/empty raw severity according to existing model choices; do not invent a final Finding severity.

The candidate CVSS score must not bypass the existing promotion rule. When a Consultant promotes an observation, they must still supply/review the CVSS score through the existing promotion flow, and the server derives Finding severity.

### CVE and CWE normalisation

- Extract all CVE IDs from repeated elements or delimited text.
- Normalise to upper-case `CVE-YYYY-NNNN...` format.
- Deduplicate while preserving stable order.
- Extract/normalise CWE IDs to `CWE-<number>`.
- Ignore malformed values safely rather than failing the complete report.

---

## Nessus fingerprint and deduplication

Nessus re-runs must update the existing observation rather than create duplicates.

Build a stable fingerprint from:

```text
assessment ID + NESSUS + normalised host identity + protocol + port + plugin ID
```

Example conceptual fingerprint input:

```text
assessment=12 | tool=NESSUS | asset=10.10.10.15 | protocol=tcp | port=443 | plugin=42873
```

Do not include volatile text such as plugin output, timestamps, scan name or report filename.

Expected re-import behaviour:

- A new `ScanImport` is created for each command run.
- An existing matching `ScannerObservation` is re-observed.
- `last_seen_at` / `last_seen_import` update using established Day 3 conventions.
- A new `ScanImportObservation` history link is created.
- The Asset is reused.
- No duplicate `ScannerObservation`, Asset or Finding is created.
- Existing triage status is preserved. Re-importing a `CONFIRMED`, `FALSE_POSITIVE`, `DUPLICATE` or `PROMOTED` observation must not reset it to `NEW`.

Do not merge different plugin IDs automatically, even when titles or CVEs are similar.

---

## Existing triage and promotion integration

Do not rewrite Day 4 triage or promotion endpoints.

The Day 5 importer must produce observations that work with these existing actions:

```text
POST /api/v1/observations/{id}/triage/
POST /api/v1/observations/{id}/promote/
```

Rules remain:

- Only Admin or an assigned Consultant can triage or promote within an authorised Assessment.
- Client users cannot see raw imports or observations.
- Managers remain read-only.
- A Nessus observation is `NEW` after first import.
- It can be marked `CONFIRMED`, `FALSE_POSITIVE` or `DUPLICATE` using existing rules.
- Only a `CONFIRMED` observation may be promoted.
- Promotion creates one Finding and one `FindingSource` link.
- A `PROMOTED` observation cannot be promoted or triaged again.

---

## Management command

Extend the existing command; do not create a parallel command.

```bash
python manage.py import_scan \
  --assessment-id 1 \
  --tool nessus \
  --file fixtures/nessus/sample.nessus \
  --actor-email consultant@sarp.local
```

Rules:

- `--tool nessus` must work alongside existing `nmap` and `zap`.
- Unknown tool errors remain safe and do not list internal details.
- Keep `--actor-email` only for this trusted local management command.
- Do not add actor email to browser/API requests.
- Report created/re-observed counters using the established command output style.

---

## Required fixture

Create:

```text
backend/fixtures/nessus/sample.nessus
```

It must be fully fictional and safe to commit. Use a test-only host, for example `10.10.10.15` / `training-server.local`.

Include at least:

1. Two ReportItems on the same host with different plugin IDs.
2. One item containing a valid CVE and CVSS field.
3. One item with no CVE to prove optional metadata handling.
4. One `plugin_output` value containing clearly fake sensitive-looking data, such as `token=should-not-persist`, so tests prove it is excluded.
5. Host properties with `host-ip` and `host-fqdn`.

Do not include real target names, credentials, customer data, raw scanner results or production IPs.

---

## Required tests

Use fixtures and existing test helpers. Tests must be deterministic and make no external calls.

### Parser tests

- Valid `.nessus` fixture produces the expected number of normalised observations.
- Plugin ID, title, host, port/protocol, service, raw severity, CVE and CWE extraction works.
- Candidate CVSS extraction works when present.
- Missing optional fields do not crash parsing.
- Wrong extension, blank file, oversized input, malformed XML, `DOCTYPE` and entity payloads fail with safe `ImportValidationError`.
- Wrong root / no usable `ReportHost` / no `ReportItem` fails safely.
- Parser does not persist any models.
- Raw `plugin_output` and fake token values do not appear in parser output.
- Sanitised description/solution text is bounded and plain text.

### Import-service tests

- An assigned Consultant imports the fictional `.nessus` file into an assigned Assessment.
- One Asset is created/reused for the host.
- Expected `ScannerObservation` records are created with source `NESSUS`.
- `ScanImport` counters and SHA-256 checksum are stored.
- Re-import creates a second `ScanImport`, re-observes existing observations and creates history links without duplicates.
- Existing triage status is preserved across re-import.
- No Finding is created automatically.
- Admin can import for any Client.
- Unassigned Consultant cannot import into another Client’s Assessment.
- Unknown/invalid Assessment and unsupported tool fail safely.

### API and workflow regression tests

- Authorised Consultant can list only their Client’s Nessus imports/observations.
- Manager can read authorised observations but cannot triage/promote.
- Client user cannot list raw imports/observations.
- Existing observation filtering by `source_tool=NESSUS` works if the Day 4 filter supports it.
- Confirming a Nessus observation and promoting it uses the existing promotion flow successfully.
- Promotion derives Finding severity using existing server logic and does not trust raw Nessus severity.
- Nmap and ZAP tests remain green.

---

## Expected file changes

Adapt exact paths to the existing repository. Likely changes include:

```text
backend/apps/imports/parsers/nessus.py                  # new parser
backend/apps/imports/parsers/__init__.py                # only if the project uses registry exports
backend/apps/imports/parsers/base.py                    # optional backward-compatible NormalisedObservation fields
backend/apps/imports/services/import_service.py         # route NESSUS + asset/fingerprint support
backend/apps/imports/management/commands/import_scan.py # add --tool nessus validation/help
backend/apps/imports/tests/test_parser_nessus.py        # new
backend/apps/imports/tests/test_day5_nessus_workflow.py # new or focused existing test file
backend/apps/imports/tests/test_management_command.py   # extend
backend/fixtures/nessus/sample.nessus                   # new fictional fixture
backend/requirements/base.txt                            # only if a dependency is genuinely needed; none should be needed beyond defusedxml
backend/apps/imports/migrations/...                     # only if model schema actually needs a field
backend/docs or docs/project-knowledge/...              # copy the handoff docs into repo knowledge
```

Do not add a migration merely because this document lists migrations as a possible path. Prefer existing flexible observation metadata if it already supports the fields.

---

## Definition of done

Day 5 is complete when:

1. `import_scan --tool nessus` imports the fictional `.nessus` fixture for an authorised Consultant.
2. Assets are matched/created safely in the selected Assessment only.
3. Nessus ReportItems become tenant-scoped `ScannerObservation` records, not automatic Findings.
4. Plugin IDs, CVEs, candidate CVSS, protocol/port/service and safe remediation data are captured.
5. Raw plugin output and fake secret material are not persisted.
6. Re-import deduplicates and records re-observation history without resetting triage state.
7. Existing triage and promotion work for a Nessus observation.
8. Cross-client import and read access is denied.
9. Nmap, ZAP and all existing tests remain green.
10. Changes are committed in small, logical commits and pushed only after full verification.

---

## Required verification

Run and report exact results for:

```bash
docker compose up --build -d
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations imports
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py test apps.imports apps.findings
docker compose exec backend python manage.py test
git diff --check
```

### Manual smoke test

Use a fictional local Assessment and authorised Consultant:

```bash
docker compose exec backend python manage.py import_scan \
  --assessment-id 1 \
  --tool nessus \
  --file fixtures/nessus/sample.nessus \
  --actor-email consultant@sarp.local
```

Then verify:

- The command reports created/re-observed counts.
- `GET /api/v1/imports/?source_tool=NESSUS` returns only authorised records.
- `GET /api/v1/observations/?source_tool=NESSUS` returns expected observations for an authorised Consultant.
- Confirm one observation and promote it with a CVSS score through the existing endpoints.
- The resulting Finding uses server-derived severity.
- Re-run the command and confirm no duplicate Asset or ScannerObservation appears.

Never print JWTs, passwords, raw report contents or sensitive test output in the final summary.

---

## Suggested commits

```text
feat: add native nessus report importer
feat: support nessus asset matching and observation deduplication
test: cover nessus parsing privacy and import workflow
```
