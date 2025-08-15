# LLM Factory Integration Setup Guide

## Overview

The LLM Factory provides a centralized, flexible way to manage LLM providers in ZeroToShip. It supports OpenAI, Anthropic, and Ollama with secure API key management through HashiCorp Vault.

## Environment Configuration

### 1. Create `.env` File

Create a `.env` file in the project root with the following configuration:

```bash
# ZeroToShip Environment Configuration
# ===================================

# Database Configuration
NEO4J_PASSWORD=your_neo4j_password
NEO4J_URI=bolt://localhost:7687

# Vault Configuration
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=myroot
VAULT_NAMESPACE=zerotoship

# LLM Configuration
# Options: openai, anthropic, ollama
LLM_PROVIDER=anthropic
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI Configuration (fallback)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Anthropic Configuration (primary)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Twitter API Configuration
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=True

# Sustainability Tracking
CODECARBON_ENABLED=true
CODECARBON_PROJECT_NAME=ZeroToShip
CODECARBON_SAVE_TO_FILE=false
CODECARBON_MEASURE_POWER_SECS=15

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Development Configuration
DEBUG=true
ENVIRONMENT=development
```

### 2. Vault Setup

#### Start Vault in Development Mode

```bash
# Start Vault server
vault server -dev -dev-root-token-id="myroot" -dev-listen-address="0.0.0.0:8200"

# In another terminal, set environment
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=myroot
```

#### Configure Vault Secrets

```bash
# Enable KV v2 secrets engine
vault secrets enable -path=secret kv-v2

# Store LLM API keys
vault kv put secret/zerotoship/llm/openai api_key="your_openai_api_key_here"
vault kv put secret/zerotoship/llm/anthropic api_key="your_anthropic_api_key_here"

# Store Twitter API credentials
vault kv put secret/zerotoship/twitter bearer_token="your_twitter_bearer_token"
vault kv put secret/zerotoship/twitter api_key="your_twitter_api_key"
vault kv put secret/zerotoship/twitter api_secret="your_twitter_api_secret"
vault kv put secret/zerotoship/twitter access_token="your_twitter_access_token"
vault kv put secret/zerotoship/twitter access_token_secret="your_twitter_access_token_secret"
```

### 3. Ollama Setup (Optional)

If using Ollama as your LLM provider:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull llama3.1:8b

# Start Ollama service
ollama serve
```

## Testing the Integration

### 1. Run Comprehensive Test

```bash
# Test with default provider
python test_llm_factory_integration.py

# Test with specific provider
python test_llm_factory_integration.py --provider anthropic

# Test with verbose output
python test_llm_factory_integration.py --verbose
```

### 2. Test Individual Components

```bash
# Test Vault connection
python test_vault_simple.py

# Test LLM Factory directly
python -c "
import os
os.environ['LLM_PROVIDER'] = 'anthropic'
from src.zerotoship.utils.llm_factory import get_llm
llm = get_llm()
print(f'LLM initialized: {type(llm).__name__}')
"
```

### 3. Test Crew Integration

```bash
# Test a specific crew
python -c "
import asyncio
from src.zerotoship.crews.advisory_board_crew import AdvisoryBoardCrew

test_project = {
    'id': 'test-001',
    'idea': 'A test idea for validation',
    'status': 'testing'
}

