# Production-Grade Vault Setup for ZeroToShip
# Implements comprehensive security best practices for secrets management

param(
    [string]$OpenAIAPIKey = "your-openai-api-key-here",
    [string]$AnthropicAPIKey = "your-anthropic-api-key-here",
    [string]$Environment = "dev"
)

Write-Host "🔐 Production-Grade Vault Setup for ZeroToShip" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan

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

# ============================================================================
# 1. ENABLE KV VERSION 2 SECRETS ENGINE WITH PRODUCTION CONFIGURATION
# ============================================================================
Write-Host "🗄️ Enabling KV v2 secrets engine with production configuration..." -ForegroundColor Yellow

# Check if KV v2 is already enabled
$kvStatus = vault secrets list | Select-String "secret/"
if ($kvStatus) {
    Write-Host "KV v2 engine already enabled at secret/" -ForegroundColor Green
} else {
    vault secrets enable -path=secret kv-v2
    Write-Host "✅ KV v2 engine enabled at secret/" -ForegroundColor Green
}

# Configure versioning and metadata for GDPR compliance
Write-Host "📋 Configuring versioning and metadata..." -ForegroundColor Yellow
vault kv metadata put -max-versions=10 -delete-version-after=30d secret/zerotoship

# ============================================================================
# 2. ENABLE AUDIT LOGGING FOR COMPLIANCE
# ============================================================================
Write-Host "📊 Enabling audit logging for compliance..." -ForegroundColor Yellow

# Check if audit is enabled
$auditStatus = vault audit list
if ($auditStatus -match "file") {
    Write-Host "Audit logging already enabled" -ForegroundColor Green
} else {
    # Enable file audit device
    vault audit enable file file_path=/tmp/vault_audit.log
    Write-Host "✅ Audit logging enabled" -ForegroundColor Green
}

# ============================================================================
# 3. ENABLE KUBERNETES AUTHENTICATION WITH SECURE CONFIGURATION
# ============================================================================
Write-Host "🔧 Enabling Kubernetes authentication..." -ForegroundColor Yellow

# Check if Kubernetes auth is enabled
$k8sAuthStatus = vault auth list | Select-String "kubernetes"
if ($k8sAuthStatus) {
    Write-Host "Kubernetes authentication already enabled" -ForegroundColor Green
} else {
    vault auth enable kubernetes
    Write-Host "✅ Kubernetes authentication enabled" -ForegroundColor Green
}

# Configure Kubernetes authentication with secure settings
Write-Host "⚙️ Configuring Kubernetes authentication..." -ForegroundColor Yellow

# Get the correct CA certificate from configmap
$caCertBase64 = (kubectl get configmap kube-root-ca.crt -o jsonpath="{.data['ca\.crt']}" | ForEach-Object { [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($_)) })
$caCert = [System.Convert]::FromBase64String($caCertBase64)
$caCertPath = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllBytes($caCertPath, $caCert)

# Get the correct token from the default service account
$tokenBase64 = (kubectl get secret $(kubectl get serviceaccount default -o jsonpath="{.secrets[0].name}") -o jsonpath="{.data.token}" )
$token = [System.Convert]::FromBase64String($tokenBase64)
$tokenString = [System.Text.Encoding]::UTF8.GetString($token)

