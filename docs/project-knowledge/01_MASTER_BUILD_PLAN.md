# SARP Ambitious 10-Day Build Plan

## Outcome at Day 10
A Consultant can create an authorised assessment, import Nmap, Nessus, ZAP or Burp reports, review scanner observations, promote confirmed observations to Findings, use AI-assisted remediation and evidence-based prioritisation, and track remediation. Managers see risk posture. Client users see only their approved client data. The app runs locally in Docker and has Azure deployment evidence or a reproducible runbook.

## Scope priorities

### Mandatory core
- JWT authentication and multi-tenant RBAC.
- Client, Assessment, Asset, Finding, ScanImport and ScannerObservation domain models.
- Nmap XML and ZAP JSON importers.
- Observation triage and promotion to Finding.
- Audit logging.
- React operational UI.
- Docker, tests, STRIDE, CI, README and demo.

### Advanced target
- Nessus `.nessus` importer.
- Burp XML importer.
- CVE enrichment with NVD data, CISA KEV flag and EPSS score.
- Explainable priority scoring.
- pgvector-backed RAG remediation drafts with visible sources.
- AI false-positive and duplicate-review recommendations.
- Assessment/Finding copilot chat constrained to authorised data.
- Azure deployment and optional Azure OpenAI provider.

### Cut order if time becomes tight
1. Azure OpenAI live provider.
2. AI chat.
3. Embedding-based duplicate suggestions.
4. Burp importer.
5. Nessus importer.

Never cut tenancy, import validation, audit logs, core tests, local Docker demo or documentation.

## Day-by-day plan

### Day 1 — Complete: platform foundation
**Already delivered:** Docker Compose, PostgreSQL/pgvector image, custom email user, JWT auth, health endpoint, auth tests, local `.env` handling.

**First next action:** commit Day 1 using the commands in `09_DAY_02_IMPLEMENTATION_BRIEF.md`.

### Day 2 — Tenancy, risk domain and assets
Build Client, ClientMembership, Assessment, Asset and Finding. Enforce client-scoped querysets. Add CVSS validation and derived severity. Write tests for cross-client access denial.

**Gate:** do not begin React until tenant isolation tests pass.

### Day 3 — Import engine and Nmap XML
Build ScanImport, ScannerObservation, FindingSource, a BaseImporter interface and Nmap XML parser. Add import management command and import preview API.

**Gate:** Nmap observations must not automatically become Findings.

### Day 4 — ZAP, Nessus and Burp parsers
Add ZAP JSON first, then Nessus `.nessus`, then Burp XML if time allows. Use realistic but fictional fixtures. Redact sensitive evidence.

### Day 5 — Triage and remediation lifecycle
Add observation statuses, promotion to Finding, duplicate linking, risk acceptance, remediation checklists, validation evidence and audit logs.

### Day 6 — React operational workflow
Build Login, Dashboard, Assessments, Assets, Import Console, Observation Triage and Finding Detail. Deliver an end-to-end browser flow for at least Nmap and ZAP.

### Day 7 — CVE intelligence and explainable priority
Add cached VulnerabilityIntel enrichment. Compute priority from CVSS, KEV, EPSS, asset criticality, Internet exposure and overdue status. Show reasons for the result.

### Day 8 — RAG remediation assistant
Add curated knowledge documents, chunking, pgvector similarity search, AI artifacts and a source panel. Use MockProvider for tests and Ollama locally.

### Day 9 — AI analyst assistance and CI/security
Add approval-gated false-positive and duplicate recommendations, constrained AI chat if core features are stable, file safety controls, XML parser hardening, rate limiting, CORS, CI and STRIDE.

### Day 10 — Azure and portfolio packaging
Deploy or document deployment to Azure; complete README, diagrams, screenshots, demo video, security test report and release tag.

## Milestone demos

### Demo 1: Day 3
Create an assessment and import Nmap XML. Confirm assets and observations are stored.

### Demo 2: Day 6
Import ZAP report in the browser, mark one observation false positive, promote one to Finding, assign remediation owner.

### Demo 3: Day 8
Generate a RAG-grounded remediation draft for the confirmed Finding and show retrieved sources.

### Demo 4: Day 10
Show CI, tenant isolation test, Azure deployment/runbook and short end-to-end workflow.
