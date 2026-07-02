# Ready-to-Paste Codex Prompt: Day 4

You are continuing the SARP portfolio project in the existing repository.

Read these documents first:

1. `docs/project-knowledge/01_MASTER_BUILD_PLAN.md`
2. `docs/project-knowledge/03_DIRECTORY_STRUCTURE.md`
3. `docs/project-knowledge/04_SECURITY_AND_RBAC.md`
4. `docs/project-knowledge/05_SCANNER_IMPORT_SPEC.md`
5. `docs/project-knowledge/08_CODEX_WORKING_CONTRACT.md`
6. `docs/project-knowledge/15_DAY_04_IMPLEMENTATION_BRIEF.md`

Day 1–3 are complete, committed and pushed. Day 3 implemented the secure Nmap XML import foundation. Start by running:

```bash
git status
git log --oneline -6
git diff --check
docker compose exec backend python manage.py test
```

Do not change product code until the starting working tree is clean and the full test suite passes.

## Day 4 objective

Implement **OWASP ZAP Traditional JSON Report import** plus the first analyst triage and promotion workflow.

An authorised Admin or Consultant assigned to the Assessment’s Client must be able to:

1. Import a fictional ZAP Traditional JSON report with the existing `import_scan` management command.
2. Create or match a web Application Asset.
3. Create deduplicated ZAP `ScannerObservation` records.
4. Confirm, reject as false positive, or mark an observation as a duplicate.
5. Promote one confirmed observation into exactly one SARP Finding by supplying a CVSS score and business context.
6. Preserve a `FindingSource` link from the Finding to the original ScannerObservation.

## Strict scope

Implement only what `15_DAY_04_IMPLEMENTATION_BRIEF.md` specifies.

- Support ZAP **Traditional JSON** only.
- Add `--tool zap` to the existing command.
- Add no browser upload endpoint, React page, target input, scanner execution, scheduler, Nessus, Burp, RAG, AI, CVE enrichment, Azure or audit-log model.
- Do not store raw report bytes, HTTP requests/responses, cookies, tokens, query values, payloads, ZAP `attack`, `evidence` or `otherinfo` fields.
- Do not auto-create Findings during import.
- Do not implement Accepted Risk today.

## Technical requirements

- Add `ZapJsonImporter` under the existing parser structure.
- Parsers return `NormalisedObservation` values only. No parser writes database records.
- Reuse the existing import service for hashing, permissions, persistence and deduplication.
- Enforce the existing file-size setting before parsing.
- Reject malformed JSON, wrong extensions, bad report shape and reports containing raw request/response message data with safe `ImportValidationError` errors.
- Use canonical URLs with query strings/fragments removed.
- Create one observation per ZAP alert instance.
- Use raw ZAP risk only as `raw_severity`; never set the final Finding severity from ZAP.
- Add a triage service and promotion service. Keep views thin.
- Promotion requires a consultant-supplied `cvss_score`; existing server logic derives final Finding severity.
- Promotion must be transactional and must reject second promotion attempts.
- Browser action endpoints must use `request.user`; never accept an actor email from request data.
- Preserve tenant isolation through scoped querysets and existing tenancy selectors.

## Required endpoints

```text
POST /api/v1/observations/{id}/triage/
POST /api/v1/observations/{id}/promote/
```

Use the exact request payloads, state transitions, permissions, model additions and tests in the Day 4 implementation brief.

## Working method

Before code, list affected files and give a 3–6 bullet plan.

Implement in small milestones. After each milestone, run focused tests. Do not replace unrelated files. Use type hints in parser/service code. Add migrations and fixtures. Keep all test data fictional.

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

At completion provide:

1. Concise change summary.
2. Exact migration(s) created.
3. Commands run and results.
4. Manual ZAP import and API smoke-test commands.
5. Known limitations.
6. Suggested commits:

```text
feat: add zap report import and observation triage
feat: promote confirmed scanner observations to findings
test: cover zap parsing privacy triage and promotion
```
