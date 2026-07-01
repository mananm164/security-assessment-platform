You are implementing Day 2 of SARP.

Read these documents first:
- docs/project-knowledge/README.md
- docs/project-knowledge/02_PRODUCT_AND_ARCHITECTURE.md
- docs/project-knowledge/03_DIRECTORY_STRUCTURE.md
- docs/project-knowledge/04_SECURITY_AND_RBAC.md
- docs/project-knowledge/08_CODEX_WORKING_CONTRACT.md
- docs/project-knowledge/09_DAY_02_IMPLEMENTATION_BRIEF.md

Current state:
- Day 1 Docker, PostgreSQL/pgvector, custom email User, JWT auth, health endpoint and auth tests are verified.
- Day 1 changes have not yet been committed.

First, inspect the current repository and commit the verified Day 1 work in logical commits. Confirm `.env` is not tracked.

Then implement only Day 2:
- Client, ClientMembership, Assessment, Asset and Finding models.
- Reusable server-side tenant-scoping helper/service.
- Client-scoped DRF list/detail/create/update APIs.
- Role rules: Admin full access; Consultant only assigned Clients and can edit; Manager assigned Clients read-only; Client user own Client read-only.
- CVSS validation and server-derived severity.
- Assessment/Asset validation.
- Tests for validation and cross-client BOLA/IDOR denial.

Constraints:
- Do not create React, imports, scanner parsers, upload API, AI, RAG, CVE enrichment, Azure files, delete endpoints or advanced dashboards.
- Do not weaken permissions merely to make tests easier.
- Keep views thin and put reusable domain logic in services/helpers.
- Use fictional seed/test data only.
- Prefer inaccessible-object `404` through scoped querysets.
- Do not modify unrelated Day 1 auth behaviour.

Before writing code, reply with:
1. Current relevant repository structure.
2. Affected files.
3. A 3–6 step plan.
4. Tests you will add.

After coding:
1. Run migrations.
2. Run focused tests and the full backend test suite.
3. State exact commands and outcomes.
4. Give manual API verification steps.
5. State limitations/follow-ups.
6. Provide suggested commit commands/messages.
