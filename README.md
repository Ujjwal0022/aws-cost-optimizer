# 💰 AWS Cost Optimizer — Enterprise FinOps Platform

<p align="center">
  <strong>Automated AWS Cost Visibility • Resource Optimization • Kubernetes • GitOps • Observability</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AWS-Cloud-orange?logo=amazonaws&logoColor=white" />
  <img src="https://img.shields.io/badge/Terraform-IaC-844FBA?logo=terraform&logoColor=white" />
  <img src="https://img.shields.io/badge/Kubernetes-EKS-326CE5?logo=kubernetes&logoColor=white" />
  <img src="https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D?logo=argo&logoColor=white" />
  <img src="https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white" />
  <img src="https://img.shields.io/badge/Trivy-Security-1904DA?logo=aquasecurity&logoColor=white" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Prometheus-Monitoring-E6522C?logo=prometheus&logoColor=white" />
  <img src="https://img.shields.io/badge/Grafana-Dashboards-F46800?logo=grafana&logoColor=white" />
  <img src="https://img.shields.io/badge/Helm-Packaging-0F1689?logo=helm&logoColor=white" />
</p>

> A production-oriented FinOps platform that connects AWS cost data, resource inventory, optimization recommendations, containerized services, Kubernetes deployment, GitHub Actions CI/CD, ArgoCD GitOps, and Prometheus/Grafana observability into one workflow.

---

## 🚀 Why This Project?

AWS environments can accumulate unnecessary spend through idle resources, oversized infrastructure, unexpected service usage, and weak cost visibility.

**AWS Cost Optimizer** provides a centralized way to inspect cloud spend and infrastructure signals, surface optimization opportunities, and run the platform itself on a production-style AWS + Kubernetes stack.

The application integrates with AWS Cost Explorer and AWS Budgets to provide cost summaries, service-level spend, daily trends, forecasts, and budget status information.

---

## ✨ Key Capabilities

### 💵 Cost Intelligence

* Month-to-date AWS cost visibility
* Previous-month cost comparison
* End-of-month cost forecasting
* Top AWS services by spend
* 30-day daily cost trend
* AWS Budget utilization and alert status
* Cost and budget data exposed through backend APIs

### 🔎 Resource Visibility & Optimization

* AWS resource inventory through the backend service layer
* Recommendations endpoint for optimization insights
* FinOps-oriented dashboard for centralized visibility
* API-driven architecture for extending optimization rules and reporting

### ☁️ Production Cloud Infrastructure

* AWS VPC with public/private subnets
* Amazon EKS cluster
* Managed worker node group
* AWS Load Balancer Controller
* Amazon ECR repositories for application images
* IAM + OIDC/IRSA integration for Kubernetes workloads
* Terraform-managed infrastructure

### 🔐 DevSecOps & CI/CD

* GitHub Actions based CI/CD pipeline
* Docker image builds for backend and frontend
* Trivy container security scanning
* Amazon ECR image publishing
* Commit SHA image tagging
* Automated Helm image tag updates
* ArgoCD deployment and health synchronization
* Post-deployment smoke tests

### 📊 Observability

* Prometheus metrics collection
* Grafana dashboards
* Kubernetes workload monitoring
* Application health validation
* Production-oriented deployment visibility

---

## 🏗️ High-Level Architecture

```text
                         ┌───────────────────┐
                         │      Developer    │
                         └─────────┬─────────┘
                                   │ git push
                                   ▼
                         ┌───────────────────┐
                         │   GitHub Actions  │
                         │                   │
                         │  Build            │
                         │  Trivy Scan       │
                         │  Push to ECR      │
                         │  Update Helm      │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │     Amazon ECR     │
                         │  backend/frontend  │
                         └─────────┬─────────┘
                                   │ image
                                   ▼
                         ┌───────────────────┐
                         │      ArgoCD       │
                         │   GitOps Sync     │
                         └─────────┬─────────┘
                                   │
                                   ▼
              ┌────────────────────────────────────┐
              │          Amazon EKS Cluster         │
              │                                    │
              │  ┌────────────┐  ┌──────────────┐ │
              │  │ React/Nginx│  │   FastAPI    │ │
              │  │  Frontend  │  │   Backend    │ │
              │  └────────────┘  └──────┬───────┘ │
              │                         │         │
              │                       AWS APIs    │
              └────────────────────────┼─────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
                 ▼                     ▼                     ▼
        ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
        │ AWS Cost       │   │ AWS Budgets    │   │ AWS Resources  │
        │ Explorer       │   │                │   │ APIs           │
        └────────────────┘   └────────────────┘   └────────────────┘

                 ┌────────────────────────────────────┐
                 │ Prometheus + Grafana               │
                 │ Monitoring / Dashboards / Metrics  │
                 └────────────────────────────────────┘
```

