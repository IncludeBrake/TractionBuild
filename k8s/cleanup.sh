#!/bin/bash

# tractionbuild Kubernetes Cleanup Script
set -e

echo "🧹 Cleaning up tractionbuild from Kubernetes..."

# Configuration
NAMESPACE="tractionbuild"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

print_warning "This will delete all tractionbuild resources from the cluster!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Cleanup cancelled"
    exit 0
fi

print_status "Deleting Ingress..."
kubectl delete -f k8s/ingress.yaml --ignore-not-found=true

print_status "Deleting Horizontal Pod Autoscaler..."
kubectl delete -f k8s/hpa.yaml --ignore-not-found=true

print_status "Deleting tractionbuild application..."
kubectl delete -f k8s/tractionbuild-deployment.yaml --ignore-not-found=true

print_status "Deleting Neo4j..."
kubectl delete -f k8s/neo4j-deployment.yaml --ignore-not-found=true

print_status "Deleting Secret..."
kubectl delete -f k8s/secret.yaml --ignore-not-found=true

print_status "Deleting ConfigMap..."
kubectl delete -f k8s/configmap.yaml --ignore-not-found=true

print_status "Deleting namespace..."
kubectl delete -f k8s/namespace.yaml --ignore-not-found=true

print_status "Cleanup completed successfully!"

echo ""
print_status "Note: Persistent volumes may still exist. To delete them:"
echo "  kubectl get pvc -A | grep tractionbuild"
echo "  kubectl delete pvc <pvc-name> -n <namespace>"