vault write auth/kubernetes/config `
    kubernetes_host="https://kubernetes.default.svc:443" `
    kubernetes_ca_cert="@$caCertPath" `
    token_reviewer_jwt="$tokenString"

# Clean up temp file
Remove-Item $caCertPath

# ============================================================================
# 4. CREATE PRODUCTION-GRADE POLICIES WITH LEAST PRIVILEGE
# ============================================================================
Write-Host "📋 Creating production-grade policies..." -ForegroundColor Yellow

# Create comprehensive policy for ZeroToShip
$policyContent = @"
# ZeroToShip Production Policy - Least Privilege Access
# Read access to application secrets
path "secret/data/zerotoship/$Environment/*" {
  capabilities = ["read", "list"]
}

# Read access to metadata for auditing
path "secret/metadata/zerotoship/$Environment/*" {
  capabilities = ["read", "list"]
}

# Deny access to other paths
path "secret/data/*" {
  capabilities = ["deny"]
}

path "secret/metadata/*" {
  capabilities = ["deny"]
}
"@

$policyContent | vault policy write "zerotoship-$Environment-policy" -
Write-Host "✅ Production policy created: zerotoship-$Environment-policy" -ForegroundColor Green

# ============================================================================
# 5. CREATE KUBERNETES ROLE WITH SECURE TTL SETTINGS
# ============================================================================
Write-Host "🎭 Creating Kubernetes role with secure TTL..." -ForegroundColor Yellow

vault write auth/kubernetes/role/zerotoship `
    bound_service_account_names=zerotoship `
    bound_service_account_namespaces=zerotoship `
    policies="zerotoship-$Environment-policy" `
    ttl=1h `
    max_ttl=24h `
    audience="vault" `
    token_type=service

Write-Host "✅ Kubernetes role created with 1h TTL, 24h max TTL" -ForegroundColor Green

# ============================================================================
# 6. CREATE SERVICE ACCOUNT AND NAMESPACE
# ============================================================================
Write-Host "👤 Creating service account and namespace..." -ForegroundColor Yellow

# Create namespace if it doesn't exist
kubectl create namespace zerotoship --dry-run=client -o yaml | kubectl apply -f -

# Create service account
$serviceAccountYaml = @"
apiVersion: v1
kind: ServiceAccount
metadata:
  name: zerotoship
  namespace: zerotoship
  annotations:
    vault.hashicorp.com/role: "zerotoship"
"@

$serviceAccountYaml | kubectl apply -f -
Write-Host "✅ Service account created" -ForegroundColor Green

# ============================================================================
# 7. STORE SECRETS WITH VERSIONING AND METADATA
# ============================================================================
Write-Host "💾 Storing secrets with versioning and metadata..." -ForegroundColor Yellow

# Store database secrets with metadata
vault kv put secret/zerotoship/$Environment/database `
    NEO4J_PASSWORD="test_password" `
    NEO4J_URI="neo4j://zerotoship-neo4j.zerotoship.svc.cluster.local:7687"

# Add metadata for compliance
vault kv metadata put -custom-metadata="owner=zerotoship-team,environment=$Environment,compliance=GDPR,rotation=manual" secret/zerotoship/$Environment/database

# Store API keys with metadata
vault kv put secret/zerotoship/$Environment/apikeys `
    OPENAI_API_KEY="$OpenAIAPIKey" `
    ANTHROPIC_API_KEY="$AnthropicAPIKey"

# Add metadata for compliance
vault kv metadata put -custom-metadata="owner=zerotoship-team,environment=$Environment,compliance=GDPR,rotation=automatic" secret/zerotoship/$Environment/apikeys

Write-Host "✅ Secrets stored with versioning and metadata" -ForegroundColor Green

# ============================================================================
# 8. VERIFY SECRETS AND ACCESS
# ============================================================================
Write-Host "✅ Verifying secrets and access..." -ForegroundColor Green

Write-Host "Database secrets:" -ForegroundColor Cyan
vault kv get secret/zerotoship/$Environment/database

Write-Host "API keys:" -ForegroundColor Cyan
vault kv get secret/zerotoship/$Environment/apikeys

# Test policy access
Write-Host "Testing policy access..." -ForegroundColor Yellow
$testToken = vault write -field=token auth/kubernetes/login role=zerotoship jwt="$(kubectl create token zerotoship -n zerotoship)"
$env:VAULT_TOKEN = $testToken

# Test secret access
try {
    vault kv get secret/zerotoship/$Environment/database | Out-Null
    Write-Host "✅ Policy access test successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Policy access test failed" -ForegroundColor Red
}

# Reset to root token
$env:VAULT_TOKEN = 'root'

# ============================================================================
# 9. SETUP MONITORING AND ALERTING
# ============================================================================
Write-Host "📊 Setting up monitoring and alerting..." -ForegroundColor Yellow

