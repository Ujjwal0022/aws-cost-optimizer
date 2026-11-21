# ⚡ Quick Reference — All Commands

## Run Tests
```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing
pytest tests/test_auth.py -v
pytest tests/test_accounts.py -v
pytest tests/test_recommendations_remediation.py -v
pytest tests/test_security_audit.py -v
```

## Local Dev
```bash
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# PostgreSQL (Docker)
docker run -d --name finops-db \
  -e POSTGRES_USER=finops \
  -e POSTGRES_PASSWORD=finops123 \
  -e POSTGRES_DB=finops_db \
  -p 5432:5432 postgres:15
```

## Push to GitHub
```bash
git add .
git commit -m "feat: Phase 7 — tests + docs + CI/CD"
git push origin main
```

## Kubernetes
```bash
# Setup secrets (first time)
chmod +x k8s/setup-secrets.sh
./k8s/setup-secrets.sh

# Check pods
kubectl get pods -n finops
kubectl get pods -n monitoring

# Logs
kubectl logs -l app=finops-backend -n finops -f

# Port forward
kubectl port-forward svc/finops-backend -n finops 8000:8000
```

## API Test
```bash
# Signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test@1234!","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test@1234!"}'

# Connect account (use token from login)
curl -X POST http://localhost:8000/accounts/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_name":"Prod","aws_account_id":"123456789012","role_arn":"arn:aws:iam::123:role/FinOpsRole"}'

# Get recommendations
curl "http://localhost:8000/recommendations/?account_id=ACCOUNT_ID" \
  -H "Authorization: Bearer TOKEN"
```

## Files to Copy Per Phase

### Phase 1 (Auth)
backend: auth/cognito.py, auth/dependencies.py, database/database.py, database/models.py, routers/auth.py, main.py
frontend: context/AuthContext.jsx, components/auth/ProtectedRoute.jsx, pages/auth/Login.jsx, pages/auth/Signup.jsx, pages/auth/ForgotPassword.jsx, components/ui/Sidebar.jsx, App.jsx

### Phase 2 (Multi-Account)
backend: services/aws_assume_role.py, services/account_service.py, routers/accounts.py, main.py
frontend: context/AccountContext.jsx, pages/Accounts.jsx, pages/ConnectAccount.jsx, components/ui/AccountSelector.jsx, Sidebar.jsx, App.jsx

### Phase 3 (AWS APIs)
backend: services/aws_client_factory.py, services/account_dependency.py, services/ec2_service.py, services/s3_service.py, services/rds_service.py, services/cost_service.py, services/lambda_eks_service.py, routers/resources.py, main.py
frontend: hooks/useAccountApi.js, components/ui/NoAccountBanner.jsx, pages/Overview.jsx

### Phase 4 (Recommendations)
backend: services/recommendation_service.py, routers/recommendations.py, main.py
frontend: pages/Recommendations.jsx, Sidebar.jsx, App.jsx

### Phase 5 (Remediation + Audit)
backend: services/remediation_service.py, services/audit_service.py, routers/remediation.py, routers/audit.py, main.py
frontend: pages/Remediation.jsx, pages/AuditLogs.jsx, Sidebar.jsx, App.jsx

### Phase 6 (Security + AI)
backend: services/security_service.py, services/copilot_service.py, routers/security.py, routers/copilot.py, main.py
frontend: pages/SecurityCenter.jsx, pages/AICopilot.jsx, Sidebar.jsx, App.jsx

### Phase 7 (Tests + CI/CD)
backend: tests/conftest.py, tests/test_auth.py, tests/test_accounts.py, tests/test_recommendations_remediation.py, tests/test_security_audit.py, pyproject.toml
root: .github/workflows/cicd.yml, k8s/helm/values.yaml, k8s/setup-secrets.sh, README.md
