# Vault Setup Script for ZeroToShip (PowerShell)
# This script configures Vault with secrets, policies, and Kubernetes authentication

param(
    [string]$OpenAIAPIKey = "your-openai-api-key-here",
    [string]$AnthropicAPIKey = "your-anthropic-api-key-here"
)

Write-Host "🔐 Setting up Vault for ZeroToShip..." -ForegroundColor Green

# Wait for Vault to be ready
Write-Host "⏳ Waiting for Vault to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod/vault-0 -n default --timeout=300s

# Port forward Vault
Write-Host "🔌 Setting up port forward to Vault..." -ForegroundColor Yellow
$portForwardJob = Start-Job -ScriptBlock {
    kubectl port-forward vault-0 8200:8200 -n default
}

# Wait for port forward to be established
Start-Sleep -Seconds 5

# Set Vault environment
$env:VAULT_ADDR = 'http://localhost:8200'
$env:VAULT_TOKEN = 'root'

# Wait for Vault to be unsealed and ready
Write-Host "⏳ Waiting for Vault to be unsealed..." -ForegroundColor Yellow
do {
    try {
        vault status | Out-Null
        break
    }
    catch {
        Write-Host "Vault not ready yet, waiting..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
} while ($true)

Write-Host "✅ Vault is ready!" -ForegroundColor Green

# Enable Kubernetes authentication
Write-Host "🔧 Enabling Kubernetes authentication..." -ForegroundColor Yellow
vault auth enable kubernetes

# Configure Kubernetes authentication
Write-Host "⚙️ Configuring Kubernetes authentication..." -ForegroundColor Yellow
$caCertBase64 = kubectl get secret -n default -o jsonpath='{.data.ca\.crt}'
$caCert = [System.Convert]::FromBase64String($caCertBase64)
$caCertPath = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllBytes($caCertPath, $caCert)

vault write auth/kubernetes/config `
    kubernetes_host="https://kubernetes.default.svc.cluster.local" `
    kubernetes_ca_cert="@$caCertPath"

# Clean up temp file
Remove-Item $caCertPath

# Create policy for ZeroToShip
Write-Host "📋 Creating ZeroToShip policy..." -ForegroundColor Yellow
$policyContent = @"
# ZeroToShip application policy
path "secret/data/zerotoship/*" {
  capabilities = ["read"]
}

path "secret/metadata/zerotoship/*" {
  capabilities = ["read"]
}
"@

$policyContent | vault policy write zerotoship -

# Create Kubernetes role for ZeroToShip
Write-Host "🎭 Creating Kubernetes role for ZeroToShip..." -ForegroundColor Yellow
vault write auth/kubernetes/role/zerotoship `
    bound_service_account_names=zerotoship `
    bound_service_account_namespaces=zerotoship `
    policies=zerotoship `
    ttl=1h

# Create namespace and service account for ZeroToShip
Write-Host "👤 Creating namespace and service account for ZeroToShip..." -ForegroundColor Yellow

# Create namespace first
kubectl create namespace zerotoship

$serviceAccountYaml = @"
apiVersion: v1
kind: ServiceAccount
metadata:
  name: zerotoship
  namespace: zerotoship
"@

$serviceAccountYaml | kubectl apply -f -

# Enable key-value secrets engine
Write-Host "🗄️ Enabling KV secrets engine..." -ForegroundColor Yellow
vault secrets enable -path=secret kv-v2

# Store database secrets
Write-Host "💾 Storing database secrets..." -ForegroundColor Yellow
vault kv put secret/zerotoship/database `
    NEO4J_PASSWORD="test_password"

# Store API keys
Write-Host "🔑 Storing API keys..." -ForegroundColor Yellow
vault kv put secret/zerotoship/apikeys `
    OPENAI_API_KEY="$OpenAIAPIKey" `
    ANTHROPIC_API_KEY="$AnthropicAPIKey"

# Verify secrets are stored
Write-Host "✅ Verifying secrets..." -ForegroundColor Green
Write-Host "Database secrets:" -ForegroundColor Cyan
vault kv get secret/zerotoship/database

Write-Host "API keys:" -ForegroundColor Cyan
vault kv get secret/zerotoship/apikeys

# Clean up port forward
Write-Host "🧹 Cleaning up port forward..." -ForegroundColor Yellow
Stop-Job $portForwardJob
Remove-Job $portForwardJob

Write-Host "🎉 Vault setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "- Kubernetes authentication enabled"
Write-Host "- ZeroToShip policy created"
Write-Host "- Kubernetes role configured"
Write-Host "- Service account created"
Write-Host "- Database secrets stored"
Write-Host "- API keys stored"
Write-Host ""
Write-Host "🚀 Your ZeroToShip deployment can now use Vault for secrets management!" -ForegroundColor Green