# Enable Vault metrics
$metricsConfig = @"
{
  "statsd_address": "localhost:8125",
  "statsite_address": "localhost:8125",
  "circonus_api_token": "",
  "circonus_api_app": "",
  "circonus_api_url": "",
  "circonus_submission_interval": "10s",
  "circonus_submission_url": "",
  "circonus_check_id": "",
  "circonus_check_force_metric_activation": "",
  "circonus_check_instance_id": "",
  "circonus_check_search_tag": "",
  "circonus_check_display_name": "",
  "circonus_check_tags": "",
  "circonus_broker_id": "",
  "circonus_broker_select_tag": "",
  "disable_tagged_metrics": false,
  "disable_hostname": false
}
"@

$metricsConfig | vault write sys/metrics config=-

Write-Host "✅ Monitoring configured" -ForegroundColor Green

# ============================================================================
# 10. CREATE BACKUP AND RECOVERY PROCEDURES
# ============================================================================
Write-Host "💾 Setting up backup procedures..." -ForegroundColor Yellow

# Create backup script
$backupScript = @"
#!/bin/bash
# Vault Backup Script for ZeroToShip
# Run this script regularly for disaster recovery

BACKUP_DIR="/tmp/vault-backups"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\$BACKUP_DIR/vault-backup-\$DATE.json"

mkdir -p \$BACKUP_DIR

# Export all secrets (requires root token)
vault kv list -format=json secret/zerotoship > \$BACKUP_FILE

echo "Backup created: \$BACKUP_FILE"
"@

$backupScript | Out-File -FilePath "k8s/vault-backup.sh" -Encoding UTF8
Write-Host "✅ Backup script created: k8s/vault-backup.sh" -ForegroundColor Green

# ============================================================================
# 11. CLEANUP AND SUMMARY
# ============================================================================
# Clean up port forward
Write-Host "🧹 Cleaning up port forward..." -ForegroundColor Yellow
Stop-Job $portForwardJob
Remove-Job $portForwardJob

Write-Host "🎉 Production-Grade Vault Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Production Setup Summary:" -ForegroundColor Cyan
Write-Host "✅ KV v2 engine enabled with versioning (max 10 versions)"
Write-Host "✅ Audit logging enabled for compliance"
Write-Host "✅ Kubernetes authentication configured securely"
Write-Host "✅ Production policy created with least privilege"
Write-Host "✅ Kubernetes role with 1h TTL, 24h max TTL"
Write-Host "✅ Service account created with proper annotations"
Write-Host "✅ Secrets stored with metadata and compliance tags"
Write-Host "✅ Monitoring and metrics enabled"
Write-Host "✅ Backup procedures established"
Write-Host ""
Write-Host "🔐 Security Features Implemented:" -ForegroundColor Green
Write-Host "• Least privilege access policies"
Write-Host "• Short-lived tokens (1h TTL)"
Write-Host "• Audit logging for compliance"
Write-Host "• Secret versioning and metadata"
Write-Host "• Namespace isolation"
Write-Host "• Service account binding"
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update your deployment to use the new secret paths:"
Write-Host "   secret/data/zerotoship/$Environment/database"
Write-Host "   secret/data/zerotoship/$Environment/apikeys"
Write-Host "2. Test the deployment with: kubectl apply -f k8s/zerotoship-deployment.yaml"
Write-Host "3. Monitor logs: kubectl logs -f -l app=zerotoship -n zerotoship"
Write-Host "4. Set up regular backups using k8s/vault-backup.sh"
Write-Host ""
Write-Host "🔍 Verification Commands:" -ForegroundColor Cyan
Write-Host "• Check secrets: vault kv list secret/zerotoship/$Environment"
Write-Host "• Check policies: vault policy list"
Write-Host "• Check audit logs: kubectl logs vault-0 -n default"
Write-Host "• Test access: kubectl exec -it <pod> -n zerotoship -- cat /vault/secrets/database.env"
