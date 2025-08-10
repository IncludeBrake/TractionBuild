# ZeroToShip Monitoring Setup Script
# Sets up Prometheus, Grafana, and alerting for comprehensive monitoring

Write-Host "📊 ZeroToShip Monitoring Setup Script" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# ============================================================================
# STEP 1: INSTALL PROMETHEUS OPERATOR
# ============================================================================
Write-Host "🔧 Step 1: Installing Prometheus Operator..." -ForegroundColor Yellow

# Add Prometheus Operator Helm repository
Write-Host "  - Adding Prometheus Operator Helm repository..." -ForegroundColor Cyan
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus Operator
Write-Host "  - Installing Prometheus Operator..." -ForegroundColor Cyan
helm install prometheus prometheus-community/kube-prometheus-stack `
    --namespace monitoring `
    --create-namespace `
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false `
    --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false `
    --set prometheus.prometheusSpec.ruleSelectorNilUsesHelmValues=false `
    --set prometheus.prometheusSpec.probeSelectorNilUsesHelmValues=false

Write-Host "✅ Prometheus Operator installed" -ForegroundColor Green

# ============================================================================
# STEP 2: CREATE ZEROTOSHIP MONITORING CONFIGURATION
# ============================================================================
Write-Host "📋 Step 2: Creating ZeroToShip monitoring configuration..." -ForegroundColor Yellow

# Create ServiceMonitor for ZeroToShip
$serviceMonitorYaml = @"
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: zerotoship-monitor
  namespace: zerotoship
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: zerotoship
      component: app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - zerotoship
"@

$serviceMonitorYaml | kubectl apply -f -
Write-Host "✅ ServiceMonitor created" -ForegroundColor Green

# Create PodMonitor for detailed pod metrics
$podMonitorYaml = @"
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: zerotoship-pod-monitor
  namespace: zerotoship
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: zerotoship
  podMetricsEndpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - zerotoship
"@

$podMonitorYaml | kubectl apply -f -
Write-Host "✅ PodMonitor created" -ForegroundColor Green

# ============================================================================
# STEP 3: APPLY ALERTING RULES
# ============================================================================
Write-Host "🚨 Step 3: Applying alerting rules..." -ForegroundColor Yellow

# Apply storage alerting rules
Write-Host "  - Applying storage alerting rules..." -ForegroundColor Cyan
kubectl apply -f k8s/prometheus-pvc-rules.yaml

# Create application-specific alerting rules
$appAlertsYaml = @"
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: zerotoship-app-alerts
  namespace: zerotoship
  labels:
    prometheus: kube-prometheus
    role: alert-rules
spec:
  groups:
  - name: zerotoship.application
    rules:
    # Alert when application is down
    - alert: ZeroToShipAppDown
      expr: up{app="zerotoship"} == 0
      for: 1m
      labels:
        severity: critical
        component: application
      annotations:
        summary: "ZeroToShip application is down"
        description: "ZeroToShip application has been down for more than 1 minute."
        
    # Alert when application is slow to respond
    - alert: ZeroToShipAppSlow
      expr: http_request_duration_seconds{app="zerotoship"} > 5
      for: 2m
      labels:
        severity: warning
        component: application
      annotations:
        summary: "ZeroToShip application is responding slowly"
        description: "ZeroToShip application is taking more than 5 seconds to respond."
        
    # Alert when memory usage is high
    - alert: ZeroToShipHighMemory
      expr: container_memory_usage_bytes{container="zerotoship"} / container_spec_memory_limit_bytes{container="zerotoship"} > 0.8
      for: 5m
      labels:
        severity: warning
        component: application
      annotations:
        summary: "ZeroToShip application memory usage is high"
        description: "ZeroToShip application is using more than 80% of its memory limit."
        
    # Alert when CPU usage is high
    - alert: ZeroToShipHighCPU
      expr: rate(container_cpu_usage_seconds_total{container="zerotoship"}[5m]) > 0.8
      for: 5m
      labels:
        severity: warning
        component: application
      annotations:
        summary: "ZeroToShip application CPU usage is high"
        description: "ZeroToShip application is using more than 80% of its CPU limit."
        
    # Alert when Neo4j connection is down
    - alert: Neo4jConnectionDown
      expr: up{app="neo4j"} == 0
      for: 1m
      labels:
        severity: critical
        component: database
      annotations:
        summary: "Neo4j database connection is down"
        description: "Neo4j database has been down for more than 1 minute."
