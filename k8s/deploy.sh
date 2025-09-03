#!/bin/bash

# tractionbuild Kubernetes Deployment Script
set -e

echo "🚀 Deploying tractionbuild to Kubernetes..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="tractionbuild"
IMAGE_NAME="tractionbuild"
IMAGE_TAG="latest"
REGISTRY="your-registry.com"  # Change this to your container registry

# Function to print colored output
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

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Not connected to a Kubernetes cluster"
    exit 1
fi

print_status "Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

print_status "Tagging image for registry..."
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

print_status "Pushing image to registry..."
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

print_status "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

print_status "Creating ConfigMap..."
kubectl apply -f k8s/configmap.yaml

print_status "Creating Secret..."
kubectl apply -f k8s/secret.yaml

print_status "Deploying Neo4j..."
kubectl apply -f k8s/neo4j-deployment.yaml

print_status "Waiting for Neo4j to be ready..."
kubectl wait --for=condition=ready pod -l app=tractionbuild,component=neo4j -n ${NAMESPACE} --timeout=300s

print_status "Deploying tractionbuild application..."
kubectl apply -f k8s/tractionbuild-deployment.yaml

print_status "Creating Horizontal Pod Autoscaler..."
kubectl apply -f k8s/hpa.yaml

print_status "Creating Ingress..."
kubectl apply -f k8s/ingress.yaml

print_status "Waiting for application to be ready..."
kubectl wait --for=condition=ready pod -l app=tractionbuild,component=app -n ${NAMESPACE} --timeout=300s

print_status "Deployment completed successfully!"

echo ""
echo "📊 Deployment Status:"
kubectl get pods -n ${NAMESPACE}
echo ""
echo "🌐 Services:"
kubectl get services -n ${NAMESPACE}
echo ""
echo "📈 HPA Status:"
kubectl get hpa -n ${NAMESPACE}
echo ""
echo "🔗 Ingress:"
kubectl get ingress -n ${NAMESPACE}

print_status "To access the application:"
echo "  1. Update your /etc/hosts file to point tractionbuild.local to your cluster IP"
echo "  2. Or use port-forward: kubectl port-forward -n ${NAMESPACE} svc/tractionbuild-app 8000:8000"
echo ""
print_status "To view logs:"
echo "  kubectl logs -f -l app=tractionbuild,component=app -n ${NAMESPACE}"
echo ""
print_status "To scale the application:"
echo "  kubectl scale deployment tractionbuild-app --replicas=5 -n ${NAMESPACE}"