---

## 🔄 End-to-End Delivery Flow

```text
Developer
   │
   ▼
GitHub
   │
   ▼
GitHub Actions
   │
   ├── Build Backend Image
   ├── Build Frontend Image
   ├── Trivy Security Scan
   ├── Push Images → Amazon ECR
   │
   ▼
Update Helm image tags
   │
   ▼
Git commit / push
   │
   ▼
ArgoCD
   │
   ├── Refresh Application
   ├── Auto-Sync
   └── Wait for Healthy State
   │
   ▼
Amazon EKS
   │
   ▼
AWS ALB
   │
   ▼
FinOps Dashboard + API
   │
   ▼
Smoke Tests ✅
```

---

## 🔐 Security Pipeline

The CI pipeline adds security validation before application images are promoted.

```text
Docker Build
     │
     ▼
Trivy Image Scan
     │
     ├── Backend: CRITICAL findings can fail the pipeline
     │
     └── Frontend: HIGH / CRITICAL findings exported as SARIF
     │
     ▼
Amazon ECR
```

---

## 📊 FinOps Data Flow

The backend uses AWS SDK (`boto3`) to query AWS Cost Explorer and AWS Budgets.

```text
                         ┌─────────────────────┐
                         │   AWS Cost Explorer │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        MTD Spend             Service Spend          Daily Trend
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Backend   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                         ▼                     ▼
                 React Dashboard       Optimization APIs

                         ┌─────────────────────┐
                         │     AWS Budgets     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         Budget / Forecast Status
```

---

## 🛠️ Technology Stack

| Layer                  | Technology                         |
| ---------------------- | ---------------------------------- |
| Cloud                  | AWS                                |
| Infrastructure as Code | Terraform                          |
| Networking             | Amazon VPC                         |
| Kubernetes             | Amazon EKS                         |
| Load Balancing         | AWS Load Balancer Controller / ALB |
| Container Registry     | Amazon ECR                         |
| Backend                | FastAPI + Python                   |
| Frontend               | React + TypeScript + Vite          |
| Containerization       | Docker                             |
| Packaging              | Helm                               |
| GitOps                 | ArgoCD                             |
| CI/CD                  | GitHub Actions                     |
| Security               | Trivy                              |
| Monitoring             | Prometheus                         |
| Visualization          | Grafana                            |
| AWS Integration        | Boto3 / Cost Explorer / Budgets    |

---


## 📁 Project Structure

```text
aws-cost-optimizer/
│
├── .github/
│   └── workflows/
│       └── deploy.yml            # CI/CD pipeline
│
├── argocd/
│   ├── application.yaml          # ArgoCD application
│   └── project.yaml              # ArgoCD project
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   │   ├── aws_cost.py      # Cost & budget integration
│   │   │   ├── aws_resources.py  # Resource discovery
│   │   │   └── report_generator.py
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   └── tables/
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── grafana/                     # Grafana configuration
├── helm/                        # Kubernetes Helm charts
├── terraform/                   # AWS infrastructure
├── docker-compose.yml
├── setup.sh
└── README.md
```
## 🚀 Project Deployment Flow

<p align="center">
  <img 
    src="https://your-hosted-gif-url/aws-cost-optimizer-deployment-flow.gif"
    alt="AWS Cost Optimizer Deployment Flow"
    width="100%"
  />
</p>
---


## ⚙️ Deployment Guide

### Prerequisites

Install and configure:

```bash
aws
terraform
kubectl
helm
argocd
```