"@

$appAlertsYaml | kubectl apply -f -
Write-Host "✅ Application alerting rules created" -ForegroundColor Green

# ============================================================================
# STEP 4: SETUP GRAFANA DASHBOARDS
# ============================================================================
Write-Host "📈 Step 4: Setting up Grafana dashboards..." -ForegroundColor Yellow

# Create ConfigMap for Grafana dashboard
$dashboardConfigMap = @"
apiVersion: v1
kind: ConfigMap
metadata:
  name: zerotoship-grafana-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  zerotoship-dashboard.json: |
    {
      "dashboard": {
        "id": null,
        "title": "ZeroToShip Application Dashboard",
        "tags": ["zerotoship", "application"],
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Application Status",
            "type": "stat",
            "targets": [
              {
                "expr": "up{app=\"zerotoship\"}",
                "legendFormat": "{{pod}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {
                  "mode": "thresholds"
                },
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "green", "value": 1}
                  ]
                }
              }
            }
          },
          {
            "id": 2,
            "title": "Memory Usage",
            "type": "graph",
            "targets": [
              {
                "expr": "container_memory_usage_bytes{container=\"zerotoship\"} / 1024 / 1024",
                "legendFormat": "{{pod}} - Memory (MB)"
              }
            ]
          },
          {
            "id": 3,
            "title": "CPU Usage",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(container_cpu_usage_seconds_total{container=\"zerotoship\"}[5m]) * 100",
                "legendFormat": "{{pod}} - CPU (%)"
              }
            ]
          },
          {
            "id": 4,
            "title": "HTTP Request Duration",
            "type": "graph",
            "targets": [
              {
                "expr": "http_request_duration_seconds{app=\"zerotoship\"}",
                "legendFormat": "{{method}} {{endpoint}}"
              }
            ]
          }
        ],
        "time": {
          "from": "now-1h",
          "to": "now"
        },
        "refresh": "30s"
      }
    }
"@

$dashboardConfigMap | kubectl apply -f -
Write-Host "✅ Grafana dashboard created" -ForegroundColor Green

# ============================================================================
# STEP 5: SETUP ALERTMANAGER CONFIGURATION
# ============================================================================
Write-Host "📢 Step 5: Setting up AlertManager configuration..." -ForegroundColor Yellow

# Create AlertManager configuration
$alertManagerConfig = @"
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-config
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://127.0.0.1:5001/'
    inhibit_rules:
      - source_match:
          severity: 'critical'
        target_match:
          severity: 'warning'
        equal: ['alertname', 'dev', 'instance']
"@

$alertManagerConfig | kubectl apply -f -
Write-Host "✅ AlertManager configuration created" -ForegroundColor Green

# ============================================================================
# STEP 6: VERIFY MONITORING SETUP
# ============================================================================
Write-Host "✅ Step 6: Verifying monitoring setup..." -ForegroundColor Yellow

# Wait for Prometheus to be ready
Write-Host "  - Waiting for Prometheus to be ready..." -ForegroundColor Cyan
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s

# Wait for Grafana to be ready
Write-Host "  - Waiting for Grafana to be ready..." -ForegroundColor Cyan
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s

# Check monitoring components
Write-Host "  - Checking monitoring components..." -ForegroundColor Cyan
kubectl get pods -n monitoring

# Check ServiceMonitors
Write-Host "  - Checking ServiceMonitors..." -ForegroundColor Cyan
kubectl get servicemonitors -n zerotoship

