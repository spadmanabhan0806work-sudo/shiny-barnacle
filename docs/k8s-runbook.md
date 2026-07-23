# Operyx AI — Kubernetes Runbook

## Prerequisites

- Kubernetes 1.28+
- Helm 3.14+
- Container images built and pushed (or loaded locally)
- `kubectl` configured for target cluster

## Quick Deploy (Dev)

```bash
# Build images locally
docker build -f docker/Dockerfile.api -t operyx-ai-api:latest .
docker build -f docker/Dockerfile.worker -t operyx-ai-worker:latest .
docker build -f docker/Dockerfile.dashboard -t operyx-ai-dashboard:latest .

# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Install with dev overlay
helm upgrade --install operyx k8s/helm/operyx \
  -f k8s/overlays/dev/values.yaml \
  --namespace operyx \
  --create-namespace
```

## Production Deploy

```bash
helm upgrade --install operyx k8s/helm/operyx \
  -f k8s/overlays/prod/values.yaml \
  --namespace operyx \
  --set secrets.databaseUrl="$DATABASE_URL" \
  --set secrets.redisUrl="$REDIS_URL" \
  --set ingress.hosts[0].host=operyx.yourdomain.com
```

## GPU Workers

Enable GPU node affinity in `values.yaml`:

```yaml
worker:
  gpu:
    enabled: true
    nodeSelector:
      accelerator: nvidia-gpu
    tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

## Health Checks

| Probe | Endpoint | Component |
|-------|----------|-----------|
| Liveness | `GET /api/v1/health` | API |
| Readiness | `GET /api/v1/ready` | API (DB + Redis) |

## Scaling

Worker HPA is enabled by default (`minReplicas: 2`, `maxReplicas: 10`, CPU 70%).

```bash
kubectl get hpa -n operyx
kubectl scale deployment operyx-worker --replicas=5 -n operyx
```

## Migrations

API pods run `alembic upgrade head` on startup. For manual migration:

```bash
kubectl exec -it deploy/operyx-api -n operyx -- alembic upgrade head
```

## Troubleshooting

```bash
kubectl get pods -n operyx
kubectl logs deploy/operyx-worker -n operyx --tail=100
kubectl describe pod -l app.kubernetes.io/component=worker -n operyx
```

Common issues:
- **Worker pending**: Check Redis/Postgres readiness
- **GPU not scheduled**: Verify node labels and tolerations
- **503 on /ready**: Database or Redis connection string in secrets

## Uninstall

```bash
helm uninstall operyx -n operyx
kubectl delete namespace operyx
```
