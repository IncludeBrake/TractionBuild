# ZeroToShip Comprehensive Deployment Fix Script
# Implements all fixes for Vault, storage, resources, and monitoring

param(
    [string]$OpenAIAPIKey = $null,
    [string]$AnthropicAPIKey = $null,
    [string]$Environment = "dev",
    [string]$Namespace = "zerotoship"
)

Write-Host "🚀 ZeroToShip Comprehensive Deployment Fix Script" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Validate approved verbs (self-check)
$approvedVerbs = Get-Verb | Select-Object -ExpandProperty Verb
if ("Invoke" -notin $approvedVerbs) {
    Write-Warning "Approved verbs list may be incomplete; update PowerShell if needed."
}

# Function for error handling and rollback (approved verb)
function Invoke-ErrorHandler {
    param ([string]$Message, [string]$RollbackCommand)
    Write-Host "❌ Error: $Message" -ForegroundColor Red
    # GDPR-compliant logging: Anonymize and log to file
    $anonMessage = $Message -replace '(sk-|anthropic-)[^ ]+', '$1[REDACTED]'  # Redact keys
    $anonMessage | Out-File -FilePath "k8s/deployment-errors.log" -Append
    if ($RollbackCommand) {
        Write-Host "Rolling back: $RollbackCommand" -ForegroundColor Yellow
        Invoke-Expression $RollbackCommand
    }
    exit 1
}

# Securely prompt for API keys if not provided
if (-not $OpenAIAPIKey) {
    $secureOpenAI = Read-Host "Enter OpenAI API Key (secure input)" -AsSecureString
    $OpenAIAPIKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureOpenAI))
}
if (-not $AnthropicAPIKey) {
    $secureAnthropic = Read-Host "Enter Anthropic API Key (secure input)" -AsSecureString
    $AnthropicAPIKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureAnthropic))
}

# Get kubectl version for compatibility (though not needed for this fix, retained for future)
$kubectlVersion = kubectl version --client --output=json | ConvertFrom-Json
$major = [int]$kubectlVersion.clientVersion.major
$minor = [int]$kubectlVersion.clientVersion.minor

# ============================================================================
# STEP 1: CLEANUP AND PREPARATION
# ============================================================================
Write-Host "🧹 Step 1: Cleanup and preparation..." -ForegroundColor Yellow

# Set namespace with check
$currentNamespace = kubectl config view --minify --output 'jsonpath={..namespace}'
if ($currentNamespace -ne $Namespace) {
    Write-Host "⚠️ Not in $Namespace namespace. Switching..." -ForegroundColor Yellow
    kubectl config set-context --current --namespace=$Namespace
}

# Backup deployment config for rollback
kubectl get deployment zerotoship-app -o yaml > k8s/zerotoship-deployment-backup.yaml 2>$null

# Pre-check if deployment exists before scaling
Write-Host "Scaling down deployment to clean up..." -ForegroundColor Cyan
$deploymentExists = kubectl get deployment zerotoship-app -n $Namespace 2>$null
if ($LASTEXITCODE -eq 0 -and $deploymentExists) {
    try {
        kubectl scale deployment zerotoship-app --replicas=0 -n $Namespace
    } catch {
        Write-Host "⚠️ Scale down failed; forcing pod deletion..." -ForegroundColor Yellow
        kubectl delete pod -l app=zerotoship -n $Namespace --force --grace-period=0
    }
} else {
    Write-Host "Deployment not found; skipping scale-down." -ForegroundColor Yellow
}

# Wait for pods to terminate with timeout
Write-Host "Waiting for pods to terminate..." -ForegroundColor Cyan
$timeout = 120  # seconds
$elapsed = 0
do {
    $pendingPods = kubectl get pods -n $Namespace -l app=zerotoship -o jsonpath='{.items[*].status.phase}' | Where-Object { $_ -eq "Running" -or $_ -eq "Pending" }
    if ($pendingPods) { Start-Sleep -Seconds 5; $elapsed += 5 }
    if ($elapsed -ge $timeout) { Invoke-ErrorHandler "Timeout waiting for pods to terminate" }
} until (-not $pendingPods)

