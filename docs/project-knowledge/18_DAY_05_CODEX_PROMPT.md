# Ready-to-Paste Codex Prompt: Day 5

You are continuing the SARP portfolio project in the existing repository.

Read these documents first:

1. `docs/project-knowledge/01_MASTER_BUILD_PLAN.md`
2. `docs/project-knowledge/03_DIRECTORY_STRUCTURE.md`
3. `docs/project-knowledge/04_SECURITY_AND_RBAC.md`
4. `docs/project-knowledge/05_SCANNER_IMPORT_SPEC.md`
5. `docs/project-knowledge/08_CODEX_WORKING_CONTRACT.md`
6. `docs/project-knowledge/17_DAY_05_IMPLEMENTATION_BRIEF.md`

Day 1–4 are complete, committed and pushed. Day 4 implemented safe ZAP Traditional JSON import, observation triage, and promotion to Findings. Start by running:

```bash
git status
git log --oneline -8
git diff --check
docker compose exec backend python manage.py test
```

Do not change product code until the working tree is clean and the full test suite passes.

## Day 5 objective

Implement import of an authorised **native Tenable Nessus `.nessus` XML export**.

An Admin or Consultant assigned to the Assessment’s Client must be able to:

1. Import a fictional `.nessus` report using the existing `import_scan` management command and `--tool nessus`.
2. Create or match one host Asset by IP address/hostname inside the selected Assessment.
3. Create deduplicated Nessus `ScannerObservation` records from `ReportItem` elements.
4. Preserve scan history during re-import without resetting existing triage states.
5. Use the existing triage endpoint to confirm an observation.
6. Use the existing promotion endpoint to create a Finding with server-derived severity.

## Strict scope

Implement only `17_DAY_05_IMPLEMENTATION_BRIEF.md`.

- Support native `.nessus` XML only.
- Add `--tool nessus` to the existing command.
- Reuse the established `BaseImporter → NormalisedObservation → import service` architecture.
- Reuse existing Day 4 triage and promotion services/endpoints. Do not redesign them.
- Add no browser upload endpoint, React page, direct scanner execution, scanner scheduling, Burp importer, AI/RAG, CVE enrichment, Azure, background worker, audit model, CSV/JSON/PDF support, or external API calls.
- Do not auto-create Findings during import.
- Do not store raw report bytes, raw XML, full `plugin_output`, scanner credentials, tokens, passwords, secrets, hashes, raw commands, or diagnostic blobs.

## Technical requirements

- Implement `NessusXmlImporter` in the existing parser structure.
- Use `defusedxml` only for `.nessus` input. Reject malformed XML, entity/DOCTYPE input, wrong root structures and unusable reports with safe `ImportValidationError` messages.
- Enforce the existing file-size limit before parsing and accept `.nessus` extension only.
- Parsers return structured `NormalisedObservation` values only; parsers never write database records.
- Extract only safe fields: host IP/FQDN/name, plugin ID/name, raw severity, protocol, port, service, CVE IDs, CWE IDs, candidate CVSS, sanitised description, sanitised solution and a generated safe evidence summary.
- Generate the evidence summary; never persist raw `plugin_output`.
- Build a Nessus fingerprint from assessment + tool + normalised host + protocol + port + plugin ID.
- On re-import, reuse the Asset and ScannerObservation, update re-observation history, and preserve the observation triage status.
- Never let raw Nessus severity or candidate CVSS bypass the existing promotion flow or server-derived Finding severity logic.
- Preserve tenant isolation in every command, service, selector and API path.
- Keep existing Nmap and ZAP behaviour/tests passing.

## Required fixture

Create a fictional safe fixture:

```text
backend/fixtures/nessus/sample.nessus
```

It must include a test host, two different plugin findings, one valid CVE/CVSS example, one no-CVE example, and a fake `plugin_output` secret such as `token=should-not-persist` to prove that raw plugin output is never stored.

## Working method

Before code, list affected files and give a 3–6 bullet plan.

Implement in small milestones. Run focused tests after each milestone. Do not replace unrelated files. Use type hints in parser/service code. Add only necessary migrations. Keep fixtures fictional and make no external network calls.

## Required verification

Run:

```bash
docker compose up --build -d
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations imports
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py test apps.imports apps.findings
docker compose exec backend python manage.py test
git diff --check
```

Perform a manual import using the documented command in the Day 5 brief. Confirm a Nessus observation and promote it with the existing API. Re-import the same report and confirm no duplicate Asset, Observation or Finding is created.

At completion provide:

1. Concise change summary.
2. Exact migration(s) created, or explicitly state none were required.
3. Commands run and results.
4. Manual Nessus import and API smoke-test commands/results.
5. Privacy protections applied to `plugin_output` and other diagnostic data.
6. Known limitations.
7. Suggested commits:

```text
feat: add native nessus report importer
feat: support nessus asset matching and observation deduplication
test: cover nessus parsing privacy and import workflow
```