crew = AdvisoryBoardCrew(test_project)
print(f'Crew initialized with LLM: {type(crew.llm).__name__}')
"
```

## Crew Files Integration

All crew files have been updated to use the LLM Factory:

### Updated Files:
- `src/zerotoship/crews/base_crew.py` - Base class with LLM Factory integration
- `src/zerotoship/crews/advisory_board_crew.py` - Advisory Board Crew
- `src/zerotoship/crews/builder_crew.py` - Builder Crew
- `src/zerotoship/crews/execution_crew.py` - Execution Crew
- `src/zerotoship/crews/marketing_crew.py` - Marketing Crew
- `src/zerotoship/crews/validator_crew.py` - Validator Crew

### Key Changes:
1. **LLM Factory Import**: All crews now import `get_llm` from `llm_factory`
2. **Centralized LLM**: Each crew uses `self.llm` (initialized in `BaseCrew`)
3. **Vault Integration**: Secure API key management through Vault
4. **Fallback Support**: Automatic fallback to environment variables if Vault fails

## Scalability Considerations

### For 1,000+ Nodes:

1. **Caching**: The LLM Factory includes caching to reduce initialization overhead
2. **Concurrent Access**: Thread-safe LLM initialization for high concurrency
3. **Celery Integration**: Distributed task execution across nodes
4. **Vault HA**: Use Vault in high-availability mode for production

### Performance Optimization:

```python
# Enable caching in llm_factory.py
from functools import lru_cache

@lru_cache()
def get_llm():
    # ... existing implementation
```

## Troubleshooting

### Common Issues:

1. **Vault Connection Failed**
   - Check `VAULT_ADDR` and `VAULT_TOKEN` in `.env`
   - Ensure Vault server is running
   - Verify secrets are stored correctly

2. **LLM Provider Not Found**
   - Check `LLM_PROVIDER` environment variable
   - Verify API keys are stored in Vault
   - Check fallback environment variables

3. **Import Errors**
   - Ensure all dependencies are installed: `uv pip install -e .`
   - Check Python path includes `src` directory

4. **Crew Initialization Failed**
   - Verify project data structure
   - Check LLM initialization in `BaseCrew`
   - Review crew-specific configuration

### Debug Mode:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python test_llm_factory_integration.py --verbose
```

## Production Deployment

### 1. Vault Production Setup

```bash
# Use Vault in production mode with proper authentication
vault server -config=/etc/vault.d/vault.hcl

# Configure AppRole authentication
vault auth enable approle
vault write auth/approle/role/zerotoship policies=zerotoship-policy
```

### 2. Environment Variables

```bash
# Production environment
export LLM_PROVIDER=anthropic
export VAULT_ADDR=https://vault.yourdomain.com
export VAULT_ROLE_ID=your-role-id
export VAULT_SECRET_ID=your-secret-id
```

### 3. Kubernetes Deployment

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zerotoship
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: zerotoship
        env:
        - name: LLM_PROVIDER
          value: "anthropic"
        - name: VAULT_ADDR
          value: "https://vault.yourdomain.com"
```

## Monitoring and Logging

### 1. LLM Usage Monitoring

```python
# Monitor LLM usage in your application
from src.zerotoship.utils.llm_factory import test_llm_connection

# Check LLM health
status = test_llm_connection("anthropic")
print(f"LLM Status: {status}")
```

### 2. Vault Audit Logging

```python
# Enable Vault audit logging
vault audit enable file file_path=/var/log/vault/audit.log
```

### 3. Performance Metrics

```python
# Monitor performance
import time
start_time = time.time()
llm = get_llm()
init_time = time.time() - start_time
print(f"LLM initialization time: {init_time:.2f}s")
```

## Security Best Practices

1. **API Key Rotation**: Regularly rotate API keys stored in Vault
2. **Access Control**: Use Vault policies to restrict access to secrets
3. **Network Security**: Use TLS for Vault communication
4. **Audit Logging**: Enable comprehensive audit logging
5. **Environment Isolation**: Use separate Vault namespaces for different environments

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the test results from `test_llm_factory_integration.py`
3. Check Vault logs and application logs
4. Verify environment configuration

## Next Steps

1. **Enhanced Caching**: Implement Redis-based caching for LLM instances
2. **Load Balancing**: Add load balancing for multiple LLM instances
3. **Metrics Collection**: Implement comprehensive metrics collection
4. **Auto-scaling**: Add auto-scaling based on LLM usage patterns
