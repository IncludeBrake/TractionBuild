# ZeroToShip Deployment Verification Script
# Comprehensive verification and troubleshooting for the deployment

Write-Host "🔍 ZeroToShip Deployment Verification Script" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# ============================================================================
# STEP 1: CHECK NAMESPACE AND BASIC SETUP
# ============================================================================
Write-Host "📋 Step 1: Checking namespace and basic setup..." -ForegroundColor Yellow

# Check current namespace
$currentNamespace = kubectl config view --minify --output 'jsonpath={..namespace}'
Write-Host "  - Current namespace: $currentNamespace" -ForegroundColor Cyan

if ($currentNamespace -ne "zerotoship") {
    Write-Host "  ⚠️  Not in zerotoship namespace. Switching..." -ForegroundColor Yellow
    kubectl config set-context --current --namespace=zerotoship
}

# Check namespace exists
$namespaceExists = kubectl get namespace zerotoship 2>$null
if ($namespaceExists) {
    Write-Host "  ✅ Namespace 'zerotoship' exists" -ForegroundColor Green
} else {
    Write-Host "  ❌ Namespace 'zerotoship' does not exist" -ForegroundColor Red
    Write-Host "  💡 Run: kubectl create namespace zerotoship" -ForegroundColor Yellow
}

# ============================================================================
# STEP 2: CHECK STORAGE CONFIGURATION
# ============================================================================
Write-Host "💾 Step 2: Checking storage configuration..." -ForegroundColor Yellow

# Check storage classes
Write-Host "  - Available storage classes:" -ForegroundColor Cyan
kubectl get storageclass

$defaultStorageClass = kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
Write-Host "  - Default storage class: $defaultStorageClass" -ForegroundColor Cyan

if ($defaultStorageClass -eq "local-path") {
    Write-Host "  ✅ Local-path is default storage class" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Local-path is not default storage class" -ForegroundColor Yellow
    Write-Host "  💡 Run: kubectl patch storageclass local-path -p '{\"metadata\": {\"annotations\":{\"storageclass.kubernetes.io/is-default-class\":\"true\"}}}'" -ForegroundColor Yellow
}

# Check PVCs
Write-Host "  - PVC status:" -ForegroundColor Cyan
kubectl get pvc -n zerotoship

# Check PVs
Write-Host "  - PV status:" -ForegroundColor Cyan
kubectl get pv

# ============================================================================
# STEP 3: CHECK VAULT CONFIGURATION
# ============================================================================
Write-Host "🔐 Step 3: Checking Vault configuration..." -ForegroundColor Yellow

