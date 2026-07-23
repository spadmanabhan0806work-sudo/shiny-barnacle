# Operyx AI — Security Hardening Guide

## Secrets Management

- **Never commit** `.env`, database passwords, or API keys
- Use Kubernetes Secrets (`k8s/helm/operyx/templates/secret.yaml`) or external secret managers (Vault, AWS Secrets Manager)
- Rotate `POSTGRES_PASSWORD` and Redis credentials on a 90-day schedule
- In production, replace inline `stringData` with sealed-secrets or CSI driver references

## Authentication & Authorization

- OIDC stub auth is in `src/api/middleware/auth.py` — enable via `auth.enabled: true` in config
- RBAC roles: `annotator` < `reviewer` < `admin`
- Route permissions are defined in `ROUTE_PERMISSIONS` — extend for new endpoints
- Replace stub base64 JWT decoding with real JWKS validation before production:
  - Set `auth.oidc_issuer`, `auth.oidc_audience`, `auth.jwks_url` in config

## Network Security

- Enable TLS ingress (`ingress.tls` in Helm values)
- Restrict API/dashboard services to ClusterIP; expose only via ingress
- Use NetworkPolicies to limit worker → Postgres/Redis only

## Pod Security

Helm chart defaults:
- `runAsNonRoot: true`, `runAsUser: 1000`
- `allowPrivilegeEscalation: false`
- Drop all capabilities

## Data Protection

- Recordings stored via `StorageProvider` — use encrypted object storage (S3 SSE, Azure Blob encryption) in production
- Audit log on every extraction change, review action, and export (`audit_logs` table)
- PII in call recordings: define retention policy and encrypt at rest

## Prompt Injection

- LLM prompts are sandboxed — no tool execution from transcript content
- Output validated against JSON schema (`prompts/call_to_trade/*/schema.json`)
- `IntentValidator` post-processes all extractions deterministically

## CI/CD Security

- GitHub Actions runs lint + tests on every PR
- Images built on main branch only; no secrets in workflow files
- Helm chart linted before deploy job

## Compliance Checklist

| Control | Status | Notes |
|---------|--------|-------|
| Encryption at rest | Configurable | Use cloud storage adapter |
| Audit logging | Implemented | `audit_logs` table |
| RBAC | Stub OIDC | Upgrade to Keycloak/Auth0 |
| TLS in transit | Helm ingress | Enable in prod overlay |
| Secret rotation | Manual | Automate via external secrets |
| HITL for low confidence | Implemented | Threshold configurable |

## Reporting Security Issues

Report vulnerabilities to your security team. Do not open public issues for undisclosed security findings.
