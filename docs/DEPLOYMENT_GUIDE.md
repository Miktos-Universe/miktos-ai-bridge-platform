# 🚀 Miktos AI Bridge Platform - Deployment Guide

## Production Deployment for AI-Powered 3D Automation Platform

This comprehensive deployment guide covers everything needed to deploy the Miktos AI Bridge Platform in production environments.

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#-pre-deployment-checklist)
2. [Infrastructure Requirements](#️-infrastructure-requirements)
3. [Docker Deployment](#-docker-deployment)
4. [Kubernetes Deployment](#️-kubernetes-deployment)
5. [Cloud Provider Setup](#️-cloud-provider-setup)
6. [Security Configuration](#-security-configuration)
7. [Monitoring & Logging](#-monitoring--logging)
8. [Backup & Recovery](#-backup--recovery)
9. [Performance Optimization](#-performance-optimization)
10. [Troubleshooting](#-troubleshooting)

---

## ✅ Pre-Deployment Checklist

### Environment Validation

- [ ] **Python 3.9+** installed and configured
- [ ] **Blender 3.0+** available on deployment target
- [ ] **Docker** and **Docker Compose** installed
- [ ] **SSL certificates** obtained for HTTPS
- [ ] **Domain name** configured and DNS updated
- [ ] **Database** (PostgreSQL/MySQL) set up
- [ ] **Redis** cache server configured
- [ ] **Load balancer** configured (if using multiple instances)

### Configuration Files

- [ ] `config.production.yaml` prepared
- [ ] Environment variables defined
- [ ] API keys and secrets secured
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented

### Security Requirements

- [ ] **Authentication** method chosen (API key, OAuth, JWT)
- [ ] **Rate limiting** configured
- [ ] **CORS** settings defined
- [ ] **Input validation** enabled
- [ ] **Audit logging** configured
- [ ] **Security headers** implemented

---

## 🏗️ Infrastructure Requirements

### Minimum Production Requirements

**Single Instance Deployment:**

- **CPU**: 4 cores (2.4GHz+)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB SSD
- **Network**: 100Mbps bandwidth
- **OS**: Ubuntu 20.04 LTS, CentOS 8, or RHEL 8

**High Availability Deployment:**

- **Load Balancer**: 2 instances (2 cores, 4GB RAM each)
- **Application Servers**: 3+ instances (4 cores, 16GB RAM each)
- **Database**: Primary + Replica (4 cores, 8GB RAM each)
- **Cache**: Redis cluster (2 cores, 4GB RAM per node)
- **Storage**: Shared NFS or cloud storage

### Network Architecture

```text
Internet
    ↓
Load Balancer (HAProxy/Nginx)
    ↓
Application Servers (3+ instances)
    ↓
Database Cluster (PostgreSQL)
    ↓
Cache Layer (Redis)
```

### Port Configuration

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| HTTP | 80 | TCP | Web traffic (redirect to HTTPS) |
| HTTPS | 443 | TCP | Secure web traffic |
| API | 8000 | TCP | REST API endpoints |
| Viewer | 8080 | TCP | Real-time 3D viewer |
| WebSocket | 8001 | TCP | Real-time updates |
| Metrics | 9090 | TCP | Prometheus metrics |
| Health | 8090 | TCP | Health check endpoint |

---

## 🐳 Docker Deployment

### Production Dockerfile

```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    blender \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 miktos && \
    mkdir -p /app /data /logs && \
    chown -R miktos:miktos /app /data /logs

USER miktos
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.production.txt ./
RUN pip install --no-cache-dir -r requirements.production.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs output cache

# Expose ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "main.py", "--server", "--production"]
```

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  miktos-app:
    build:
      context: .
      dockerfile: Dockerfile.production
    environment:
      - MIKTOS_ENV=production
      - MIKTOS_LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://miktos:${DB_PASSWORD}@postgres:5432/miktos
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
      - "8080:8080"
    volumes:
      - ./data:/data
      - ./logs:/app/logs
      - ./cache:/app/cache
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - miktos-network

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=miktos
      - POSTGRES_USER=miktos
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - miktos-network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - miktos-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/private
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - miktos-app
    restart: unless-stopped
    networks:
      - miktos-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped
    networks:
      - miktos-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped
    networks:
      - miktos-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  miktos-network:
    driver: bridge
```

### Environment Configuration

```bash
# .env.production
MIKTOS_ENV=production
SECRET_KEY=your-super-secret-key-here
DB_PASSWORD=secure-database-password
GRAFANA_PASSWORD=grafana-admin-password

# SSL Configuration
SSL_CERT_PATH=/etc/ssl/private/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem

# Performance Tuning
MIKTOS_WORKERS=4
MIKTOS_MAX_MEMORY=4096
MIKTOS_CACHE_SIZE=1024
```

### Deployment Commands

```bash
# Prepare environment
cp config.template.yaml config.production.yaml
cp .env.template .env.production

# Build and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs miktos-app

# Health check
curl http://localhost:8000/health
```

---

## ☸️ Kubernetes Deployment

### Namespace Configuration

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: miktos-platform
  labels:
    name: miktos-platform
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: miktos-config
  namespace: miktos-platform
data:
  config.yaml: |
    environment: production
    
    logging:
      level: INFO
      file: /app/logs/miktos.log
      
    performance:
      auto_optimize: true
      max_workers: 4
      
    database:
      url: postgresql://miktos:password@postgres:5432/miktos
      
    cache:
      redis_url: redis://redis:6379/0
      
    security:
      enable_auth: true
      cors_enabled: true
      allowed_origins:
        - "https://your-domain.com"
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: miktos-secrets
  namespace: miktos-platform
type: Opaque
data:
  secret-key: <base64-encoded-secret-key>
  db-password: <base64-encoded-db-password>
  api-key: <base64-encoded-api-key>
```

### Application Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: miktos-app
  namespace: miktos-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: miktos-app
  template:
    metadata:
      labels:
        app: miktos-app
    spec:
      containers:
      - name: miktos-app
        image: miktos-platform:latest
        ports:
        - containerPort: 8000
        - containerPort: 8080
        env:
        - name: MIKTOS_ENV
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: miktos-secrets
              key: secret-key
        - name: DATABASE_URL
          value: "postgresql://miktos:$(DB_PASSWORD)@postgres:5432/miktos"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: miktos-secrets
              key: db-password
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: data-volume
          mountPath: /data
        - name: logs-volume
          mountPath: /app/logs
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: miktos-config
      - name: data-volume
        persistentVolumeClaim:
          claimName: miktos-data-pvc
      - name: logs-volume
        persistentVolumeClaim:
          claimName: miktos-logs-pvc
```

### Services

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: miktos-service
  namespace: miktos-platform
spec:
  selector:
    app: miktos-app
  ports:
  - name: api
    port: 8000
    targetPort: 8000
  - name: viewer
    port: 8080
    targetPort: 8080
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: miktos-loadbalancer
  namespace: miktos-platform
spec:
  selector:
    app: miktos-app
  ports:
  - name: api
    port: 8000
    targetPort: 8000
  - name: viewer
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: miktos-ingress
  namespace: miktos-platform
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.miktos.com
    secretName: miktos-tls
  rules:
  - host: api.miktos.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: miktos-service
            port:
              number: 8000
  - host: viewer.miktos.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: miktos-service
            port:
              number: 8080
```

### Persistent Storage

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: miktos-data-pvc
  namespace: miktos-platform
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: miktos-logs-pvc
  namespace: miktos-platform
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 20Gi
  storageClassName: standard
```

### Kubernetes Deployment Commands

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Verify deployment
kubectl get pods -n miktos-platform
kubectl get services -n miktos-platform
kubectl logs -f deployment/miktos-app -n miktos-platform

# Scale deployment
kubectl scale deployment miktos-app --replicas=5 -n miktos-platform
```

---

## ☁️ Cloud Provider Setup

### AWS Deployment

#### ECS with Fargate

```yaml
# aws-ecs-task-definition.json
{
  "family": "miktos-platform",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "miktos-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/miktos-platform:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        },
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MIKTOS_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:miktos/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/miktos-platform",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name miktos-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345 \
  --scheme internet-facing \
  --type application

# Create target group
aws elbv2 create-target-group \
  --name miktos-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-12345 \
  --health-check-path /health
```

#### RDS Database

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier miktos-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 14.7 \
  --allocated-storage 100 \
  --storage-type gp2 \
  --db-name miktos \
  --master-username miktos \
  --master-user-password secure-password \
  --vpc-security-group-ids sg-database \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/miktos-platform

# Deploy to Cloud Run
gcloud run deploy miktos-platform \
  --image gcr.io/PROJECT_ID/miktos-platform \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars MIKTOS_ENV=production
```

#### Cloud SQL Database

```bash
# Create Cloud SQL instance
gcloud sql instances create miktos-postgres \
  --database-version POSTGRES_14 \
  --tier db-custom-2-4096 \
  --region us-central1 \
  --backup-start-time 02:00 \
  --enable-bin-log \
  --maintenance-release-channel production
```

### Azure Deployment

#### Container Instances

```bash
# Create resource group
az group create --name miktos-rg --location eastus

# Create container instance
az container create \
  --resource-group miktos-rg \
  --name miktos-platform \
  --image miktos-platform:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 8080 \
  --environment-variables MIKTOS_ENV=production \
  --restart-policy Always
```

---

## 🔒 Security Configuration

### SSL/TLS Setup

#### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.miktos.com -d viewer.miktos.com

# Test renewal
sudo certbot renew --dry-run

# Auto-renewal cron job
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

#### Manual Certificate Installation

```bash
# Create certificate directory
sudo mkdir -p /etc/ssl/private

# Install certificates
sudo cp certificate.crt /etc/ssl/private/
sudo cp private.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/*
```

### Nginx Security Configuration

```nginx
# nginx.security.conf
server {
    listen 443 ssl http2;
    server_name api.miktos.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/private/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://miktos-app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Security
        proxy_hide_header X-Powered-By;
        proxy_set_header X-Forwarded-Host $host;
    }
}
```

### Application Security

```yaml
# security.yaml
security:
  authentication:
    enabled: true
    method: "jwt"
    secret_key: "${SECRET_KEY}"
    token_expiry: 3600
    
  rate_limiting:
    enabled: true
    requests_per_minute: 100
    burst_size: 20
    
  cors:
    enabled: true
    allowed_origins:
      - "https://your-domain.com"
      - "https://app.your-domain.com"
    allowed_methods: ["GET", "POST", "PUT", "DELETE"]
    allowed_headers: ["Authorization", "Content-Type"]
    
  input_validation:
    enabled: true
    max_command_length: 1000
    sanitize_inputs: true
    
  audit_logging:
    enabled: true
    log_file: "/app/logs/audit.log"
    include_ip: true
    include_user_agent: true
```

### Firewall Configuration

```bash
# UFW Firewall Setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 8000  # Internal API access
sudo ufw enable

# iptables rules
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -P INPUT DROP
```

---

## 📊 Monitoring & Logging

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'miktos-platform'
    static_configs:
      - targets: ['miktos-app:8000']
    metrics_path: /metrics
    scrape_interval: 10s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
      
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: miktos-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(miktos_http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
          
      - alert: HighMemoryUsage
        expr: (miktos_memory_usage_bytes / miktos_memory_limit_bytes) > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
          
      - alert: DatabaseConnectionFailure
        expr: miktos_database_connections_active == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "No active database connections"
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Miktos Platform Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(miktos_http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(miktos_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(miktos_http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "Error rate"
          }
        ]
      }
    ]
  }
}
```

### Centralized Logging

```yaml
# fluentd.conf
<source>
  @type tail
  path /app/logs/*.log
  pos_file /var/log/fluentd/miktos.log.pos
  tag miktos.*
  format json
</source>

<match miktos.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name miktos
  type_name logs
</match>
```

---

## 💾 Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database"
DB_NAME="miktos"
DB_USER="miktos"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h postgres -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/miktos_$DATE.sql.gz

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/miktos_$DATE.sql.gz s3://miktos-backups/database/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: miktos_$DATE.sql.gz"
```

### Application Data Backup

```bash
#!/bin/bash
# backup_application.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/application"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application data
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz \
  /data \
  /app/logs \
  /app/cache \
  /app/config

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/app_data_$DATE.tar.gz s3://miktos-backups/application/

# Clean old backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Application backup completed: app_data_$DATE.tar.gz"
```

### Automated Backup Schedule

```bash
# Crontab entries
0 2 * * * /scripts/backup_database.sh
0 3 * * * /scripts/backup_application.sh
0 4 * * 0 /scripts/backup_full_system.sh  # Weekly full backup
```

### Recovery Procedures

```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop application
docker-compose stop miktos-app

# Restore database
gunzip -c $BACKUP_FILE | psql -h postgres -U miktos -d miktos

# Start application
docker-compose start miktos-app

echo "Database restore completed"
```

---

## ⚡ Performance Optimization

### Application Tuning

```yaml
# performance.yaml
performance:
  workers: 4
  max_connections: 1000
  keep_alive_timeout: 65
  
  caching:
    enabled: true
    backend: "redis"
    default_timeout: 300
    max_entries: 10000
    
  optimization:
    auto_optimize: true
    enable_compression: true
    enable_http2: true
    
  resources:
    max_memory_mb: 4096
    max_cpu_percent: 80
    gc_threshold: 700
```

### Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();

-- Create indexes
CREATE INDEX CONCURRENTLY idx_workflows_created_at ON workflows(created_at);
CREATE INDEX CONCURRENTLY idx_executions_session_id ON executions(session_id);
CREATE INDEX CONCURRENTLY idx_skills_category ON skills(category);
```

### Redis Configuration

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 60
timeout 0
```

### Load Testing

```bash
# Apache Bench
ab -n 10000 -c 100 http://localhost:8000/api/v1/health

# wrk load testing
wrk -t12 -c400 -d30s --script=post.lua http://localhost:8000/api/v1/execute

# Artillery load testing
artillery run load-test.yml
```

---

## 🔧 Troubleshooting

### Common Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats miktos-app

# Optimize memory
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' >> /etc/sysctl.conf
sysctl -p
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Check connections
docker-compose exec postgres psql -U miktos -d miktos -c "SELECT * FROM pg_stat_activity;"

# Reset connections
docker-compose restart postgres
```

#### SSL Certificate Problems

```bash
# Check certificate expiry
openssl x509 -in /etc/ssl/private/cert.pem -text -noout | grep "Not After"

# Test SSL configuration
openssl s_client -connect api.miktos.com:443 -servername api.miktos.com

# Renew Let's Encrypt certificate
certbot renew --force-renewal
```

### Health Checks

```bash
# Application health
curl -f http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U miktos

# Redis health
docker-compose exec redis redis-cli ping

# Overall system health
curl -f http://localhost:8000/health/detailed
```

### Log Analysis

```bash
# Application logs
docker-compose logs -f miktos-app

# Error patterns
grep -i error /app/logs/miktos.log | tail -50

# Performance analysis
grep "execution_time" /app/logs/miktos.log | awk '{print $5}' | sort -n | tail -10
```

### Performance Debugging

```bash
# Top processes
htop

# Network connections
netstat -tulpn | grep :8000

# Disk I/O
iostat -x 1

# Memory analysis
free -h && cat /proc/meminfo
```

---

## 📞 Support and Maintenance

### Monitoring Checklist

**Daily:**

- [ ] Check application health endpoints
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backup completion

**Weekly:**

- [ ] Review performance metrics
- [ ] Check security updates
- [ ] Analyze user patterns
- [ ] Update documentation

**Monthly:**

- [ ] Security audit
- [ ] Performance optimization review
- [ ] Backup restoration test
- [ ] Capacity planning assessment

### Emergency Procedures

#### Service Outage Response

1. **Immediate Assessment** (0-5 minutes)
   - Check health endpoints
   - Review monitoring dashboards
   - Identify scope of impact

2. **Initial Response** (5-15 minutes)
   - Restart failed services
   - Check resource availability
   - Enable maintenance mode if needed

3. **Detailed Investigation** (15-60 minutes)
   - Analyze logs and metrics
   - Identify root cause
   - Implement temporary fixes

4. **Resolution** (1-4 hours)
   - Deploy permanent fix
   - Verify service restoration
   - Update monitoring and alerts

#### Incident Communication

```bash
# Status page update script
#!/bin/bash
STATUS_PAGE_API="https://api.statuspage.io/v1/pages/YOUR_PAGE_ID"
API_KEY="your-api-key"

curl -X POST \
  -H "Authorization: OAuth $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "incident": {
      "name": "API Performance Degradation",
      "status": "investigating",
      "impact_override": "minor",
      "body": "We are investigating reports of slow API response times."
    }
  }' \
  "$STATUS_PAGE_API/incidents"
```

---

This comprehensive deployment guide provides everything needed to successfully deploy the Miktos AI Bridge Platform in production environments. For additional support and advanced configurations, visit the [complete documentation](https://docs.miktos.ai).

**Miktos AI Bridge Platform** - *Production-ready AI-powered 3D automation*
