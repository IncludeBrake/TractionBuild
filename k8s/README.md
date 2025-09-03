# tractionbuild Kubernetes Deployment

This directory contains all the Kubernetes manifests and scripts needed to deploy tractionbuild to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.20+)

- kubectl configured and connected to your cluster

- Docker installed and configured

- Container registry (Docker Hub, GCR, ECR, etc.)

- Ingress controller (nginx-ingress recommended)

- cert-manager (for SSL certificates)

## Quick Start

1. **Update the configuration:**

   ```bash
   # Edit k8s/deploy.sh and update the REGISTRY variable
   REGISTRY="your-registry.com"
   
   # Edit k8s/tractionbuild-deployment.yaml and update the image
   image: your-registry.com/tractionbuild:latest
   
   # Edit k8s/secret.yaml and add your API keys
   OPENAI_API_KEY: <base64-encoded-openai-key>
   ANTHROPIC_API_KEY: <base64-encoded-anthropic-key>

   ```

2. **Make scripts executable:**

   ```bash
   chmod +x k8s/deploy.sh
   chmod +x k8s/cleanup.sh
   ```

3. **Deploy to Kubernetes:**

   ```bash
   ./k8s/deploy.sh
   ```

## Manual Deployment

If you prefer to deploy manually:

```bash
# Create namespace

kubectl apply -f k8s/namespace.yaml

# Create ConfigMap and Secret

kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy Neo4j

kubectl apply -f k8s/neo4j-deployment.yaml

# Wait for Neo4j to be ready

kubectl wait --for=condition=ready pod -l app=tractionbuild,component=neo4j -n tractionbuild

# Deploy tractionbuild application

kubectl apply -f k8s/tractionbuild-deployment.yaml

# Create HPA and Ingress

kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml

```

## Configuration

### Environment Variables

The application is configured through ConfigMaps and Secrets:

**ConfigMap (k8s/configmap.yaml):**

- `NEO4J_URI`: Neo4j connection URI

- `NEO4J_USER`: Neo4j username

- `PROMETHEUS_PORT`: Metrics port

- `MEMORY_FILE_PATH`: Memory file path

- `CREWAI_MEMORY_PATH`: CrewAI memory path

- `HOME`: Home directory

- `LOG_LEVEL`: Logging level

- `ENVIRONMENT`: Environment name

**Secret (k8s/secret.yaml):**

- `NEO4J_PASSWORD`: Neo4j password

- `OPENAI_API_KEY`: OpenAI API key

- `ANTHROPIC_API_KEY`: Anthropic API key

### Resource Requirements

**tractionbuild Application:**

- Requests: 500m CPU, 1Gi memory

- Limits: 2000m CPU, 4Gi memory

**Neo4j Database:**

- Requests: 500m CPU, 1Gi memory

- Limits: 2000m CPU, 4Gi memory

### Storage

The deployment uses Persistent Volumes for:

- Neo4j data (10Gi)

- Neo4j logs (5Gi)

- Application output (20Gi)

- Application data (10Gi)

## Monitoring

### Health Checks

The application includes:

- Liveness probe: `/metrics` endpoint

- Readiness probe: `/metrics` endpoint

- Startup probe: 60s initial delay

### Metrics

Prometheus metrics are available at:

- Endpoint: `/metrics`

- Port: `8000`

### Logging

View application logs:

```bash
kubectl logs -f -l app=tractionbuild,component=app -n tractionbuild

```

## Scaling

### Horizontal Pod Autoscaler

The HPA automatically scales based on:

- CPU utilization (70% target)

- Memory utilization (80% target)

- Min replicas: 3

- Max replicas: 10

### Manual Scaling

Scale manually:

```bash
kubectl scale deployment tractionbuild-app --replicas=5 -n tractionbuild

```

## Access

### Port Forward

For local access:

```bash
kubectl port-forward -n tractionbuild svc/tractionbuild-app 8000:8000

```

### Ingress

The application is exposed via Ingress:

- Host: `tractionbuild.local` (update in k8s/ingress.yaml)

- TLS: Automatic via cert-manager

- Rate limiting: 100 requests per minute

## Troubleshooting

### Common Issues

1. **Image Pull Errors:**
   - Ensure your container registry is accessible
   - Check image pull secrets if using private registry

2. **Neo4j Connection Issues:**
   - Verify Neo4j pod is running: `kubectl get pods -n tractionbuild`
   - Check Neo4j logs: `kubectl logs -l app=tractionbuild,component=neo4j -n tractionbuild`

3. **Storage Issues:**
   - Ensure your cluster has default storage class
   - Check PVC status: `kubectl get pvc -n tractionbuild`

4. **Ingress Issues:**
   - Verify ingress controller is installed
   - Check ingress status: `kubectl get ingress -n tractionbuild`

### Debug Commands

```bash
# Check pod status

kubectl get pods -n tractionbuild

# Check events

kubectl get events -n tractionbuild --sort-by='.lastTimestamp'

# Check resource usage

kubectl top pods -n tractionbuild

# Check HPA status

kubectl get hpa -n tractionbuild

# Check ingress status

kubectl describe ingress tractionbuild-ingress -n tractionbuild

```

## Cleanup

To remove the deployment:

```bash
./k8s/cleanup.sh

```

Or manually:

```bash
kubectl delete namespace tractionbuild

```

## Security Considerations

1. **Secrets Management:**
   - Use Kubernetes secrets for sensitive data
   - Consider using external secret managers (HashiCorp Vault, AWS Secrets Manager)

2. **Network Policies:**
   - Implement network policies to restrict pod-to-pod communication
   - Use service mesh for advanced traffic management

3. **RBAC:**
   - Create dedicated service accounts with minimal permissions
   - Use RBAC to control access to resources

4. **Pod Security:**
   - Run containers as non-root users
   - Use security contexts to restrict capabilities

## Production Considerations

1. **High Availability:**
   - Deploy across multiple availability zones
   - Use anti-affinity rules for pod distribution

2. **Backup:**
   - Implement regular backups of Neo4j data
   - Use Velero for cluster-wide backup

3. **Monitoring:**
   - Set up Prometheus and Grafana
   - Configure alerting for critical metrics

4. **Logging:**
   - Use centralized logging (ELK stack, Fluentd)
   - Implement log retention policies
