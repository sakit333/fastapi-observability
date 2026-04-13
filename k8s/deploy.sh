#!/bin/bash

NAMESPACE="observability"

# =========================
# FUNCTIONS
# =========================

create_namespace() {
  kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
}

create_secrets() {
  if [ -f .env.prod ]; then
    echo "🔐 Creating Secrets..."

    kubectl create secret generic app-secrets \
      --from-env-file=.env.prod \
      -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

  else
    echo "❌ ERROR: .env.prod not found"
    exit 1
  fi
}

wait_for_pods() {
  echo "⏳ Waiting for pods..."

  kubectl wait --for=condition=ready pod \
    --all -n $NAMESPACE --timeout=180s

  if [ $? -ne 0 ]; then
    echo "❌ Some pods are not ready. Check logs:"
    kubectl get pods -n $NAMESPACE
    exit 1
  fi

  echo "✅ All pods ready"
}

delete_all() {
  echo "💣 Deleting entire namespace: $NAMESPACE"

  kubectl delete namespace $NAMESPACE --ignore-not-found=true

  echo "⏳ Waiting for namespace deletion..."
  kubectl wait --for=delete namespace/$NAMESPACE --timeout=120s

  echo "♻️ Recreating namespace..."
  kubectl create namespace $NAMESPACE

  echo "✅ Fresh namespace ready"
}

cleanup_ports() {
  echo "🛑 Stopping port-forward processes..."
  if command -v pkill >/dev/null 2>&1; then
    pkill -f "kubectl port-forward"
  else
    echo "pkill not found - skipping cleanup (Windows env)"
  fi
}

delete_images() {
  echo "🧹 Deleting local Docker images..."
  docker rmi sakit333/fastapi-observability:latest --force
}

deploy_core() {
  echo "🔧 Deploying Core Services..."
  kubectl apply -f postgres-deploy-svc.yml -n $NAMESPACE
  kubectl apply -f redis-deploy-svc.yml -n $NAMESPACE
}

build_images() {
  echo "🛠️ Building Docker image..."

  ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

  docker build -t sakit333/fastapi-observability:latest "$ROOT_DIR"

  echo "🔍 Checking for k3s..."

  if command -v k3s >/dev/null 2>&1; then
    echo "📦 k3s detected → importing image..."

    sudo k3s ctr images rm docker.io/sakit333/fastapi-observability:latest 2>/dev/null || true

    docker save sakit333/fastapi-observability:latest | sudo k3s ctr images import -

    echo "✅ Image imported into k3s"
  else
    echo "ℹ️ k3s not found → skipping import (Docker/Docker Desktop case)"
  fi
}

deploy_observability() {
  echo "📊 Deploying Observability Stack..."
  kubectl apply -f prom-deploy-svc.yml -n $NAMESPACE
  kubectl apply -f loki-deploy-svc.yml -n $NAMESPACE
  kubectl apply -f promtail-deploy.yml -n $NAMESPACE
  kubectl apply -f tempo-deploy-svc.yml -n $NAMESPACE
  kubectl apply -f grafana-datasource.yml -n $NAMESPACE
  kubectl apply -f grafana-deploy-svc.yml -n $NAMESPACE
}

deploy_app() {
  echo "🚀 Deploying Application..."
  kubectl apply -f app-deploy-svc.yml -n $NAMESPACE
}


status() {
  echo "📦 Pods:"
  kubectl get pods -n $NAMESPACE

  echo "🌐 Services:"
  kubectl get svc -n $NAMESPACE
}

grafana_access() {
  echo ""
  echo "🌍 Access Grafana:"
  echo "👉 http://localhost:3000"
  echo "👉 admin / admin"
  echo ""
}

show_access_urls() {
  echo ""
  echo "🌍 Access URLs:"
  echo "👉 FastAPI:    http://localhost:30007"
  echo "👉 Prometheus: http://localhost:30009"
  echo "👉 Grafana:    http://localhost:31011"
  echo "   Login: admin / admin"
  echo ""
}

ensure_logs_dir() {
  if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir logs
  fi
}

port_forward_all() {
  echo "🌍 Starting all port-forwards..."

  ensure_logs_dir

  nohup kubectl port-forward svc/fastapi-service 8000:80 -n $NAMESPACE > logs/fastapi.log 2>&1 &
  nohup kubectl port-forward svc/prometheus 9090:9090 -n $NAMESPACE > logs/prometheus.log 2>&1 &
  nohup kubectl port-forward svc/grafana 3000:3000 -n $NAMESPACE > logs/grafana.log 2>&1 &
  nohup kubectl port-forward svc/loki 3100:3100 -n $NAMESPACE > logs/loki.log 2>&1 &
  nohup kubectl port-forward svc/tempo 3200:3200 -n $NAMESPACE > logs/tempo.log 2>&1 &

  echo "✅ All services available on localhost"
}

# =========================
# MENU
# =========================

echo ""
echo "=============================="
echo "🚀 Kubernetes Deploy Menu"
echo "=============================="
echo "1) Full Deploy (Clean + All)"
echo "2) Deploy Core (Postgres + Redis)"
echo "3) Deploy Observability (LGTM)"
echo "4) Deploy App"
echo "5) Clean (Delete All)"
echo "6) Status"
echo "7) Open Grafana"
echo "8) Build Docker Image"
echo "9) Show Access URLs + Port-Forward"
echo "0) Exit"
echo "=============================="

read -p "👉 Select an option: " choice

# =========================
# LOGIC
# =========================

case $choice in

  1)
    echo "🔥 Full Deployment Selected"
    build_images
    create_namespace
    create_secrets
    deploy_core
    deploy_observability
    deploy_app
    wait_for_pods
    status
    grafana_access
    show_access_urls
    port_forward_all
    ;;

  2)
    create_namespace
    deploy_core
    status
    ;;

  3)
    create_namespace
    deploy_observability
    status
    ;;

  4)
    create_namespace
    deploy_app
    status
    ;;

  5)
    delete_all
    cleanup_ports
    kubectl delete ns observability --ignore-not-found=true
    cleanup_ports
    delete_images
    ;;

  6)
    status
    ;;

  7)
    grafana_access
    ;;

  8)
    build_images
    ;;

  9)
    show_access_urls
    port_forward_all
    ;;

  0)
    echo "👋 Exiting..."
    exit 0
    ;;

  *)
    echo "❌ Invalid option"
    ;;

esac