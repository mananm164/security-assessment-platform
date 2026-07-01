# Day 2 Implementation Brief: Tenancy, Assessments, Assets and Findings

## Objective
Build the secure domain foundation for report imports. At the end of Day 2, Consultants can create Assessments and Assets under assigned Clients and create Findings only within those clients. Other users cannot access another tenant's records.

## Step 0: Commit Day 1 verified work

Inspect before staging:

```bash
git status
git diff --stat
git ls-files .env
```

Then make milestone commits. Adjust paths only if the repository layout differs.

```bash
git add backend docker-compose.yml .env.example .gitignore README.md
git commit -m "feat: add dockerised django jwt authentication"

git add backend/apps/accounts/tests
git commit -m "test: add authentication endpoint coverage"
```

If files are already staged differently, do not force the exact commands. Preserve logical commits and confirm `.env` remains untracked.

## Scope

Create these backend apps if absent:

```text
apps/tenancy
apps/assessments
apps/findings
apps/audit
apps/common
```

Do not create scanner parsers, React, AI, RAG, upload endpoints, Azure resources or CVE enrichment today.

## Models

### Client

```text
name (unique)
industry
contact_name
contact_email
created_at
```

### ClientMembership

```text
user → accounts.User
client → tenancy.Client
relationship_role: CONSULTANT | MANAGER | CLIENT_USER
is_active
created_at
unique(user, client)
```

### Assessment

```text
client → tenancy.Client
name
framework: ISO_27001 | NIST | OWASP | NIS2 | OTHER
status: PLANNED | ACTIVE | COMPLETED | ARCHIVED
start_date
end_date
scope_summary
created_by → accounts.User
created_at
```

### Asset

```text
assessment → Assessment
asset_type: HOST | APPLICATION | API | DATABASE | CLOUD_RESOURCE | OTHER
display_name
hostname (optional)
ip_address (optional)
base_url (optional)
environment: DEVELOPMENT | TEST | STAGING | PRODUCTION | UNKNOWN
criticality: LOW | MEDIUM | HIGH | CRITICAL
internet_exposed: bool
owner (optional)
created_at
```

Validate that an Asset has at least one useful identifier: hostname, IP address, base URL or display name.

### Finding

```text
assessment → Assessment
affected_asset → Asset (optional)
title
description
cve_id (optional for now)
cvss_score: Decimal, 0.0 to 10.0
severity: derived field
business_impact
remediation
remediation_owner
status: OPEN | IN_PROGRESS | ACCEPTED_RISK | MITIGATED | CLOSED
due_date
created_by → accounts.User
created_at
updated_at
```

Derived severity rule:

```text
0.0                  → INFORMATIONAL
0.1–3.9              → LOW
4.0–6.9              → MEDIUM
7.0–8.9              → HIGH
9.0–10.0             → CRITICAL
```

Do not trust severity from API input. Compute it server-side whenever CVSS changes.

## Permissions

| Action | Admin | Consultant | Manager | Client User |
|---|---:|---:|---:|---:|
| Create Client | Yes | No | No | No |
| View Client/Assessment/Asset/Finding | All | Assigned Clients | Assigned Clients | Own Client only |
| Create Assessment/Asset/Finding | Yes | Assigned Clients | No | No |
| Update Assessment/Asset/Finding | Yes | Assigned Clients | No | No |
| Delete | No MVP delete endpoints | No | No | No |

Implement a reusable service/queryset helper for visible clients. Do not copy/paste tenant filtering into every view.

## Initial API endpoints

```text
GET/POST   /api/v1/clients/
GET/PATCH  /api/v1/clients/{id}/
GET/POST   /api/v1/assessments/
GET/PATCH  /api/v1/assessments/{id}/
GET/POST   /api/v1/assets/
GET/PATCH  /api/v1/assets/{id}/
GET/POST   /api/v1/findings/
GET/PATCH  /api/v1/findings/{id}/
```

List endpoints must be paginated and tenant scoped. Query filters may be minimal today, e.g. `assessment`, `status`, `severity`.

## Required tests

### Model/serializer validation
- Invalid CVSS less than 0 or greater than 10 rejected.
- Severity derives correctly at boundaries 0.0, 0.1, 3.9, 4.0, 6.9, 7.0, 8.9, 9.0, 10.0.
- Assessment end date before start date rejected.
- Asset without any usable identifier rejected.

### Permissions / tenant isolation
Create:

```text
Admin
Consultant A assigned to Client A
Consultant B assigned to Client B
Manager A assigned to Client A
Client User A assigned to Client A
```

Test:

- Consultant A lists only Client A records.
- Consultant A cannot retrieve/update Client B Assessment, Asset or Finding.
- Manager A can read but cannot create/update.
- Client User A can read only Client A data and cannot write.
- Admin can access both Client A and Client B.
- Unauthenticated request is denied.

For inaccessible object details, use a scoped queryset so the response is normally `404`, avoiding tenant existence disclosure.

## Commands to run

```bash
docker compose exec backend python manage.py makemigrations tenancy assessments findings audit
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py test apps.tenancy apps.assessments apps.findings
```

Run the existing accounts test suite too before final handoff:

```bash
docker compose exec backend python manage.py test
```

## Definition of done
- Migrations apply on a clean database.
- All required tests pass.
- Tenant-scoped list and detail routes work with JWT.
- Client A cannot access Client B even when changing URL IDs.
- CVSS is validated and severity is derived server-side.
- No Day 3+ import or AI scope has been added.

## Suggested commits

```text
feat: add client scoped assessments assets and findings
test: enforce tenant scoped domain access controls
```
