# ZeroToShip Storage Fix Script
# This script fixes PVC access mode conflicts and configures local-path provisioner

Write-Host "🔧 ZeroToShip Storage Fix Script" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check if we're in the zerotoship namespace
Write-Host "📋 Checking current namespace..." -ForegroundColor Yellow
$currentNamespace = kubectl config view --minify --output 'jsonpath={..namespace}'
if ($currentNamespace -ne "zerotoship") {
    Write-Host "⚠️  Not in zerotoship namespace. Switching..." -ForegroundColor Yellow
    kubectl config set-context --current --namespace=zerotoship
}

# Step 1: Delete existing PVCs to resolve access mode conflicts
Write-Host "🗑️  Step 1: Deleting existing PVCs to resolve access mode conflicts..." -ForegroundColor Yellow
kubectl delete pvc zerotoship-data-pvc zerotoship-output-pvc -n zerotoship --ignore-not-found=true

# Wait for PVCs to be fully deleted
Write-Host "⏳ Waiting for PVCs to be fully deleted..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 2: Configure local-path as default storage class
Write-Host "⚙️  Step 2: Configuring local-path as default storage class..." -ForegroundColor Yellow

# Remove default annotation from standard storage class
Write-Host "  - Removing default annotation from 'standard' storage class..." -ForegroundColor Cyan
kubectl patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}' --ignore-not-found=true

# Set local-path as default storage class
Write-Host "  - Setting 'local-path' as default storage class..." -ForegroundColor Cyan
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}' --ignore-not-found=true

# Step 3: Apply the updated deployment with proper PVC configuration
Write-Host "🚀 Step 3: Applying updated deployment with proper PVC configuration..." -ForegroundColor Yellow
kubectl apply -f k8s/zerotoship-deployment.yaml

# Step 4: Monitor PVC creation
Write-Host "📊 Step 4: Monitoring PVC creation..." -ForegroundColor Yellow
Write-Host "  - Checking PVC status..." -ForegroundColor Cyan
kubectl get pvc -n zerotoship

Write-Host "  - Checking PV status..." -ForegroundColor Cyan
kubectl get pv

# Step 5: Verify storage class configuration
Write-Host "✅ Step 5: Verifying storage class configuration..." -ForegroundColor Yellow
Write-Host "  - Available storage classes:" -ForegroundColor Cyan
kubectl get storageclass

Write-Host "  - Default storage class:" -ForegroundColor Cyan
kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'

# Step 6: Check pod status
Write-Host "🔍 Step 6: Checking pod status..." -ForegroundColor Yellow
kubectl get pods -n zerotoship -l app=zerotoship

Write-Host ""
Write-Host "🎉 Storage fix completed!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Monitor PVC binding: kubectl get pvc -n zerotoship -w" -ForegroundColor White
Write-Host "  2. Check pod logs: kubectl logs -f deployment/zerotoship-app -n zerotoship" -ForegroundColor White
Write-Host "  3. If issues persist, check events: kubectl get events -n zerotoship --sort-by='.lastTimestamp'" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Note: If using Kind/Minikube, ensure local-path-provisioner is running:" -ForegroundColor Yellow
Write-Host "  kubectl get pods -n kube-system | grep local-path-provisioner" -ForegroundColor White
