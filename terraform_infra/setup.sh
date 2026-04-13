#!/bin/bash

set -e

# =========================
# GLOBAL CONFIG
# =========================
LOG_FILE="/var/log/k8s-setup.log"
export DEBIAN_FRONTEND=noninteractive

# Redirect ALL output to log + console
exec > >(tee -a $LOG_FILE) 2>&1

echo "=============================="
echo "🚀 EC2 Kubernetes Setup Started"
echo "📅 $(date)"
echo "=============================="

# =========================
# 1. Update system
# =========================
echo "📦 Updating system..."
sudo apt update -y
sudo apt upgrade -y

# =========================
# 2. Install dependencies
# =========================
echo "🔧 Installing dependencies..."
sudo apt install -y curl wget git unzip net-tools

# =========================
# 3. Install Docker
# =========================
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# =========================
# 4. Install K3s (Kubernetes)
# =========================
echo "☸️ Installing K3s..."
curl -sfL https://get.k3s.io | sh -

echo "⏳ Waiting for K3s to be ready..."
sleep 25

# =========================
# 5. Configure kubectl
# =========================
echo "⚙️ Configuring kubectl..."

mkdir -p /home/ubuntu/.kube
sudo cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
sudo chown ubuntu:ubuntu /home/ubuntu/.kube/config

export KUBECONFIG=/home/ubuntu/.kube/config

# =========================
# 6. Verify Kubernetes
# =========================
echo "🔍 Checking Kubernetes..."
kubectl get nodes

# =========================
# 7. Install Helm
# =========================
echo "📦 Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# =========================
# 8. Open Ports (NodePort)
# =========================
echo "🌐 Opening ports..."

sudo iptables -I INPUT -p tcp --dport 30000:32767 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT

echo "⚙️ Installing iptables-persistent (non-interactive)..."

echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections

sudo apt install -y iptables-persistent
sudo netfilter-persistent save

# =========================
# 9. System Info
# =========================
echo "💾 System Info:"
free -h
df -h

# =========================
# 10. Final Validation
# =========================
echo "=============================="
echo "🔍 FINAL VALIDATION"
echo "=============================="

echo "📦 Kubernetes Nodes:"
kubectl get nodes

echo ""
echo "📦 System Pods:"
kubectl get pods -A

echo ""
echo "🌐 Open Ports:"
sudo netstat -tulnp | grep LISTEN | head -20

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