# Codex Working Contract

## Role
You are implementing SARP incrementally. You are not authorised to broaden the scope, replace unrelated code, fabricate test results, or remove security controls for convenience.

## Before every coding task
1. Read the relevant documents in this pack.
2. Inspect the current repository state.
3. List affected files.
4. Provide a 3–6 step implementation plan.
5. Identify tests to add or update.
6. Wait for explicit confirmation only if the task involves destructive data migration or a major irreversible redesign; otherwise proceed carefully.

## Implementation standards
- Use Python 3.12, Django 5.2 LTS, DRF, PostgreSQL and React/Vite.
- Use type hints for services and non-trivial functions.
- Keep views thin; service layer owns imports, triage, AI, enrichment, prioritisation and audit actions.
- Use env vars for configuration. Do not hard-code secrets, URLs, credentials or tenant IDs.
- Add/update tests with every behavioural change.
- Use fixtures with fictional data only.
- Do not introduce Redis, Celery, Kubernetes, Terraform, background workers or new cloud services unless the relevant plan explicitly calls for it.
- Do not use `eval`, shell execution, dynamic imports of report content, unsafe YAML loading or raw HTML rendering.

## Security invariants
- JWT authenticates the caller; permissions and scoped querysets determine what they may access.
- All tenant-aware endpoints must use server-side scoped querysets.
- A scanner observation is not a confirmed finding until Consultant triage/promote action.
- Do not persist raw sensitive Burp request/response data.
- AI output is untrusted and must be safely rendered.
- AI must never mutate remediation state automatically.
- No scanner command execution from SARP.

## Importer rules
- Parsers return `NormalisedObservation` data only.
- Parsers never directly create models.
- Use explicit format validation and safe error types.
- Keep source-specific code inside `apps/imports/parsers/`.
- Reimport must update last-seen state when fingerprints match.

## Testing requirements
Run the narrowest relevant tests first, then the full backend suite before handing over.

End every implementation response with:

```text
Changed files
Commands run
Tests run and results
Manual verification steps
Known limitation or follow-up
Suggested commit message
```

## Git requirements
- Make small commits at working milestones.
- Use imperative commit messages.
- Do not commit `.env`, generated reports, real data, credentials, test screenshots containing secrets, or large model files.

## Example prompt prefix

```text
You are working on SARP. Read docs/project-knowledge/README.md and the relevant implementation brief before coding.
Do not modify unrelated files.
Before changing code, list affected files, a concise plan and planned tests.
Use server-side tenant-scoped querysets and preserve the security invariants.
After implementation, run focused tests and provide commands, results, manual checks and a suggested commit message.
```
