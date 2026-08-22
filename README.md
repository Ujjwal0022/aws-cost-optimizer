# FinOps Cost Optimizer — Enterprise Edition

> Production-grade AWS cost optimization platform with EKS, ArgoCD GitOps, Prometheus/Grafana monitoring, AWS ALB, and GitHub Actions CI/CD.

## Architecture

```
GitHub Push → GitHub Actions (Build → Trivy Scan → Push ECR → ArgoCD Sync)
                                                          │
                                                          ▼
                                               EKS Cluster (finops-eks)
                                          ┌─────────────────────────────┐
                                          │  ArgoCD (GitOps auto-sync)  │
                                          │                             │
                                          │  finops namespace:          │
                                          │  ├── backend (FastAPI)      │
                                          │  ├── frontend (React/Nginx) │
                                          │  └── HPA (auto-scale)       │
                                          │                             │
                                          │  monitoring namespace:      │
                                          │  ├── Prometheus             │
                                          │  ├── Grafana                │
                                          │  └── AlertManager           │
                                          │                             │
                                          │  AWS ALB (Load Balancer)    │
                                          │  /     → frontend           │
                                          │  /api  → backend            │
                                          │  /grafana → grafana         │
                                          └─────────────────────────────┘
```

## Deploy — Step by Step

### Prerequisites
```bash
aws, terraform, kubectl, helm, argocd CLI installed
```

### Step 1 — Provision EKS
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars  # fill in your values
terraform init
terraform plan
terraform apply  # ~15 minutes
```

### Step 2 — Setup ArgoCD + Prometheus + Grafana
```bash
chmod +x setup.sh
./setup.sh
# Follow prompts for AWS credentials
```

### Step 3 — Add GitHub Secrets
| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your AWS key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret |
| `AWS_REGION` | `us-east-1` |
| `ECR_REGISTRY` | `ACCOUNT.dkr.ecr.REGION.amazonaws.com` |
| `ARGOCD_SERVER` | From setup.sh output |
| `ARGOCD_PASSWORD` | From setup.sh output |

### Step 4 — Push & Deploy
```bash
git push origin main
# GitHub Actions runs: Build → Trivy → Push ECR → ArgoCD Sync → Smoke Test
```

## Access

| Service | URL |
|---|---|
| FinOps Dashboard | `http://<ALB-DNS>/` |
| API Docs | `http://<ALB-DNS>/api/docs` |
| ArgoCD | `https://<ARGOCD-LB>/` |
| Grafana | `http://<ALB-DNS>/grafana` |

## CI/CD Pipeline Stages

```
1. Build       → Docker build (backend + frontend)
2. Trivy Scan  → Security scan — CRITICAL = fail, HIGH = warn
3. Push        → ECR (commit SHA tag + latest)
4. Deploy      → Update Helm values → Git push → ArgoCD auto-sync
5. Smoke Test  → Health check + API test via ALB
```

## Monitoring

- **Prometheus** scrapes finops pods via annotations automatically
- **Grafana** dashboards: Request rate, Error rate, P99 latency, Pod count, CPU/Memory, HPA scale events
- **AlertManager** sends email on: backend down, high latency, error rate spike, crash loop, HPA maxed out

## Tech Stack

| Layer | Technology |
|---|---|
| Cloud | AWS (EKS, ALB, ECR, VPC, IAM) |
| Container Orchestration | Kubernetes + Helm |
| GitOps | ArgoCD |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana + AlertManager |
| Auto-scaling | HPA (CPU + Memory) |
| Security | Trivy image scanning |
| IaC | Terraform (VPC module + EKS module) |
| Backend | FastAPI + Python 3.11 |
| Frontend | React 18 + TypeScript + Vite |
