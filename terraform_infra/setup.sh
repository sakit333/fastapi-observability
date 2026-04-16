#!/bin/bash

set -e

LOG_FILE="/var/log/k8s-setup.log"
export DEBIAN_FRONTEND=noninteractive

exec > >(tee -a $LOG_FILE) 2>&1

echo "=============================="
echo "🚀 EC2 Kubernetes Setup Started"
echo "📅 $(date)"
echo "=============================="

# =========================
# Fix Ubuntu mirror
# =========================
echo "🌍 Switching to stable Ubuntu mirror..."
sed -i 's|http://security.ubuntu.com/ubuntu|http://archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list

# =========================
# Safe apt update with retry
# =========================
echo "📦 Updating system (with retries)..."

for i in {1..5}; do
  apt-get clean
  rm -rf /var/lib/apt/lists/*
  if apt-get update; then
    echo "✅ apt update successful"
    break
  fi
  echo "⚠️ apt update failed... retrying ($i/5)"
  sleep 10
done

apt-get upgrade -y

# =========================
# Install dependencies
# =========================
echo "🔧 Installing dependencies..."
apt-get install -y curl wget git unzip net-tools

# =========================
# Install K3s
# =========================
echo "☸️ Installing K3s..."
curl -sfL https://get.k3s.io | sh -

# =========================
# Wait for K3s
# =========================
KUBECTL="/usr/local/bin/kubectl"

echo "⏳ Waiting for Kubernetes API..."

for i in {1..15}; do
  if $KUBECTL get nodes &>/dev/null; then
    echo "✅ Kubernetes is ready"
    break
  fi
  echo "⏳ Still starting... ($i/15)"
  sleep 10
done

# =========================
# Configure kubeconfig
# =========================
echo "⚙️ Configuring kubeconfig..."

if id "ubuntu" &>/dev/null; then
  USER_HOME="/home/ubuntu"
  mkdir -p $USER_HOME/.kube
  cp /etc/rancher/k3s/k3s.yaml $USER_HOME/.kube/config
  chown ubuntu:ubuntu $USER_HOME/.kube/config
  export KUBECONFIG=$USER_HOME/.kube/config
else
  echo "⚠️ ubuntu user not found, using root kubeconfig"
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
fi

# =========================
# Verify Kubernetes
# =========================
echo "🔍 Checking Kubernetes..."
$KUBECTL get nodes

# =========================
# Install Helm
# =========================
echo "📦 Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# =========================
# Open Ports
# =========================
echo "🌐 Opening ports..."

iptables -I INPUT -p tcp --dport 30000:32767 -j ACCEPT
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
iptables -I INPUT -p tcp --dport 443 -j ACCEPT

echo "⚙️ Installing iptables-persistent..."

echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections

apt-get install -y iptables-persistent
netfilter-persistent save

# =========================
# System Info
# =========================
echo "💾 System Info:"
free -h
df -h

# =========================
# Final Validation
# =========================
echo "=============================="
echo "🔍 FINAL VALIDATION"
echo "=============================="

echo "📦 Kubernetes Nodes:"
$KUBECTL get nodes

echo ""
echo "📦 System Pods:"
$KUBECTL get pods -A

echo ""
echo "🌐 Open Ports:"
netstat -tulnp | grep LISTEN | head -20

echo ""
echo "💾 Memory:"
free -h

echo ""
echo "💽 Disk:"
df -h

echo "=============================="
echo "✅ Setup Completed Successfully"
echo "📄 Logs: $LOG_FILE"
echo "=============================="