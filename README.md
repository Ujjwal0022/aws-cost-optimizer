# 🚀 Multi-Account AWS FinOps SaaS Platform

<div align="center">

![AWS](https://img.shields.io/badge/AWS-Multi--Account-orange?style=for-the-badge&logo=amazon-aws)
![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-JSX-61DAFB?style=for-the-badge&logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Multi--Tenant-336791?style=for-the-badge&logo=postgresql)
![Kubernetes](https://img.shields.io/badge/Kubernetes-EKS-326CE5?style=for-the-badge&logo=kubernetes)
![Claude AI](https://img.shields.io/badge/Claude-AI_Copilot-7C3AED?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-Pytest-green?style=for-the-badge&logo=pytest)

**Production-grade, multi-tenant AWS FinOps automation and governance platform.**

### 🌐 [Live Demo →](https://aws-cost-optimizer-nw25-two.vercel.app/)

</div>

---

## 🎯 What Is This?

Not just a cost dashboard. A complete **FinOps automation platform** implementing the full cycle:

```
OBSERVE → DETECT → ANALYZE → RECOMMEND → SIMULATE → APPROVE → REMEDIATE → VERIFY → AUDIT
```

Users sign up, connect any number of AWS accounts via secure cross-account IAM roles, and get:
real-time cost analysis, AI-powered recommendations, one-click remediation with audit trails,
security posture scoring, and a Claude AI Copilot that answers questions using real account data.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Users (Multi-Tenant)                        │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              React Frontend (Vercel) — 15 pages                     │
│  Login │ Dashboard │ Accounts │ Recommendations │ Remediation │ ...  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ JWT (Bearer)
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (AWS EKS)                              │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────────────┐  │
│  │   Cognito   │ │  PostgreSQL  │ │     FinOps Engine           │  │
│  │   Auth      │ │  Multi-tenant│ │  Recommendations + Security  │  │
│  └─────────────┘ └──────────────┘ └─────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ STS AssumeRole + ExternalId
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              User's AWS Accounts (Cross-Account)                    │
│  Account A          Account B          Account C                    │
│  EC2/S3/RDS/Lambda  EC2/S3/RDS/Lambda  EC2/S3/RDS/Lambda           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Phase | Feature | Highlight |
|-------|---------|-----------|
| 1 | **Multi-user Auth** | Cognito + JWT RS256 + PostgreSQL |
| 2 | **Multi-Account** | STS AssumeRole + ExternalId (confused-deputy prevention) |
| 3 | **AWS APIs** | EC2, S3, RDS, Lambda, EKS, Cost Explorer — all account-aware |
| 4 | **Recommendations** | 8 types, confidence scores, savings estimates |
| 5 | **Remediation** | Dry-run + approval + complete audit trail |
| 6 | **Security Center** | IAM, S3, SG checks + security score (0-100) |
| 6 | **AI Copilot** | Claude AI with real AWS data context |
| 7 | **Tests** | pytest with mocked AWS — auth, IDOR, recommendations, remediation |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, JSX, Tailwind CSS, Recharts, Vercel |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, boto3 |
| **Auth** | Amazon Cognito, JWT (RS256 verification) |
| **Database** | PostgreSQL (multi-tenant, SQLAlchemy ORM) |
| **Cloud** | AWS EKS, ECR, STS, IAM, Cost Explorer, EC2, S3, RDS, Lambda |
| **AI** | Claude (Anthropic API) |
| **DevOps** | Docker, Kubernetes, Helm, Terraform, GitHub Actions, ArgoCD |
| **Monitoring** | Prometheus, Grafana, AlertManager |
| **Testing** | pytest, pytest-cov, httpx, unittest.mock |

---

## 📁 Project Structure

```
aws-cost-optimizer/
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   │   ├── cognito.py          # Signup/login/logout/verify
│   │   │   └── dependencies.py     # JWT verification + FastAPI dep
│   │   ├── database/
│   │   │   ├── database.py         # PostgreSQL + SQLAlchemy
│   │   │   └── models.py           # Users, AWSAccounts, AuditLogs...
│   │   ├── routers/
│   │   │   ├── auth.py             # /auth/*
│   │   │   ├── accounts.py         # /accounts/*
│   │   │   ├── resources.py        # /resources/* (account-aware)
│   │   │   ├── recommendations.py  # /recommendations/*
│   │   │   ├── remediation.py      # /remediation/*
│   │   │   ├── audit.py            # /audit/*
│   │   │   ├── security.py         # /security/*
│   │   │   └── copilot.py          # /copilot/*
│   │   └── services/
│   │       ├── aws_assume_role.py      # STS AssumeRole + ExternalId
│   │       ├── aws_client_factory.py   # Account-aware boto3 sessions
│   │       ├── account_dependency.py   # FastAPI dependency + ownership
│   │       ├── ec2_service.py          # EC2, EBS, EIP
│   │       ├── s3_service.py           # S3 buckets
│   │       ├── rds_service.py          # RDS instances
│   │       ├── cost_service.py         # Cost Explorer
│   │       ├── lambda_eks_service.py   # Lambda + EKS
│   │       ├── recommendation_service.py # Recommendation engine
│   │       ├── remediation_service.py  # Stop/delete/release actions
│   │       ├── audit_service.py        # Audit log queries
│   │       ├── security_service.py     # IAM/S3/SG security checks
│   │       └── copilot_service.py      # Claude AI copilot
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_accounts.py
│       ├── test_recommendations_remediation.py
│       └── test_security_audit.py
├── frontend/
│   └── src/
│       ├── context/
│       │   ├── AuthContext.jsx     # Auth state
│       │   └── AccountContext.jsx  # Account state
│       ├── hooks/
│       │   └── useAccountApi.js    # Account-aware API calls
│       ├── pages/
│       │   ├── auth/Login.jsx
│       │   ├── auth/Signup.jsx
│       │   ├── Overview.jsx
│       │   ├── Accounts.jsx
│       │   ├── Recommendations.jsx
│       │   ├── Remediation.jsx
│       │   ├── AuditLogs.jsx
│       │   ├── SecurityCenter.jsx
│       │   └── AICopilot.jsx
│       └── components/ui/
│           ├── Sidebar.jsx
│           ├── AccountSelector.jsx
│           └── NoAccountBanner.jsx
├── k8s/helm/values.yaml
├── terraform/
├── .github/workflows/cicd.yml
└── .env.example
```

---

## 🚀 Quick Start

### Prerequisites
```bash
aws, python 3.11+, node 18+, docker, kubectl, helm
```

### Local Development

```bash
# 1. Clone
git clone https://github.com/Ujjwal0022/aws-cost-optimizer.git
cd aws-cost-optimizer

# 2. Configure environment
cp .env.example .env
# Edit .env with your Cognito + PostgreSQL + Anthropic values

# 3. Start PostgreSQL
docker run -d --name finops-db \
  -e POSTGRES_USER=finops \
  -e POSTGRES_PASSWORD=finops123 \
  -e POSTGRES_DB=finops_db \
  -p 5432:5432 postgres:15

# 4. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 5. Frontend
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

Open: http://localhost:5173

---

## ☁️ AWS Setup

### 1. Amazon Cognito

```
1. AWS Console → Cognito → Create User Pool
2. Sign-in: Email
3. MFA: Optional
4. App client: Allow USER_PASSWORD_AUTH + REFRESH_TOKEN_AUTH
5. Enable client secret
6. Copy: User Pool ID, Client ID, Client Secret → .env
```

### 2. PostgreSQL (Render free tier)

```
1. dashboard.render.com → New → PostgreSQL
2. Copy connection string → DATABASE_URL in .env
```

### 3. User's IAM Role (FinOpsReadOnlyRole)

Users create this in **their** AWS account:

```bash
# Trust policy
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::PLATFORM_ACCOUNT_ID:root"},
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {"sts:ExternalId": "finops-GENERATED-EXTERNAL-ID"}
    }
  }]
}
```

Attach: `ReadOnlyAccess` policy (or custom `FinOpsReadOnlyPolicy.json`)

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Specific test file
pytest tests/test_accounts.py -v

# Specific test
pytest tests/test_recommendations_remediation.py::TestRemediationService::test_stop_ec2_dry_run -v
```