# Delete existing PVCs idempotently
Write-Host "Deleting existing PVCs..." -ForegroundColor Cyan
kubectl delete pvc zerotoship-data-pvc zerotoship-output-pvc -n $Namespace --ignore-not-found=true

# ============================================================================
# STEP 2: STORAGE CONFIGURATION
# ============================================================================
Write-Host "💾 Step 2: Configuring storage with local-path..." -ForegroundColor Yellow

# Set local-path as default storage class
kubectl patch storageclass standard -p '{\"metadata\": {\"annotations\":{\"storageclass.kubernetes.io/is-default-class\":\"false\"}}}' 2>$null
kubectl patch storageclass local-path -p '{\"metadata\": {\"annotations\":{\"storageclass.kubernetes.io/is-default-class\":\"true\"}}}' 2>$null

# Apply updated deployment (assume YAML updated with storageClassName: local-path and ReadWriteOnce)
kubectl apply -f k8s/zerotoship-deployment.yaml

# Verify PVC binding with timeout
Write-Host "Verifying PVC binding..." -ForegroundColor Cyan
$elapsed = 0
do {
    $pendingPVCs = kubectl get pvc -n $Namespace -o jsonpath='{.items[?(@.status.phase=="Pending")].metadata.name}'
    if ($pendingPVCs) { Start-Sleep -Seconds 5; $elapsed += 5 }
    if ($elapsed -ge $timeout) { Invoke-ErrorHandler "Timeout binding PVCs" "kubectl delete -f k8s/zerotoship-deployment.yaml" }
} until (-not $pendingPVCs)

# ============================================================================
# STEP 3: VAULT INTEGRATION AND SECRETS
# ============================================================================
Write-Host "🔐 Step 3: Injecting secrets to Vault..." -ForegroundColor Yellow

# Run Vault setup script (assume vault-production-setup.ps1 is fixed from previous)
.\k8s\vault-production-setup.ps1 -Environment $Environment

# Inject API keys to Vault with rotation metadata
vault kv put -mount=secret zerotoship/$Environment/apikeys OPENAI_API_KEY=$OpenAIAPIKey ANTHROPIC_API_KEY=$AnthropicAPIKey
vault kv metadata put -custom-metadata="rotation=automatic,compliance=GDPR" secret/zerotoship/$Environment/apikeys

# ============================================================================
# STEP 4: RESOURCE OPTIMIZATION
# ============================================================================
Write-Host "⚙️ Step 4: Optimizing resources..." -ForegroundColor Yellow

# Apply resource quota
$quotaYaml = @"
apiVersion: v1
kind: ResourceQuota
metadata:
  name: zerotoship-quota
  namespace: $Namespace
spec:
  hard:
    requests.cpu: 2
    requests.memory: 4Gi
    limits.cpu: 3
    limits.memory: 6Gi
"@
$quotaYaml | kubectl apply -f -

# Scale back up
kubectl scale deployment zerotoship-app --replicas=1 -n $Namespace  # Start with 1 for dev

# ============================================================================
# STEP 5: MONITORING SETUP
# ============================================================================
Write-Host "📊 Step 5: Setting up monitoring..." -ForegroundColor Yellow

kubectl apply -f k8s/prometheus-pvc-rules.yaml

# ============================================================================
# STEP 6: VERIFICATION AND BENCHMARKING
# ============================================================================
Write-Host "✅ Step 6: Verification and benchmarking..." -ForegroundColor Yellow

kubectl get pods -n $Namespace -w  # Watch pods

# Benchmark throughput (simple test; expand for production)
Write-Host "Running basic throughput benchmark..."
for ($i=1; $i -le 10; $i++) {
    curl -X POST http://localhost:8000/api/v1/projects -H "Content-Type: application/json" -d '{"name":"TestProject$i"}'  # Port-forward first
}

# CI/CD Hook Example: Comment on GitHub PR
# Add your GitHub token and repo details here

Write-Host "🎉 Deployment Fix Complete! Check logs with: kubectl logs -f -l app=zerotoship -n $Namespace" -ForegroundColor Green