# Check if Vault is running
$vaultPod = kubectl get pods -n default -l app=vault 2>$null
if ($vaultPod) {
    Write-Host "  ✅ Vault pod exists" -ForegroundColor Green
    
    # Check Vault status
    $vaultStatus = kubectl get pods -n default -l app=vault -o jsonpath='{.items[0].status.phase}'
    Write-Host "  - Vault pod status: $vaultStatus" -ForegroundColor Cyan
    
    if ($vaultStatus -eq "Running") {
        Write-Host "  ✅ Vault is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Vault is not running properly" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Vault pod not found" -ForegroundColor Red
    Write-Host "  💡 Install Vault first" -ForegroundColor Yellow
}

# Check Vault authentication configuration
Write-Host "  - Testing Vault authentication..." -ForegroundColor Cyan
try {
    # Port forward Vault
    $portForwardJob = Start-Job -ScriptBlock {
        kubectl port-forward vault-0 8200:8200 -n default
    }
    Start-Sleep -Seconds 3
    
    $env:VAULT_ADDR = 'http://localhost:8200'
    $env:VAULT_TOKEN = 'root'
    
    $authConfig = vault read auth/kubernetes/config 2>$null
    if ($authConfig) {
        Write-Host "  ✅ Vault Kubernetes authentication configured" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Vault Kubernetes authentication not configured" -ForegroundColor Red
        Write-Host "  💡 Run: .\k8s\vault-production-setup.ps1" -ForegroundColor Yellow
    }
    
    Stop-Job $portForwardJob
    Remove-Job $portForwardJob
} catch {
    Write-Host "  ⚠️  Could not test Vault authentication: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ============================================================================
# STEP 4: CHECK DEPLOYMENT STATUS
# ============================================================================
Write-Host "🚀 Step 4: Checking deployment status..." -ForegroundColor Yellow

# Check deployment
Write-Host "  - Deployment status:" -ForegroundColor Cyan
kubectl get deployment zerotoship-app -n zerotoship

# Check pods
Write-Host "  - Pod status:" -ForegroundColor Cyan
kubectl get pods -n zerotoship -l app=zerotoship

# Check service
Write-Host "  - Service status:" -ForegroundColor Cyan
kubectl get service zerotoship-app -n zerotoship

# ============================================================================
# STEP 5: CHECK POD DETAILS AND LOGS
# ============================================================================
Write-Host "🔍 Step 5: Checking pod details and logs..." -ForegroundColor Yellow

# Get pod name
$podName = kubectl get pods -n zerotoship -l app=zerotoship -o jsonpath='{.items[0].metadata.name}' 2>$null

if ($podName) {
    Write-Host "  - Pod name: $podName" -ForegroundColor Cyan
    
    # Check pod details
    Write-Host "  - Pod details:" -ForegroundColor Cyan
    kubectl describe pod $podName -n zerotoship | Select-String -Pattern "Status:|Events:|Conditions:" -Context 2
    
    # Check pod logs
    Write-Host "  - Recent application logs:" -ForegroundColor Cyan
    kubectl logs $podName -c zerotoship -n zerotoship --tail=10
    
    # Check Vault agent logs if Vault is enabled
    $vaultEnabled = kubectl get pod $podName -n zerotoship -o jsonpath='{.metadata.annotations.vault\.hashicorp\.com/agent-inject}' 2>$null
    if ($vaultEnabled -eq "true") {
        Write-Host "  - Recent Vault agent logs:" -ForegroundColor Cyan
        kubectl logs $podName -c vault-agent -n zerotoship --tail=10 2>$null
        
        Write-Host "  - Recent Vault agent init logs:" -ForegroundColor Cyan
        kubectl logs $podName -c vault-agent-init -n zerotoship --tail=10 2>$null
    }
} else {
    Write-Host "  ❌ No pods found" -ForegroundColor Red
}

# ============================================================================
# STEP 6: CHECK RESOURCE USAGE
# ============================================================================
Write-Host "📊 Step 6: Checking resource usage..." -ForegroundColor Yellow

# Check resource usage
Write-Host "  - Resource usage:" -ForegroundColor Cyan
kubectl top pods -n zerotoship 2>$null

# Check node resources
Write-Host "  - Node resource allocation:" -ForegroundColor Cyan
kubectl describe nodes | Select-String -Pattern "Allocated resources:" -Context 5

# ============================================================================
# STEP 7: CHECK EVENTS AND ISSUES
# ============================================================================
Write-Host "📢 Step 7: Checking events and issues..." -ForegroundColor Yellow

# Check recent events
Write-Host "  - Recent events:" -ForegroundColor Cyan
kubectl get events -n zerotoship --sort-by='.lastTimestamp' --tail=10

# Check for any issues
Write-Host "  - Checking for common issues..." -ForegroundColor Cyan

# Check for pending pods
$pendingPods = kubectl get pods -n zerotoship --field-selector=status.phase=Pending
if ($pendingPods -and $pendingPods -notmatch "No resources found") {
    Write-Host "  ⚠️  Found pending pods:" -ForegroundColor Yellow
    Write-Host $pendingPods -ForegroundColor Red
}

# Check for failed pods
$failedPods = kubectl get pods -n zerotoship --field-selector=status.phase=Failed
if ($failedPods -and $failedPods -notmatch "No resources found") {
    Write-Host "  ❌ Found failed pods:" -ForegroundColor Red
    Write-Host $failedPods -ForegroundColor Red
}

# Check for unbound PVCs
$unboundPVCs = kubectl get pvc -n zerotoship --field-selector=status.phase=Pending
if ($unboundPVCs -and $unboundPVCs -notmatch "No resources found") {
    Write-Host "  ⚠️  Found unbound PVCs:" -ForegroundColor Yellow
    Write-Host $unboundPVCs -ForegroundColor Red
}

# ============================================================================
# STEP 8: TEST APPLICATION ACCESS
# ============================================================================
Write-Host "🌐 Step 8: Testing application access..." -ForegroundColor Yellow

# Check if service is accessible
Write-Host "  - Testing service connectivity..." -ForegroundColor Cyan
try {
    $testJob = Start-Job -ScriptBlock {
        kubectl port-forward svc/zerotoship-app 8000:8000 -n zerotoship
    }
    Start-Sleep -Seconds 3
    
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing 2>$null
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ Application health check successful" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Application health check returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
    
    Stop-Job $testJob
    Remove-Job $testJob
} catch {
    Write-Host "  ❌ Application health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================================
# STEP 9: CHECK MONITORING SETUP
# ============================================================================
Write-Host "📈 Step 9: Checking monitoring setup..." -ForegroundColor Yellow

# Check if monitoring namespace exists
$monitoringNamespace = kubectl get namespace monitoring 2>$null
if ($monitoringNamespace) {
    Write-Host "  ✅ Monitoring namespace exists" -ForegroundColor Green
    
    # Check monitoring components
    Write-Host "  - Monitoring components:" -ForegroundColor Cyan
    kubectl get pods -n monitoring
    
    # Check ServiceMonitors
    Write-Host "  - ServiceMonitors:" -ForegroundColor Cyan
    kubectl get servicemonitors -n zerotoship 2>$null
    
    # Check PrometheusRules
    Write-Host "  - PrometheusRules:" -ForegroundColor Cyan
    kubectl get prometheusrules -n zerotoship 2>$null
} else {
    Write-Host "  ⚠️  Monitoring namespace not found" -ForegroundColor Yellow
    Write-Host "  💡 Run: .\k8s\setup-monitoring.ps1" -ForegroundColor Yellow
}

# ============================================================================
# STEP 10: SUMMARY AND RECOMMENDATIONS
# ============================================================================
Write-Host ""
Write-Host "📋 Verification Summary" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green

# Count issues
$issues = @()

if ($currentNamespace -ne "zerotoship") { $issues += "Namespace not set to zerotoship" }
if (-not $namespaceExists) { $issues += "Namespace zerotoship does not exist" }
if ($defaultStorageClass -ne "local-path") { $issues += "Local-path not default storage class" }
if (-not $vaultPod) { $issues += "Vault not installed" }
if (-not $podName) { $issues += "No application pods running" }
if ($pendingPods -and $pendingPods -notmatch "No resources found") { $issues += "Pending pods detected" }
if ($failedPods -and $failedPods -notmatch "No resources found") { $issues += "Failed pods detected" }
if ($unboundPVCs -and $unboundPVCs -notmatch "No resources found") { $issues += "Unbound PVCs detected" }
if (-not $monitoringNamespace) { $issues += "Monitoring not set up" }

if ($issues.Count -eq 0) {
    Write-Host "✅ All checks passed! Deployment appears to be healthy." -ForegroundColor Green
} else {
    Write-Host "⚠️  Found $($issues.Count) issue(s):" -ForegroundColor Yellow
    foreach ($issue in $issues) {
        Write-Host "  • $issue" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔧 Recommended Actions:" -ForegroundColor Cyan
Write-Host "• If storage issues: Run .\k8s\fix-storage.ps1" -ForegroundColor White
Write-Host "• If Vault issues: Run .\k8s\vault-production-setup.ps1" -ForegroundColor White
Write-Host "• If deployment issues: Run .\k8s\deploy-with-fixes.ps1" -ForegroundColor White
Write-Host "• If monitoring issues: Run .\k8s\setup-monitoring.ps1" -ForegroundColor White
Write-Host "• For static secrets fallback: kubectl apply -f k8s/zerotoship-deployment-static-secrets.yaml" -ForegroundColor White

Write-Host ""
Write-Host "🔍 Useful Commands:" -ForegroundColor Yellow
Write-Host "• Monitor pods: kubectl get pods -n zerotoship -w" -ForegroundColor White
Write-Host "• Check logs: kubectl logs -f <pod-name> -n zerotoship" -ForegroundColor White
Write-Host "• Check events: kubectl get events -n zerotoship --sort-by='.lastTimestamp'" -ForegroundColor White
Write-Host "• Test app: kubectl port-forward svc/zerotoship-app 8000:8000 -n zerotoship" -ForegroundColor White
Write-Host "• Check resources: kubectl top pods -n zerotoship" -ForegroundColor White
