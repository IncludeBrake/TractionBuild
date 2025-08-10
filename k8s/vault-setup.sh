#!/bin/bash

# Vault Setup Script for ZeroToShip
# This script configures Vault with secrets, policies, and Kubernetes authentication

set -e

echo "🔐 Setting up Vault for ZeroToShip..."

# Wait for Vault to be ready
echo "⏳ Waiting for Vault to be ready..."
kubectl wait --for=condition=ready pod/vault-0 -n default --timeout=300s

# Port forward Vault
echo "🔌 Setting up port forward to Vault..."
kubectl port-forward vault-0 8200:8200 -n default &
VAULT_PID=$!

# Wait for port forward to be established
sleep 5

# Set Vault environment
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='dev-token'

# Wait for Vault to be unsealed and ready
echo "⏳ Waiting for Vault to be unsealed..."
until vault status > /dev/null 2>&1; do
    echo "Vault not ready yet, waiting..."
    sleep 2
done

echo "✅ Vault is ready!"

# Enable Kubernetes authentication
echo "🔧 Enabling Kubernetes authentication..."
vault auth enable kubernetes

# Configure Kubernetes authentication
echo "⚙️ Configuring Kubernetes authentication..."
vault write auth/kubernetes/config \
    kubernetes_host="https://kubernetes.default.svc.cluster.local" \
    kubernetes_ca_cert=@<(kubectl get secret -n default -o jsonpath='{.data.ca\.crt}' | base64 -d)

# Create policy for ZeroToShip
echo "📋 Creating ZeroToShip policy..."
cat << EOF | vault policy write zerotoship -
# ZeroToShip application policy
path "secret/data/zerotoship/*" {
  capabilities = ["read"]
}

path "secret/metadata/zerotoship/*" {
  capabilities = ["read"]
}
EOF

# Create Kubernetes role for ZeroToShip
echo "🎭 Creating Kubernetes role for ZeroToShip..."
vault write auth/kubernetes/role/zerotoship \
    bound_service_account_names=zerotoship \
    bound_service_account_namespaces=zerotoship \
    policies=zerotoship \
    ttl=1h

# Create service account for ZeroToShip
echo "👤 Creating service account for ZeroToShip..."
kubectl apply -f - << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: zerotoship
  namespace: zerotoship
EOF

# Enable key-value secrets engine
echo "🗄️ Enabling KV secrets engine..."
vault secrets enable -path=secret kv-v2

# Store database secrets
echo "💾 Storing database secrets..."
vault kv put secret/zerotoship/database \
    NEO4J_PASSWORD="test_password"

# Store API keys
echo "🔑 Storing API keys..."
vault kv put secret/zerotoship/apikeys \
    OPENAI_API_KEY="your-openai-api-key-here" \
    ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# Verify secrets are stored
echo "✅ Verifying secrets..."
echo "Database secrets:"
vault kv get secret/zerotoship/database

echo "API keys:"
vault kv get secret/zerotoship/apikeys

# Clean up port forward
echo "🧹 Cleaning up port forward..."
kill $VAULT_PID

echo "🎉 Vault setup complete!"
echo ""
echo "📋 Summary:"
echo "- Kubernetes authentication enabled"
echo "- ZeroToShip policy created"
echo "- Kubernetes role configured"
echo "- Service account created"
echo "- Database secrets stored"
echo "- API keys stored"
echo ""
echo "🚀 Your ZeroToShip deployment can now use Vault for secrets management!"
