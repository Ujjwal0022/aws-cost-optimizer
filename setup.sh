#!/bin/bash
# FinOps — Complete EKS Setup Script
# Run ONCE after: terraform apply

set -e
CLUSTER="finops-eks"
REGION="${AWS_REGION:-us-east-1}"
REPO="https://github.com/YOUR_USERNAME/finops-cost-optimizer"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; exit 1; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FinOps EKS Setup — $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1: kubectl config ──────────────────────────────────
log "Configuring kubectl..."
aws eks update-kubeconfig --region $REGION --name $CLUSTER
kubectl cluster-info | head -1
ok "kubectl configured"

# ── Step 2: Namespaces ─────────────────────────────────────
log "Creating namespaces..."
kubectl create namespace finops     --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace argocd     --dry-run=client -o yaml | kubectl apply -f -
ok "Namespaces ready"

# ── Step 3: ArgoCD ─────────────────────────────────────────
log "Installing ArgoCD..."
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available --timeout=180s \
  deployment/argocd-server -n argocd
ARGOCD_PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d)
kubectl patch svc argocd-server -n argocd \
  -p '{"spec":{"type":"LoadBalancer"}}'
ok "ArgoCD ready"

# ── Step 4: Prometheus + Grafana ───────────────────────────
log "Installing kube-prometheus-stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
cd helm/monitoring && helm dependency update && cd ../..
helm upgrade --install finops-monitoring helm/monitoring \
  --namespace monitoring \
  --create-namespace \
  --wait \
  --timeout 5m
ok "Prometheus + Grafana ready"

# ── Step 5: AWS Secret ─────────────────────────────────────
log "Creating AWS credentials secret..."
read -p "AWS_ACCESS_KEY_ID: "     AWS_KEY
read -s -p "AWS_SECRET_ACCESS_KEY: " AWS_SECRET; echo
read -p "AWS_ACCOUNT_ID: "        AWS_ACCOUNT
kubectl create secret generic finops-aws-secret \
  --from-literal=AWS_ACCESS_KEY_ID=$AWS_KEY \
  --from-literal=AWS_SECRET_ACCESS_KEY=$AWS_SECRET \
  --from-literal=AWS_ACCOUNT_ID=$AWS_ACCOUNT \
  -n finops --dry-run=client -o yaml | kubectl apply -f -
ok "AWS secret created"

# ── Step 6: ArgoCD Apps ────────────────────────────────────
log "Applying ArgoCD applications..."
# Update repo URL first
sed -i "s|YOUR_USERNAME|$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/' | cut -d'/' -f1)|" argocd/application.yaml
kubectl apply -f argocd/application.yaml
ok "ArgoCD apps created"

# ── Step 7: Get URLs ───────────────────────────────────────
log "Waiting for Load Balancers..."
sleep 30

ARGOCD_URL=$(kubectl get svc argocd-server -n argocd \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
ALB_URL=$(kubectl get ingress finops-ingress -n finops \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending - wait 2-3 min")
GRAFANA_URL=$(kubectl get ingress -n monitoring \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}✅ SETUP COMPLETE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 FinOps Dashboard : http://$ALB_URL"
echo "🔄 ArgoCD UI        : https://$ARGOCD_URL"
echo "📈 Grafana          : http://$GRAFANA_URL/grafana"
echo ""
echo "🔑 Credentials:"
echo "   ArgoCD  → admin / $ARGOCD_PASS"
echo "   Grafana → admin / finops-admin-2024"
echo ""
echo "📋 GitHub Actions secrets to add:"
echo "   ARGOCD_SERVER   = $ARGOCD_URL"
echo "   ARGOCD_PASSWORD = $ARGOCD_PASS"
echo "   ECR_REGISTRY    = $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com"
echo "   AWS_REGION      = $REGION"
echo ""
echo "👀 Watch pods:"
echo "   kubectl get pods -n finops -w"
echo "   kubectl get pods -n monitoring -w"
