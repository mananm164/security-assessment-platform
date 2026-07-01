# API Contract: Current and Future

## Base path

```text
/api/v1/
```

## Day 1 endpoints

```text
GET  /health/
POST /auth/token/
POST /auth/token/refresh/
GET  /auth/me/
```

## Day 2 endpoints

```text
GET/POST  /clients/
GET/PATCH /clients/{id}/
GET/POST  /assessments/
GET/PATCH /assessments/{id}/
GET/POST  /assets/
GET/PATCH /assets/{id}/
GET/POST  /findings/
GET/PATCH /findings/{id}/
```

## Planned import endpoints

```text
POST /assessments/{assessment_id}/imports/
GET  /imports/{id}/
GET  /imports/{id}/observations/
POST /observations/{id}/triage/
POST /observations/{id}/promote/
POST /observations/{id}/link-existing-finding/
```

## Planned intelligence and AI endpoints

```text
POST /findings/{id}/enrich-cves/
GET  /findings/{id}/priority/
POST /findings/{id}/ai/remediation/
POST /findings/{id}/ai/false-positive-review/
GET  /findings/{id}/duplicate-candidates/
POST /assessments/{id}/ai/chat/
GET  /findings/{id}/ai-artifacts/
```

## HTTP and response rules
- Use generic authentication failures.
- `401` for missing/invalid authentication.
- `403` when caller is authenticated but an endpoint type is prohibited and the resource is within visible scope.
- For a resource outside tenant scope, use filtered querysets and normally return `404`.
- `400` or `422` style validation responses must not leak stack traces or sensitive parser details.
- Paginate every potentially large collection.
- Never return internal fields, audit-safe metadata exclusions, raw scanner files or raw sensitive evidence to Client users.
