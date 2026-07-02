# Ready-to-Paste Codex Prompt: Day 6

You are continuing the SARP portfolio project in the existing repository.

Read these documents first:

1. `docs/project-knowledge/01_MASTER_BUILD_PLAN.md`
2. `docs/project-knowledge/03_DIRECTORY_STRUCTURE.md`
3. `docs/project-knowledge/04_SECURITY_AND_RBAC.md`
4. `docs/project-knowledge/05_SCANNER_IMPORT_SPEC.md`
5. `docs/project-knowledge/08_CODEX_WORKING_CONTRACT.md`
6. `docs/project-knowledge/19_DAY_06_IMPLEMENTATION_BRIEF.md`

Day 1–5 are complete, committed and pushed. The app currently supports secure import of Nmap XML, ZAP Traditional JSON and Nessus `.nessus` reports, plus shared observation triage and promotion to Findings.

Start with:

```bash
git status
git log --oneline -10
git diff --check
docker compose exec backend python manage.py test
```

Do not edit product code until the working tree is clean and the baseline test suite passes.

## Day 6 objective

Implement import of an authorised **Burp Suite Professional XML “Export Issue Data” report**.

An Admin or Consultant assigned to an Assessment’s Client must be able to:

1. Import a fictional Burp XML issue-data report using the existing `import_scan` management command and `--tool burp`.
2. Create or match a canonical web application Asset inside the selected Assessment.
3. Create deduplicated Burp `ScannerObservation` records from safe issue metadata.
4. Re-import the same report without duplicating Assets, Observations or Findings, and without resetting triage state.
5. Reuse the existing triage endpoint to confirm an observation.
6. Reuse the existing promotion endpoint to create a Finding with consultant-reviewed CVSS and server-derived severity.

## Critical security constraint

Burp XML may contain raw HTTP requests/responses, cookies, bearer tokens, passwords, payloads, personal data and response bodies. SARP must never store, return, log or render any of that material.

Store only safe, structured issue metadata:

- issue type/name;
- canonical origin and path;
- parameter/location name after sanitisation;
- raw scanner severity;
- confidence;
- sanitised issue/remediation text;
- generated safe evidence summary.

Ignore all `requestresponse`, `request`, `response`, raw/base64 HTTP content, headers, cookies and bodies.

## XML parsing constraint

Keep the existing `defusedxml` parser approach unchanged for Nmap and Nessus.

Burp XML exports include an internal DTD, so use a hardened `lxml` parser for Burp only. Configure it with:

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

Add `lxml` as a backend dependency consistent with the existing requirements approach.

Before parsing, reject XML that contains:

- external `SYSTEM` or `PUBLIC` DTD references;
- `<!ENTITY` declarations;
- parameter entities;
- malformed/oversized XML;
- a non-`issues` root;
- no `<issue>` records.

Use streaming parsing or clear completed issue elements. Do not log raw XML or parser errors containing report data.

## Strict scope

Implement only `19_DAY_06_IMPLEMENTATION_BRIEF.md`.

- Add `BurpXmlImporter` and `--tool burp` to the established import architecture.
- Reuse existing models/services/triage/promotion wherever possible.
- Add a fictional fixture at `backend/fixtures/burp/sample-issues.xml`.
- Add parser, privacy, import, command, tenancy, deduplication and regression tests.
- Preserve Nmap, ZAP and Nessus behaviour.

Do not add a browser upload endpoint, React UI, direct scanner execution, Burp project file import, Burp Logger CSV import, HTML/PDF parsing, CVE enrichment, AI/RAG, Azure, audit model, worker, report export or external API calls.

Do not auto-create Findings during import. Do not auto-triage, auto-merge or auto-close anything.

## Required technical rules

- Support Burp XML **Export Issue Data** only.
- Parsers return `NormalisedObservation` objects only; parsers never write to the database.
- Build the fingerprint from assessment + `BURP` + canonical origin + canonical path + issue type/name + location/parameter.
- Canonical origin is `scheme://hostname[:non-default-port]`; do not include user info, query string, fragment or path.
- Canonical observation location excludes query strings/fragments.
- Asset reuse must occur only within the selected Assessment.
- `http` and `https` origins are distinct.
- Burp severity/confidence remain scanner metadata only; they must not bypass existing reviewed-CVSS and server-derived Finding-severity rules.
- Re-import must retain existing triage status, triage notes, duplicate links and promoted state.
- Existing tenant protections must apply in command, services, selectors and APIs.

## Required fixture

Create a fictional safe XML fixture containing:

1. One High/Firm IDOR-style issue at a fictional HTTPS application.
2. One distinct Low/Medium issue at another path on the same origin.
3. A URL with query string and fragment to prove canonicalisation.
4. A `requestresponse` section containing these fake strings:

```text
Authorization: Bearer should-not-persist
Cookie: session=should-not-persist
password=should-not-persist
```

5. An internal structural DTD, but no external DTD and no entity declaration.

Tests must prove every fake sensitive string is absent from persisted models and API responses.

## Working method

Before code, list affected files and provide a 3–6 bullet plan.

Implement in small milestones. Run focused tests after each milestone. Do not replace unrelated files. Use type hints in parser/service code. Add migrations only when truly necessary. Keep data fictional and make no external calls.

## Required verification

```bash
docker compose up --build -d
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations imports
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py test apps.imports apps.findings
docker compose exec backend python manage.py test
git diff --check
```

Perform the manual import command in the Day 6 brief. Confirm and promote an authorised Burp observation through the existing APIs. Re-import and confirm no duplicate Asset, Observation or Finding is created.

At completion provide:

1. Concise change summary.
2. Exact migration(s) created, or explicitly state none were required.
3. Commands run and results.
4. Manual Burp import and API smoke-test commands/results.
5. Privacy protections and proof that HTTP messages/tokens were excluded.
6. Known limitations.
7. Suggested commits:

```text
feat: add secure burp issue xml importer
feat: support burp web asset matching and observation deduplication
test: cover burp xml privacy and import workflow
```
