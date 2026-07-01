# SARP Ambitious Codex Pack v2

## Purpose
This is the source-of-truth planning pack for **Secure Assessment & Risk Management Platform (SARP)**.

SARP is an AI-assisted, multi-tenant vulnerability-management platform. It does **not** launch scans. It imports authorised scanner exports from Nmap, Nessus, OWASP ZAP and Burp Suite; normalises their observations; allows consultant triage; tracks approved findings and remediation; enriches CVEs; and provides a secure dashboard for managers and client users.

## Current project state
Day 1 is complete and verified:

- Docker Compose starts the Django API and PostgreSQL/pgvector.
- Email-based JWT login, refresh, `/auth/me/`, and `/health/` work.
- Six authentication tests pass.
- `.env` is ignored by Git.
- Day 1 changes must be committed before new development begins.

## Read order for Codex
1. `01_MASTER_BUILD_PLAN.md`
2. `02_PRODUCT_AND_ARCHITECTURE.md`
3. `03_DIRECTORY_STRUCTURE.md`
4. `04_SECURITY_AND_RBAC.md`
5. `05_SCANNER_IMPORT_SPEC.md`
6. `06_AI_RAG_AND_DECISION_SUPPORT.md`
7. `07_AZURE_AND_CICD.md`
8. `08_CODEX_WORKING_CONTRACT.md`
9. `09_DAY_02_IMPLEMENTATION_BRIEF.md`
10. `10_DAY_02_CODEX_PROMPT.md`

## Scope boundary
A user may import reports only for systems they own or have explicit permission to assess. SARP is an import, triage and remediation-management system, not an unrestricted scanner.

## Non-negotiable product principles
- Backend permissions are the security boundary.
- All tenancy filters happen server-side.
- Scanner observations are not automatically treated as confirmed vulnerabilities.
- AI provides recommendations and drafts only; a human decides triage, risk acceptance, remediation approval and closure.
- Never store passwords, tokens, unredacted HTTP requests/responses, or real client data in sample fixtures.
- Build a working vertical slice and tests before optional advanced features.
