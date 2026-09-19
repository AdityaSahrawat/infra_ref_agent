#!/usr/bin/env bash
# ==============================================================================
# Setup and Start Minikube for Autonomous Infrastructure Maintainer
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
K8S_DIR="${ROOT_DIR}/k8s"

echo "=================================================="
echo "🚀 SRE Agent: Minikube Setup"
echo "=================================================="

# 1. Check prerequisites
if ! command -v minikube &>/dev/null; then
    echo "❌ Error: 'minikube' is not installed or not in PATH."
    exit 1
fi

if ! command -v kubectl &>/dev/null; then
    echo "❌ Error: 'kubectl' is not installed or not in PATH."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    echo "❌ Error: 'docker' is not installed or not in PATH."
    exit 1
fi

if ! docker info &>/dev/null; then
    echo "❌ Error: Docker daemon is not running. Please start Docker Desktop first."
    exit 1
fi

# 2. Check Minikube status
echo "🔍 Checking Minikube status..."
STATUS="$(minikube status -f '{{.Host}}' 2>/dev/null || echo 'Stopped')"

if [ "$STATUS" = "Running" ]; then
    echo "✅ Minikube is already running."
else
    echo "📦 Starting Minikube with Docker driver..."
    minikube start --driver=docker --cpus=2 --memory=2048
fi

# 3. Apply sample deployments (auth-api & payment-service)
echo ""
echo "📄 Deploying sample applications (auth-api, payment-service)..."
kubectl apply -f "${K8S_DIR}/deployments.yaml"

# 4. Wait for deployments to become available
echo "⏳ Waiting for pods to become ready..."
kubectl rollout status deployment/auth-api --timeout=60s
kubectl rollout status deployment/payment-service --timeout=60s

echo ""
echo "=================================================="
echo "🎉 Minikube is ready and sample workloads are online!"
echo "=================================================="
echo ""
kubectl get deployments,pods -o wide
echo ""
echo "💡 Helpful commands:"
echo "   - View pods:       kubectl get pods"
echo "   - View logs:       kubectl logs -l app=auth-api"
echo "   - Minikube status: minikube status"
echo "   - Stop Minikube:   minikube stop"
echo "=================================================="
