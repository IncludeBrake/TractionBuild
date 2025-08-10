# ZeroToShip Storage Troubleshooting Guide

## Overview
This guide helps resolve PersistentVolumeClaim (PVC) access mode conflicts and storage provisioning issues in Kubernetes.

## Quick Fix Script
Run the automated fix script:
```powershell
.\k8s\fix-storage.ps1
```

## Manual Steps

### 1. Delete Existing PVCs
```bash
kubectl delete pvc zerotoship-data-pvc zerotoship-output-pvc -n zerotoship
```

### 2. Configure Local-Path as Default Storage Class
```bash
# Remove default from standard storage class
kubectl patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'

# Set local-path as default
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

### 3. Apply Updated Deployment
```bash
kubectl apply -f k8s/zerotoship-deployment.yaml
```

## Storage Configuration Details

### PVC Specifications
- **Access Mode**: `ReadWriteOnce` (suitable for single-node clusters)
- **Storage Class**: `local-path` (faster local storage)
- **Data PVC**: 10Gi for application data
- **Output PVC**: 20Gi for workflow outputs

### Why ReadWriteOnce?
- Compatible with single-node clusters (Kind/Minikube)
- Prevents access mode conflicts
- Suitable for most development scenarios

## Monitoring and Alerts

### Apply Prometheus Rules
```bash
kubectl apply -f k8s/prometheus-pvc-rules.yaml
```

### Key Metrics to Monitor
- PVC binding time (>10s triggers alert)
- Storage usage (>80% warning, >95% critical)
- Local-path-provisioner status
- Pod creation delays due to storage

## Common Issues and Solutions

### Issue: PVC Stuck in Pending
**Symptoms**: PVC remains in Pending state
**Solutions**:
1. Check storage class availability:
   ```bash
   kubectl get storageclass
   ```
2. Verify local-path-provisioner is running:
   ```bash
   kubectl get pods -n kube-system | grep local-path-provisioner
   ```
3. Check events for errors:
   ```bash
   kubectl get events -n zerotoship --sort-by='.lastTimestamp'
   ```

### Issue: Access Mode Conflicts
**Symptoms**: Error about changing access modes
**Solutions**:
1. Delete existing PVCs completely
2. Ensure consistent `ReadWriteOnce` configuration
3. Reapply deployment

### Issue: Slow PVC Binding
**Symptoms**: PVCs take >10s to bind
**Solutions**:
1. Use local-path storage class
2. Ensure adequate node resources
3. Consider multi-node cluster for production

### Issue: Storage Class Not Found
**Symptoms**: "storage class not found" errors
**Solutions**:
1. Install local-path-provisioner:
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
   ```
2. Set as default storage class
3. Verify with `kubectl get storageclass`

## Performance Optimization

### For Development (Single-Node)
- Use `local-path` storage class
- Keep PVC sizes reasonable (10-20Gi)
- Monitor storage usage regularly

### For Production (Multi-Node)
- Consider `ReadWriteMany` for shared access
- Use enterprise storage solutions
- Implement storage quotas and limits

## Verification Commands

### Check PVC Status
```bash
kubectl get pvc -n zerotoship
kubectl describe pvc zerotoship-data-pvc -n zerotoship
kubectl describe pvc zerotoship-output-pvc -n zerotoship
```

### Check Storage Classes
```bash
kubectl get storageclass
kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

### Check Pod Status
```bash
kubectl get pods -n zerotoship -l app=zerotoship
kubectl describe pod <pod-name> -n zerotoship
```

### Check Events
```bash
kubectl get events -n zerotoship --sort-by='.lastTimestamp'
kubectl get events --all-namespaces | grep -i storage
```

## Advanced Configuration

### Custom Storage Class
If you need a custom storage class:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: custom-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: custom-provisioner
parameters:
  type: ssd
```

### Storage Quotas
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: zerotoship
spec:
  hard:
    persistentvolumeclaims: "10"
    requests.storage: "100Gi"
```

## Support and Debugging

### Enable Verbose Logging
```bash
kubectl logs -f deployment/zerotoship-app -n zerotoship
kubectl logs -f -n kube-system -l app=local-path-provisioner
```

### Collect Debug Information
```bash
# PVC and PV information
kubectl get pvc,pv -n zerotoship -o wide

# Storage class details
kubectl get storageclass -o yaml

# Node storage capacity
kubectl describe nodes | grep -A 10 "Allocated resources"
```

### Contact Information
For persistent issues:
1. Check cluster events and logs
2. Verify storage provisioner status
3. Review resource constraints
4. Consider cluster scaling if needed