# Check PrometheusRules
Write-Host "  - Checking PrometheusRules..." -ForegroundColor Cyan
kubectl get prometheusrules -n zerotoship

# ============================================================================
# STEP 7: SETUP PORT FORWARDING FOR ACCESS
# ============================================================================
Write-Host "🔌 Step 7: Setting up port forwarding for monitoring access..." -ForegroundColor Yellow

Write-Host "  - Grafana will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  - Prometheus will be available at: http://localhost:9090" -ForegroundColor Cyan
Write-Host "  - AlertManager will be available at: http://localhost:9093" -ForegroundColor Cyan

# Create port forwarding script
$portForwardScript = @"
# ZeroToShip Monitoring Port Forward Script
# Run this script to access monitoring dashboards

Write-Host "🔌 Setting up port forwarding for monitoring..." -ForegroundColor Green

# Grafana
Start-Job -ScriptBlock { kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring }
Write-Host "✅ Grafana: http://localhost:3000 (admin/prom-operator)" -ForegroundColor Green

# Prometheus
Start-Job -ScriptBlock { kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring }
Write-Host "✅ Prometheus: http://localhost:9090" -ForegroundColor Green

# AlertManager
Start-Job -ScriptBlock { kubectl port-forward svc/prometheus-kube-prometheus-alertmanager 9093:9093 -n monitoring }
Write-Host "✅ AlertManager: http://localhost:9093" -ForegroundColor Green

Write-Host ""
Write-Host "📊 Monitoring Setup Complete!" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop port forwarding" -ForegroundColor Yellow
"@

$portForwardScript | Out-File -FilePath "k8s/monitoring-port-forward.ps1" -Encoding UTF8
Write-Host "✅ Port forwarding script created: k8s/monitoring-port-forward.ps1" -ForegroundColor Green

# ============================================================================
# STEP 8: SUMMARY AND NEXT STEPS
# ============================================================================
Write-Host ""
Write-Host "🎉 ZeroToShip Monitoring Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Monitoring Components Installed:" -ForegroundColor Cyan
Write-Host "✅ Prometheus Operator with Prometheus"
Write-Host "✅ Grafana with ZeroToShip dashboard"
Write-Host "✅ AlertManager for alerting"
Write-Host "✅ ServiceMonitor for ZeroToShip metrics"
Write-Host "✅ PodMonitor for detailed pod metrics"
Write-Host "✅ Comprehensive alerting rules"
Write-Host ""
Write-Host "🔍 Access Monitoring:" -ForegroundColor Yellow
Write-Host "• Run: .\k8s\monitoring-port-forward.ps1"
Write-Host "• Grafana: http://localhost:3000 (admin/prom-operator)"
Write-Host "• Prometheus: http://localhost:9090"
Write-Host "• AlertManager: http://localhost:9093"
Write-Host ""
Write-Host "📋 Key Metrics Monitored:" -ForegroundColor Cyan
Write-Host "• Application availability and health"
Write-Host "• Memory and CPU usage"
Write-Host "• HTTP request duration"
Write-Host "• Storage usage and PVC status"
Write-Host "• Neo4j database connectivity"
Write-Host ""
Write-Host "🚨 Alerts Configured:" -ForegroundColor Yellow
Write-Host "• Application down (critical)"
Write-Host "• Slow response times (warning)"
Write-Host "• High resource usage (warning)"
Write-Host "• Storage issues (warning/critical)"
Write-Host "• Database connectivity (critical)"
Write-Host ""
Write-Host "🔧 Next Steps:" -ForegroundColor Green
Write-Host "1. Access Grafana and import the ZeroToShip dashboard"
Write-Host "2. Configure additional alerting channels (email, Slack, etc.)"
Write-Host "3. Set up log aggregation with ELK stack if needed"
Write-Host "4. Configure backup and retention policies"
Write-Host "5. Test alerting by scaling down the application"
