# Security, Roles and Tenant Isolation

## Roles

| Role | Scope | Main abilities |
|---|---|---|
| Admin | All Clients | Manage users/clients/memberships, view all records, correct imports |
| Consultant | Assigned Clients only | Create assessments/assets, import reports, triage observations, create/edit Findings, generate AI drafts |
| Manager | Assigned Clients only | Read dashboards/findings/remediation plans, review status, no technical edits |
| Client User | Own Client only | Read approved Findings, remediation progress and client dashboard; no raw observations or internal notes |

## Server-side access model

Every request must use client-scoped querysets. Do not rely solely on a detail permission check.

```python
# Conceptual example: use a shared service, not duplicated endpoint logic.
def visible_clients_for(user):
    if user.role == UserRole.ADMIN:
        return Client.objects.all()
    return Client.objects.filter(
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()
```

Every Assessment, Asset, ScanImport, ScannerObservation, Finding, AIArtifact and AuditLog query must be constrained through its Client relationship.

## BOLA/IDOR rule

A user must never access another Client's record by changing an ID in a URL. For inaccessible objects, prefer a scoped queryset that returns `404 Not Found`; do not leak whether the other tenant's object exists.

## Import safety controls
- Consultant may import only into an Assessment belonging to an assigned Client.
- Allow-list `nmap XML`, `zap JSON`, `nessus`, and `burp XML` only.
- Enforce size limits before parsing.
- Validate report structure before using fields.
- Use safe XML parsing and explicitly prohibit external entities / DTD processing.
- Do not execute commands, templates, scripts or macros found in reports.
- Store safe summaries and structured fields; do not persist raw report content by default.
- Redact cookies, Authorization headers, API keys, bearer tokens, passwords, personal data and full Burp request/response payloads.
- Hash each uploaded report with SHA-256 for traceability.

## AI security rules
- AI receives only data the current user can access.
- Browser calls Django only. Django calls AI providers.
- Never submit secrets, raw Burp requests/responses or real sensitive client data to an external AI provider.
- All outputs are treated as untrusted text and safely rendered.
- AI does not automatically change statuses, accept risk, merge findings, close findings or execute remediation.
- Every AI output must state `Human decision required`.

## Remediation approval gate

```text
AI draft / consultant proposal
        ↓
Consultant reviews and edits
        ↓
Manager approval if required
        ↓
Remediation owner performs change outside SARP
        ↓
Consultant records safe validation evidence
        ↓
Finding status can become Mitigated or Closed
```

## Required security tests
- Missing, malformed and expired token rejected.
- Client A user cannot list/retrieve/update Client B Assessment, Asset, Import, Observation, Finding, AIArtifact or AuditLog.
- Manager and Client users cannot write technical records.
- Import report with unsupported extension/type/size is rejected.
- Malformed XML cannot crash the API or fetch external resources.
- Raw Burp sensitive data is not persisted.
- A promoted Observation cannot be promoted twice.
- Closing a Finding requires validation evidence.
- AI chat does not return records outside current user scope.

## Audit events
Log: import started/completed/failed, observation triaged, finding promoted/merged/updated, risk accepted, remediation submitted/approved/validated, AI artifact generated, AI recommendation reviewed.

Never log: passwords, access/refresh tokens, secret values, raw scanner reports, raw HTTP request bodies, or full AI prompts containing sensitive data.
