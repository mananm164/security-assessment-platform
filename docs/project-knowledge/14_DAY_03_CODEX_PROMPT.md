# Ready-to-Paste Codex Prompt: Day 3

You are continuing the SARP portfolio project in the existing repository. Read these documents first:

1. `docs/project-knowledge/01_MASTER_BUILD_PLAN.md`
2. `docs/project-knowledge/03_DIRECTORY_STRUCTURE.md`
3. `docs/project-knowledge/04_SECURITY_AND_RBAC.md`
4. `docs/project-knowledge/05_SCANNER_IMPORT_SPEC.md`
5. `docs/project-knowledge/08_CODEX_WORKING_CONTRACT.md`
6. `docs/project-knowledge/13_DAY_03_IMPLEMENTATION_BRIEF.md`

Day 1 and Day 2 are implemented and verified. Day 2 is currently uncommitted.

## First: commit the verified Day 2 work

Before changing product code:

1. Run `git status`, `git log --oneline -8`, `git diff --stat`, `git diff --check`, and `git ls-files .env`.
2. Commit the verified Day 2 tenancy, assessments, assets and findings work using logical commits. Preserve `.env` as untracked.
3. Run the full backend tests before beginning Day 3.

Do not create artificial commits if shared files contain inseparable Day 1/Day 2 changes. In that situation, make one accurate, well-scoped baseline commit and state exactly what it contains.

## Day 3 objective

Implement a secure scanner-import foundation with **Nmap XML only**.

An authorised Admin or Consultant assigned to an Assessment's Client must be able to import a fictional Nmap XML report using a Django management command. SARP must create or match Assets and create deduplicated `ScannerObservation` records. Nmap observations must never automatically create `Finding` records.

## Scope to implement

Create `apps/imports` and implement:

- `ScanImport`
- `ScannerObservation`
- `ScanImportObservation`
- `FindingSource` schema only; no promote-to-finding workflow yet
- `NormalisedObservation` dataclass
- `BaseImporter`
- `NmapXmlImporter`
- Import service that owns permission checks and persistence
- `import_scan` management command
- Read-only, tenant-scoped import/observation API endpoints
- Fictional Nmap XML fixture
- Tests

Use the exact model responsibilities, parser contract, import workflow, access rules and acceptance criteria in `13_DAY_03_IMPLEMENTATION_BRIEF.md`.

## Security and architecture rules

- Add and use `defusedxml`. Do not parse Nmap XML with the standard XML parser directly.
- Parser classes return normalised data only. They never write database records.
- The import service checks `can_write_client_records(actor, assessment.client)` before it creates records.
- The management command must require `--actor-email`; commands do not bypass tenant permissions.
- No raw XML report bytes may be saved to the database, logs, errors, or audit metadata.
- Apply a configurable 5 MiB input-size limit.
- Reject blank, malformed, wrong-extension and unsafe XML with safe domain errors.
- Use scoped querysets for every import/observation API endpoint. Unauthorised detail reads should normally return 404.
- No delete endpoints.
- No target entry, scanner execution, uploads, React, AI, RAG, ZAP, Nessus, Burp, CVE enrichment, Azure or audit-log implementation today.
- Use fictional fixture data only.

## Required command interface

```bash
python manage.py import_scan \
  --assessment-id 1 \
  --tool nmap \
  --file fixtures/nmap/sample.xml \
  --actor-email consultant@sarp.local
```

Only `nmap` is accepted today.

## Required tests

Add tests for:

- Valid Nmap parsing: host, open port and NSE script result.
- Unsafe XML/DOCTYPE/entity rejection using `defusedxml`.
- Safe validation errors for malformed input.
- Evidence sanitisation and truncation.
- Parser does not persist database records.
- Asset matching and no duplicate Asset on re-import.
- Re-import creates a new `ScanImport`, updates an existing canonical observation's `last_seen_at`, and creates import-history links without duplicate observations.
- No `Finding` created during Nmap import.
- Assigned Consultant can import; unassigned Consultant, Manager and Client User cannot.
- Tenant-scoped imports/observations list and detail endpoints.
- Client Users cannot read raw imports or observations.
- Management command safe failures for unknown user, assessment and tool.

## Working method

Before code, list affected files and give a 3–6 bullet plan.

Implement in small milestones. After each milestone, run focused tests. Do not replace unrelated files. Do not add dependencies beyond those necessary for this brief. Use type hints in the service/parser layer. Keep views thin.

At completion, provide:

1. A concise change summary.
2. Exact migrations created.
3. Commands run and their results.
4. Manual smoke-test command.
5. Any known limitations.
6. Suggested commits:

```text
feat: add secure nmap scan import foundation
test: cover nmap parsing import deduplication and tenant isolation
```
