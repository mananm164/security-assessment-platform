# Directory Structure Guide

## Final intended repository tree

```text
security-assessment-platform/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   ├── test.py
│   │   │   └── production.py
│   │   │   └── __init__.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/
│   │   ├── tenancy/
│   │   ├── assessments/
│   │   ├── imports/
│   │   ├── findings/
│   │   ├── intelligence/
│   │   ├── ai/
│   │   ├── audit/
│   │   └── common/
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── manage.py
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── dashboard/
│   │   │   ├── assessments/
│   │   │   ├── imports/
│   │   │   ├── observations/
│   │   │   ├── findings/
│   │   │   └── ai/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docs/
│   ├── architecture.md
│   ├── threat-model.md
│   ├── security-testing.md
│   ├── scanner-imports.md
│   ├── ai-governance.md
│   ├── deployment-runbook.md
│   └── decisions/
├── fixtures/
│   ├── nmap/
│   ├── zap/
│   ├── nessus/
│   ├── burp/
│   └── knowledge_base/
├── scripts/
├── .github/workflows/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
└── README.md
```

## Backend app responsibilities

| App | Owns | Must not own |
|---|---|---|
| `accounts` | Custom User, JWT/me endpoints, authentication helpers | Client data, scanner logic |
| `tenancy` | Client, ClientMembership, scoped access helpers | Assessment/finding business logic |
| `assessments` | Assessment and Asset models/services | Import parsers or AI prompts |
| `imports` | ScanImport, ScannerObservation, parsers, file validation, import services | Final Finding workflow rules |
| `findings` | Finding, FindingSource, RemediationPlan, triage/promotion services | Vendor-specific report parsing |
| `intelligence` | CVE enrichment and priority scoring | AI generation / imported file storage |
| `ai` | Providers, RAG retrieval, AIArtifact, chat/recommendation services | Permission decisions |
| `audit` | AuditLog creation/querying | Domain-specific business logic |
| `common` | shared exceptions, pagination, safe utilities, base classes | Feature models |

## File placement rules
- Put models in `models.py` or a clearly named `models/` package once an app has several related models.
- Put serializers in `serializers.py`; never put permission logic inside React components.
- Put endpoint code in `views.py` or `viewsets.py`.
- Put non-trivial domain logic in `services/`.
- Put parser classes in `apps/imports/parsers/`.
- Put small scanner examples in `fixtures/`; never use real client reports.
- Put app tests in `apps/<app>/tests/` grouped by concern, e.g. `test_permissions.py`, `test_import_nmap.py`.

## Creation schedule

### Day 2
Create `tenancy`, `assessments`, `findings`, `audit`, and minimal `common` support.

### Day 3
Create `imports` and `fixtures/nmap`.

### Day 4
Add `fixtures/zap`, `fixtures/nessus`, `fixtures/burp`.

### Day 7
Create `intelligence`.

### Day 8
Create `ai` and `fixtures/knowledge_base`.

### Day 6 onward
Create React feature folders only when their corresponding API slice works.

## Dependency direction

```text
accounts/tenancy/common
        ↓
assessments
        ↓
imports and findings
        ↓
intelligence and ai
        ↓
audit may be called by services, but must not create circular imports
```

Avoid importing app models at module import time when it creates a circular dependency. Use service boundaries and Django app references where appropriate.