Make sure the AWS CLI is authenticated with an account that has the permissions required to provision the infrastructure and access Cost Explorer, Budgets, ECR, and EKS resources.

### 1. Clone the Repository

```bash
git clone https://github.com/Ujjwal0022/aws-cost-optimizer.git
cd aws-cost-optimizer
```

### 2. Provision AWS Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

The Terraform layer provisions the FinOps VPC, Amazon EKS cluster, managed worker nodes, AWS Load Balancer Controller integration, and ECR repositories.

### 3. Configure the Application

Create the backend environment file from the example:

```bash
cd ../backend
cp .env.example .env
```

Populate the required AWS configuration values securely.

**Never commit real AWS credentials to the repository.**

### 4. Configure GitHub Secrets

| Secret                  | Purpose                |
| ----------------------- | ---------------------- |
| `AWS_ACCESS_KEY_ID`     | AWS authentication     |
| `AWS_SECRET_ACCESS_KEY` | AWS authentication     |
| `AWS_REGION`            | Deployment region      |
| `ECR_REGISTRY`          | ECR registry endpoint  |
| `ARGOCD_SERVER`         | ArgoCD server endpoint |
| `ARGOCD_PASSWORD`       | ArgoCD authentication  |

### 5. Deploy

Push to `main`:

```bash
git add .
git commit -m "feat: deploy finops platform"
git push origin main
```

The pipeline will:

```text
Build
  ↓
Trivy Scan
  ↓
Push to ECR
  ↓
Update Helm image tags
  ↓
ArgoCD Sync
  ↓
Health Check
  ↓
Smoke Test ✅
```

---

## 🌐 Application Access

After deployment, the platform is exposed through the AWS Application Load Balancer attached to the EKS environment.

Typical endpoints:

```text
Dashboard   → http://<ALB-DNS>/
API Docs    → http://<ALB-DNS>/api/docs
Health      → http://<ALB-DNS>/health
Grafana     → http://<ALB-DNS>/grafana
```

---

## 📈 Observability

```text
Application Pods
      │
      ▼
 Prometheus
      │
      ▼
  Grafana
      │
      ├── Application Metrics
      ├── Pod / Workload Visibility
      └── Infrastructure Dashboards
```

The monitoring layer gives operational visibility into the Kubernetes-hosted platform while the FinOps dashboard focuses on AWS cost and resource intelligence.

---

## 🎯 Engineering Highlights

✅ AWS Cost Explorer integration
✅ AWS Budgets integration
✅ Cost forecasting and trend analysis
✅ AWS resource discovery layer
✅ Terraform-managed AWS infrastructure
✅ EKS + managed worker nodes
✅ Dockerized frontend and backend
✅ Amazon ECR image lifecycle
✅ Trivy security scanning in CI
✅ GitHub Actions end-to-end delivery
✅ Helm-based Kubernetes deployment
✅ ArgoCD GitOps synchronization
✅ Prometheus + Grafana observability
✅ Automated health and smoke testing

---

## 💡 What This Project Demonstrates

This project brings together three areas that are often implemented separately:

**FinOps** → Understand where AWS money is going.
**Platform Engineering** → Run the application reliably on AWS + Kubernetes.
**DevSecOps / GitOps** → Secure, automate, and continuously deliver changes.

That makes the repository a practical demonstration of:

**Cloud Engineering + DevOps + Kubernetes + FinOps**

rather than a standalone cost dashboard.

---

## 📌 Project Status

🚀 **Active Project**

Infrastructure, CI/CD, GitOps, monitoring, and AWS cost-analysis components are maintained in this repository.

---

## 👨‍💻 Author

**Ujjwal Kumar**

Cloud / DevOps Engineer — AWS • Kubernetes • Terraform • CI/CD • FinOps

GitHub: [@Ujjwal0022](https://github.com/Ujjwal0022)

---

## ⭐ Support

If this project is useful for learning **AWS, DevOps, Kubernetes, GitOps, or FinOps**, consider giving the repository a ⭐.

<p align="center">
  <strong>Build cloud systems. Automate operations. Optimize cost. 🚀</strong>
</p>