**Test coverage includes:**
- ✅ Authentication (signup, login, wrong password, unconfirmed)
- ✅ Account ownership / IDOR prevention
- ✅ STS AssumeRole + ExternalId validation
- ✅ Recommendation engine (EC2, EBS, EIP, RDS)
- ✅ Remediation dry-run + execution + failed action logging
- ✅ Security checks (IAM, S3, Security Groups)
- ✅ Audit log filtering + stats

---

## 🔐 Security Model

| Protection | Implementation |
|-----------|---------------|
| **No credentials stored** | STS AssumeRole per request, 1-hour TTL |
| **Confused-deputy attack** | ExternalId on every AssumeRole call |
| **JWT verification** | Cognito JWKS public key (RS256) |
| **IDOR prevention** | DB ownership check on every account query |
| **Dry-run by default** | Remediation requires explicit `dry_run: false` |
| **Audit trail** | Every action logged: user, resource, status, savings |
| **Secrets management** | Kubernetes Secrets, never in Git |

---

## 📊 API Reference

Full interactive docs: `http://localhost:8000/docs`

```
Authentication:     POST /auth/signup  /auth/login  /auth/me
AWS Accounts:       GET/POST /accounts/  POST /accounts/{id}/test
Resources:          GET /resources/ec2  /ebs  /s3  /rds  /waste  /costs
Recommendations:    GET /recommendations/  /summary
Remediation:        POST /remediation/stop-ec2  /delete-ebs  /release-eip
Audit:              GET /audit/  /audit/stats
Security:           GET /security/report  /score  /iam  /s3
AI Copilot:         POST /copilot/ask   GET /copilot/suggestions
Enterprise:         GET /enterprise/anomalies  /forecast  /score  /regions
```

