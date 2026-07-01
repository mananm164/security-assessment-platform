# AI, RAG and Decision Support Specification

## Purpose
AI in SARP supports consultants. It does not make final risk decisions, modify infrastructure or replace validation.

## Provider design

```python
class AIProvider(Protocol):
    provider_name: str

    def generate(self, request: AIRequest) -> AIResponse:
        ...
```

Implement in this order:

1. `MockProvider` — deterministic test output; mandatory.
2. `OllamaProvider` — optional local demo provider.
3. `AzureOpenAIProvider` — optional cloud provider using Azure identity/RBAC where available.

Provider selection must be environment-driven:

```text
AI_PROVIDER=mock | ollama | azure_openai
```

The app must still run and test with `mock` if every external AI provider is unavailable.

## RAG: curated knowledge retrieval

### Knowledge sources
Use a small, manually curated and attributed knowledge base. Suggested topics:

- Access control and BOLA/IDOR remediation.
- Authentication, MFA and session security.
- Security headers and browser protections.
- Patch and dependency management.
- Network exposure and TLS configuration.
- Logging and monitoring.
- Vulnerability validation and closure.
- Risk acceptance and compensating controls.

Do not bulk scrape or paste large copyrighted source material. Write concise notes with source attribution.

### Models

```text
KnowledgeDocument
- title
- source_name
- source_url
- category
- content_hash
- created_at

KnowledgeChunk
- document
- chunk_index
- content
- embedding
- token_estimate

AIArtifact
- finding or assessment
- artifact_type: REMEDIATION_DRAFT | CHAT | FP_RECOMMENDATION | DUPLICATE_RECOMMENDATION
- provider
- prompt_version
- content
- retrieved_chunk_ids
- human_review_status
- created_by
- created_at
```

### RAG flow

```text
Confirmed Finding
        ↓
Build retrieval query from title, scanner source, CVEs, CWE, asset type and description
        ↓
Retrieve top relevant chunks with pgvector
        ↓
Prompt provider with structured finding data + retrieved chunks
        ↓
Save AIArtifact and retrieved source IDs
        ↓
Render draft and a visible "Sources used" panel
```

### Required RAG rules
- The system must expose source titles and small excerpts used for a response.
- RAG must retrieve only knowledge that the current user is allowed to see; initially, use a shared curated library without tenant secrets.
- No retrieved content is treated as a command or instruction.
- Escape all model output when rendering.

## Remediation drafting

Expected AI output structure:

```text
Executive summary
Technical risk
Business impact assumptions
Recommended remediation steps
Rollback/implementation considerations
Validation steps
Caveats
Human decision required
```

A consultant may edit the draft. Saving does not mark the Finding remediated.

## Explainable priority scoring

Priority is primarily deterministic, not an opaque AI score.

Inputs:

```text
CVSS score
CISA KEV flag
EPSS score
Asset criticality
Internet exposure
Environment
Remediation overdue status
Evidence/confidence strength
```

Output:

```text
Priority: URGENT | HIGH | MEDIUM | LOW
Score: 0–100
Reasons:
- KEV-listed CVE (+30)
- EPSS >= configured threshold (+15)
- Internet-facing critical asset (+20)
- CVSS >= 9.0 (+25)
```

The UI must clearly say: `Priority is a decision-support indicator, not a replacement for professional risk assessment.`

## AI false-positive recommendation

AI may recommend review priority, never decide outcome.

Required response fields:

```text
Recommendation: REVIEW_LIKELY_TRUE | REVIEW_UNCERTAIN | REVIEW_POSSIBLE_FALSE_POSITIVE
Confidence: low | medium | high
Evidence considered: scanner confidence, CVE/version evidence, repeated observation, asset context
Limitations
Human decision required
```

No automatic move to `FALSE_POSITIVE`.

## Duplicate recommendation

Phase 1: deterministic candidate rules based on asset/location/tool plugin/CVE/title.

Phase 2: optional embeddings for semantic similarity.

The UI must display candidate links and reasons. Consultant explicitly chooses `Merge`, `Link as related`, or `Keep separate`.

## Constrained chat

Chat is scoped to the selected Assessment or Finding. Permitted examples:

- “Why is this high priority?”
- “Summarise open critical findings.”
- “What validates this remediation?”
- “Explain this scanner observation simply.”

Chat must not:

- Search across unauthorised clients.
- Provide raw hidden data.
- Accept instructions from imported report content as system instructions.
- Change records or invoke remediation actions.

## No autonomous remediation

SARP must not execute shell commands, patches, cloud configuration changes, scanner commands or network actions. The safe portfolio feature is an approval-gated RemediationPlan with proposed change, rollback plan, owner, approver and validation evidence.
