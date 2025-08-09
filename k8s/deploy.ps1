# ZeroToShip Kubernetes Deployment Script (PowerShell)
param(
    [string]$Registry = "your-registry.com",
    [string]$ImageTag = "latest"
)

Write-Host "🚀 Deploying ZeroToShip to Kubernetes..." -ForegroundColor Green

# Configuration
$Namespace = "zerotoship"
$ImageName = "zerotoship"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if kubectl is available
try {
    $null = kubectl version --client
} catch {
    Write-Error "kubectl is not installed or not in PATH"
    exit 1
}

# Check if we're connected to a cluster
try {
    $null = kubectl cluster-info
} catch {
    Write-Error "Not connected to a Kubernetes cluster"
    exit 1
}

Write-Status "Building Docker image..."
docker build -t ${ImageName}:${ImageTag} .

Write-Status "Tagging image for registry..."
docker tag ${ImageName}:${ImageTag} ${Registry}/${ImageName}:${ImageTag}

Write-Status "Pushing image to registry..."
docker push ${Registry}/${ImageName}:${ImageTag}

Write-Status "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

Write-Status "Creating ConfigMap..."
kubectl apply -f k8s/configmap.yaml

Write-Status "Creating Secret..."
kubectl apply -f k8s/secret.yaml

Write-Status "Deploying Neo4j..."
kubectl apply -f k8s/neo4j-deployment.yaml

Write-Status "Waiting for Neo4j to be ready..."
kubectl wait --for=condition=ready pod -l app=zerotoship,component=neo4j -n $Namespace --timeout=300s

Write-Status "Deploying ZeroToShip application..."
kubectl apply -f k8s/zerotoship-deployment.yaml

Write-Status "Creating Horizontal Pod Autoscaler..."
kubectl apply -f k8s/hpa.yaml

Write-Status "Creating Ingress..."
kubectl apply -f k8s/ingress.yaml

Write-Status "Waiting for application to be ready..."
kubectl wait --for=condition=ready pod -l app=zerotoship,component=app -n $Namespace --timeout=300s

Write-Status "Deployment completed successfully!"

Write-Host ""
Write-Host "📊 Deployment Status:" -ForegroundColor Cyan
kubectl get pods -n $Namespace

Write-Host ""
Write-Host "🌐 Services:" -ForegroundColor Cyan
kubectl get services -n $Namespace

Write-Host ""
Write-Host "📈 HPA Status:" -ForegroundColor Cyan
kubectl get hpa -n $Namespace

Write-Host ""
Write-Host "🔗 Ingress:" -ForegroundColor Cyan
kubectl get ingress -n $Namespace

Write-Status "To access the application:"
Write-Host "  1. Update your /etc/hosts file to point zerotoship.local to your cluster IP"
Write-Host "  2. Or use port-forward: kubectl port-forward -n $Namespace svc/zerotoship-app 8000:8000"

Write-Host ""
Write-Status "To view logs:"
Write-Host "  kubectl logs -f -l app=zerotoship,component=app -n $Namespace"

Write-Host ""
Write-Status "To scale the application:"
Write-Host "  kubectl scale deployment zerotoship-app --replicas=5 -n $Namespace"
