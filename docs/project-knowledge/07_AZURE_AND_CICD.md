# Azure Deployment and CI/CD Plan

## Deployment objective
Demonstrate a production-shaped but cost-conscious cloud architecture. The local Docker environment remains the stable delivery target. Azure is a controlled demo environment using fictional data and mock AI by default.

## Target resources

```text
Resource group: rg-sarp-demo-uksouth

sarp-web        Azure Static Web Apps         React frontend
sarp-api-env    Azure Container Apps Environment
sarp-api        Azure Container App           Django REST API
sarp-pg         Azure Database for PostgreSQL Flexible Server
sarpacr         Azure Container Registry      Backend images
sarp-openai     Optional Azure OpenAI / Foundry model deployment
budget-sarp     Azure Cost Management budget
```

Apply consistent tags:

```text
project=sarp
environment=demo
owner=manan
purpose=portfolio
```

## Deployment model

```text
GitHub pull request
   ↓
CI: backend tests, frontend build, security checks
   ↓
Manual approval for deployment
   ↓
OIDC login to Azure
   ↓
Build Django image and tag with Git SHA
   ↓
Push to ACR
   ↓
Deploy new Azure Container Apps revision
   ↓
Run migrations as a controlled release step
   ↓
Smoke test /api/v1/health/
```

React is deployed separately to Azure Static Web Apps with its production API base URL configured at build time.

## Runtime settings

### Container App

```text
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<container-app-fqdn>
CORS_ALLOWED_ORIGINS=<static-web-app-url>
DATABASE_URL=<TLS PostgreSQL connection URL>
AI_PROVIDER=mock
```

Set ingress to external HTTPS, target port 8000, min replicas 0, max replicas 1 for a low-cost demo.

### Database
- Use Azure Database for PostgreSQL Flexible Server.
- Require TLS connection.
- Create a least-privilege application database user.
- Use managed PostgreSQL rather than a self-hosted database container in cloud.
- Enable pgvector only after checking extension availability and configuration for the selected server/version.

### AI provider
- Default cloud configuration: `AI_PROVIDER=mock`.
- Optional `azure_openai` is enabled only when availability, budget and RBAC are configured.
- Prefer Azure identity/RBAC (keyless) for the deployed app rather than committing or embedding an API key.

## GitHub Actions

### CI workflow: `ci.yml`
Runs on pull request and push:

```text
backend unit/integration tests against PostgreSQL service
Django `check --deploy`
frontend lint/build
Python dependency audit
Node dependency audit
container build smoke test
```

### Deployment workflow: `deploy-demo.yml`
Runs on manual dispatch or protected main branch release:

```text
Azure OIDC login
ACR login/build/push tagged image
Container Apps update/revision deployment
optional migration command
health endpoint smoke test
```

Use GitHub environment protection for the `demo` deployment.

## OIDC and secret handling
- Use GitHub Actions OIDC to authenticate to Azure where possible.
- Store configuration as GitHub/Azure environment configuration, never in source files.
- Use Container Apps secrets or Key Vault references when secrets are necessary.
- Never include credentials in screenshots, documentation or logs.

## Cost controls
- Create a budget before resources.
- Use the smallest appropriate database tier; confirm student/free subscription eligibility before provisioning.
- Set Container App min replicas to zero and max replicas to one for demo use.
- Use mock AI for cloud demo unless Azure OpenAI cost is explicitly approved.
- Delete the resource group after recorded screenshots/demos if not needed.

## Day 10 evidence
- Screenshot of resource group with redacted names/details where needed.
- Screenshot of healthy deployed frontend/API.
- GitHub Actions workflow log showing tests/deployment.
- Redacted environment configuration image.
- `docs/deployment-runbook.md` with setup, deploy, rollback and teardown steps.

## Production limitations to document
- Demo uses fictional data and constrained capacity.
- Public database networking may be used for a simple demo; production should use private networking/private endpoints.
- App secrets should migrate to Key Vault references.
- Background import/enrichment tasks would use queues/workers in a production system.
- Azure OpenAI availability, region and quotas vary; MockProvider preserves functionality when not provisioned.
