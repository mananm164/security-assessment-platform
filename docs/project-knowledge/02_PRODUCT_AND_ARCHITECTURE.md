# Product and Architecture Specification

## User problem
Security teams and consultancies often receive scanner reports in incompatible formats. The reports identify technical observations, but do not provide one secure workflow for triage, ownership, remediation tracking, auditability and management reporting.

SARP centralises the post-scan workflow.

```text
Authorised scanner export
        ↓
Tool-specific parser
        ↓
Normalised ScannerObservation
        ↓
Consultant triage
        ↓
Confirmed Finding
        ↓
Remediation plan, owner, approval and validation
        ↓
Manager and Client risk views
```

## High-level architecture

```text
React + Vite + Material UI
          |
          | HTTPS + JWT
          v
Django REST Framework API
  |             |              |
  v             v              v
PostgreSQL    Import services  AI services
+ pgvector    (Nmap/ZAP/       (Mock/Ollama/
              Nessus/Burp)     optional Azure OpenAI)
```

## Azure target architecture

```text
Azure Static Web Apps  →  React build
Azure Container Apps   →  Django API container
Azure Database for PostgreSQL Flexible Server → relational data + pgvector
Azure Container Registry → versioned backend images
GitHub Actions + OIDC  → CI and controlled deployment
Optional Azure OpenAI  → only via provider adapter and managed identity/RBAC
```

## Domain model

```text
User ──< ClientMembership >── Client ──< Assessment ──< Asset
                                      |              ├──< ScanImport
                                      |              |      └──< ScannerObservation
                                      |              └──< Finding
                                      |                     ├──< FindingSource >── ScannerObservation
                                      |                     ├──< AIArtifact
                                      |                     └──< RemediationPlan
User ──< AuditLog
KnowledgeDocument ──< KnowledgeChunk
VulnerabilityIntel ← Finding CVE references
```

## Main models

### Client
A tenant organisation. All business data must belong to a Client through an Assessment.

### ClientMembership
Links a User to a Client and records a relationship role. This is the source of truth for client-scoped visibility.

### Assessment
An authorised engagement or security review. Fields include client, name, framework, dates, scope summary and status.

### Asset
A scoped server, hostname, IP address, web URL, application or API. It stores criticality, environment and Internet exposure.

### ScanImport
A single file ingestion event. Stores source tool, safe file metadata, SHA-256 checksum, status, counts, import actor and error summary.

### ScannerObservation
A tool-reported issue before human confirmation. It retains source tool IDs, mapped asset, safe evidence summary, raw severity, confidence and suggested remediation.

### Finding
A consultant-approved risk that is tracked through remediation. It is not necessarily one-to-one with observations: several observations may support one Finding.

### FindingSource
Links a confirmed Finding to its original ScannerObservation(s), preserving traceability.

### VulnerabilityIntel
Cached public information for a CVE, such as summary, CVSS, CWE, KEV status, EPSS score and retrieval timestamp.

### AIArtifact
Stores a remediation draft, chat answer or recommendation with provider, prompt version, retrieved knowledge-source IDs, content and human-review state.

### RemediationPlan
Approval-gated implementation plan: proposed change, owner, rollback plan, validation plan, approver, status and safe validation evidence.

### AuditLog
Records meaningful actions with actor, action, entity type, entity ID and safe metadata. Never record password, token, secret, raw scanner report or full HTTP request/response.

## Architecture rules
- Keep views thin. Put importer, enrichment, prioritisation, AI and audit logic in services.
- Use a normalised internal observation model. Do not let tool-specific fields leak across the entire codebase.
- Preserve source links and traceability. An import must show which tool produced each observation.
- Treat scanner output as evidence to review, not as automatically confirmed truth.
- The browser never calls an LLM directly.
- All imported report handling must be safe by default: allow-list formats, bounds, parsing checks and redaction.