---

## 🏆 Resume Points

- Built a **multi-tenant AWS FinOps SaaS platform** with Cognito auth, STS cross-account role assumption, and PostgreSQL for user/account isolation
- Implemented **IDOR-safe account management** — ownership check on every DB query prevents cross-user data access
- Designed an **AI-powered recommendation engine** generating EC2 rightsizing, idle resource, and Reserved Instance recommendations with confidence scores and estimated savings
- Built an **approval-based remediation engine** with dry-run mode, safety snapshots for EBS deletion, and complete PostgreSQL audit trail
- Created a **security posture dashboard** checking IAM (root MFA, admin access), S3 public access, and security group exposure with automated scoring
- Integrated **Claude AI Copilot** that answers natural language FinOps questions grounded in real AWS Cost Explorer + resource data
- Deployed on **AWS EKS** with Helm, ArgoCD GitOps, GitHub Actions CI/CD (test → Trivy → ECR → deploy → smoke test), Prometheus/Grafana monitoring

---

## 📬 Contact

**Ujjwal Kumar**
- 📧 ujjwal.kumararvind910@gmail.com
- 📱 +91-8368327428
- 🎓 B.Tech CSE, MAIT (GGSIPU) Delhi — 2027 Batch
- 💼 [GitHub](https://github.com/Ujjwal0022) | [Live Demo](https://aws-cost-optimizer-nw25-b6k0x8v7e.vercel.app/)

---

<div align="center">
<i>Built to demonstrate production-grade Cloud Engineering, DevOps, and FinOps expertise.</i>
</div>
