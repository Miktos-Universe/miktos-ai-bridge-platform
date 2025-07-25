# 📖 Miktos AI Bridge Platform - Complete User Guide

## Master Guide for AI-Powered 3D Workflow Automation

Welcome to the complete user guide for Miktos AI Bridge Platform. This comprehensive documentation will guide you from installation to advanced usage, ensuring you can leverage the full power of AI-driven 3D automation.

---

## 📋 Table of Contents

1. [Quick Start Guide](#-quick-start-guide)
2. [Installation & Setup](#️-installation--setup)
3. [Basic Usage](#-basic-usage)
4. [Advanced Features](#-advanced-features)
5. [Natural Language Commands](#️-natural-language-commands)
6. [Workflow Automation](#️-workflow-automation)
7. [Performance Optimization](#-performance-optimization)
8. [Troubleshooting](#-troubleshooting)
9. [API Reference](#-api-reference)
10. [Deployment Guide](#-deployment-guide)

---

## 🚀 Quick Start Guide

### System Requirements

**Minimum:**

- Python 3.9+
- Blender 3.0+
- 8GB RAM
- 2GB free disk space

**Recommended:**

- Python 3.11+
- Blender 4.0+
- 16GB RAM
- 5GB free disk space
- GPU with OpenGL 4.3+

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# 2. Run automated setup
python setup.py --auto

# 3. Start the platform
python main.py --interactive

# 4. Test with your first command
miktos> create a metallic cube with size 2x2x2
```

### Your First Success

After setup, you should see:

```text
🚀 Miktos AI Bridge Platform v1.0.0
✓ Blender connection: OK
✓ Skills library: 50+ skills loaded  
✓ Viewer: Running on http://localhost:8080
✓ Agent: Ready for commands

miktos> create a metallic cube with size 2x2x2
✓ Created cube "Cube" with metallic material
✓ Applied size transformation: 2x2x2
✓ Scene updated in viewer
```

---

## 🛠️ Installation & Setup

### Prerequisites Installation

#### macOS

```bash
# Using Homebrew (recommended)
brew install python node blender git

# Manual installation
# Download from respective websites:
# - Python: python.org
# - Node.js: nodejs.org
# - Blender: blender.org
# - Git: git-scm.com
```

#### Windows

```powershell
# Using Chocolatey (recommended)
choco install python nodejs blender git

# Using Winget
winget install Python.Python.3.11
winget install OpenJS.NodeJS
winget install Blender.Blender
winget install Git.Git
```

#### Linux (Ubuntu/Debian)

```bash
# Update package manager
sudo apt update

# Install core dependencies
sudo apt install python3 python3-pip nodejs npm git

# Install Blender
sudo snap install blender --classic
# OR
sudo apt install blender
```

### Platform Installation

#### Method 1: Automated Installation

```bash
# Quick install script
curl -sSL https://raw.githubusercontent.com/Miktos-Universe/miktos-workflows/main/install.sh | bash

# Or with wget
wget -qO- https://raw.githubusercontent.com/Miktos-Universe/miktos-workflows/main/install.sh | bash
```

#### Method 2: Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# 2. Create virtual environment
python -m venv miktos-env
source miktos-env/bin/activate  # Linux/macOS
# miktos-env\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt
npm install

# 4. Initialize configuration
python setup.py --init
```

#### Method 3: Development Installation

```bash
# Clone with development branches
git clone --recursive https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install
```

### Configuration Setup

#### Basic Configuration

```bash
# Initialize with defaults
python setup.py --config-basic

# This creates config.yaml with:
# - Default Blender path
# - Basic skill library
# - Local viewer settings
```

#### Advanced Configuration

```bash
# Full configuration wizard
python setup.py --config-advanced

# Custom configuration
python setup.py --config-file custom-config.yaml
```

#### Environment Variables

```bash
# Required environment variables
export MIKTOS_BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"
export MIKTOS_SKILLS_DIR="./skills"
export MIKTOS_VIEWER_PORT=8080

# Optional advanced settings
export MIKTOS_LOG_LEVEL=INFO
export MIKTOS_AI_PROVIDER=openai
export MIKTOS_API_KEY=your_api_key_here
```

### Verification

#### System Check

```bash
# Run comprehensive system check
python main.py --check-system

# Expected output:
# ✓ Python version: 3.11.x
# ✓ Blender found: /path/to/blender
# ✓ Dependencies: All installed
# ✓ Skills library: 50+ skills loaded
# ✓ Viewer: Port 8080 available
# ✓ AI integration: Ready
```

#### First Test

```bash
# Start in test mode
python main.py --test

# Run example commands
miktos> test basic_cube
miktos> test material_application
miktos> test viewer_update
```

---

## 📁 Basic Usage

### Starting the Platform

#### Interactive Mode

```bash
# Start with interactive console
python main.py --interactive

# Advanced interactive mode
python main.py --interactive --debug
```

#### Background Service

```bash
# Start as background service
python main.py --daemon

# Check service status
python main.py --status

# Stop service
python main.py --stop
```

#### Web Interface

```bash
# Start with web interface only
python main.py --web-only

# Access at: http://localhost:8080
```

### Essential Commands

#### Object Creation

```python
# Basic shapes
miktos> create cube
miktos> create sphere radius=2
miktos> create cylinder height=4 radius=1.5

# Advanced objects
miktos> create parametric_object type=torus major_radius=3 minor_radius=1
miktos> create mesh_from_file "path/to/model.obj"
```

#### Material Application

```python
# Basic materials
miktos> apply_material metallic color=silver
miktos> apply_material glass transparency=0.8
miktos> apply_material emission strength=2.0 color=blue

# Custom materials
miktos> create_material_pbr roughness=0.2 metallic=0.8 base_color=gold
```

#### Scene Management

```python
# Camera operations
miktos> move_camera position=[5,5,5] target=[0,0,0]
miktos> set_camera_preset "top_view"

# Lighting
miktos> add_light type=sun energy=3.0 angle=45
miktos> setup_three_point_lighting
```

### File Operations

#### Saving and Loading

```python
# Save current scene
miktos> save_scene "my_project.blend"

# Load existing scene
miktos> load_scene "existing_project.blend"

# Export options
miktos> export_scene format=obj output="./exports/"
miktos> export_scene format=gltf include_materials=true
```

#### Project Management

```python
# Create new project
miktos> new_project "ProductVisualization"

# Switch projects
miktos> switch_project "ArchitecturalViz"

# List projects
miktos> list_projects
```

---

## 🎯 Advanced Features

### Workflow Automation

#### Creating Workflows

```python
# Define a custom workflow
miktos> create_workflow "product_render_pipeline"
miktos> add_step "import_cad_model"
miktos> add_step "apply_materials_auto"
miktos> add_step "setup_studio_lighting"
miktos> add_step "render_360_views"
miktos> save_workflow
```

#### Running Workflows

```python
# Execute predefined workflow
miktos> run_workflow "product_render_pipeline" input="model.step"

# Batch processing
miktos> batch_workflow "product_render_pipeline" input_dir="./cad_files/"
```

### Custom Skills Development

#### Creating a Skill

```python
# Generate skill template
miktos> generate_skill "custom_extrude"

# Edit the generated skill file
# skills/custom_extrude.py will be created
```

#### Skill Structure

```python
from miktos.core.skill import Skill

class CustomExtrudeSkill(Skill):
    def __init__(self):
        super().__init__(
            name="custom_extrude",
            description="Performs custom extrusion with parameters",
            parameters={
                "distance": {"type": "float", "default": 1.0},
                "direction": {"type": "vector", "default": [0, 0, 1]}
            }
        )
    
    def execute(self, context, **kwargs):
        # Implementation here
        distance = kwargs.get('distance', 1.0)
        direction = kwargs.get('direction', [0, 0, 1])
        
        # Blender operations
        result = self.blender.extrude_selected(distance, direction)
        
        return {
            "success": True,
            "result": result,
            "message": f"Extruded {distance} units"
        }
```

### AI Integration

#### Custom AI Providers

```python
# Configure custom AI provider
miktos> config set ai.provider "custom"
miktos> config set ai.custom.endpoint "https://api.custom-ai.com/v1"
miktos> config set ai.custom.api_key "your_api_key"
```

#### Natural Language Processing

```python
# Train custom command patterns
miktos> train_nlp_pattern "make it shiny" -> "apply_material metallic=1.0"
miktos> train_nlp_pattern "rotate {degrees} degrees" -> "rotate_object angle={degrees}"
```

### Performance Optimization

#### Parallel Processing

```python
# Enable parallel execution
miktos> config set performance.parallel true
miktos> config set performance.max_workers 4

# Batch operations with parallelization
miktos> batch_parallel "apply_material" objects=["Cube", "Sphere", "Cylinder"]
```

#### Memory Management

```python
# Configure memory limits
miktos> config set performance.memory_limit "4GB"
miktos> config set performance.auto_cleanup true

# Manual cleanup
miktos> cleanup_memory
miktos> optimize_scene
```

---

## 🗣️ Natural Language Commands

### Command Categories

#### Object Manipulation

- **"Create a red metallic sphere"**
  - Parsed as: `create_sphere() -> apply_material(metallic, color=red)`

- **"Move the cube 3 units to the right"**
  - Parsed as: `translate_object(target="Cube", vector=[3,0,0])`

- **"Scale everything by 150%"**
  - Parsed as: `scale_objects(factor=1.5, selection="all")`

#### Scene Composition

- **"Set up a three-point lighting system"**
  - Parsed as: `setup_three_point_lighting(key_intensity=3.0)`

- **"Position camera for product shot"**
  - Parsed as: `set_camera_preset("product_shot")`

- **"Add a studio environment"**
  - Parsed as: `load_environment("studio_neutral")`

#### Advanced Workflows

- **"Create a product visualization for this CAD file"**
  - Initiates multi-step workflow:
    1. Import CAD file
    2. Auto-apply materials
    3. Set up lighting
    4. Position camera
    5. Configure render settings

### Custom Command Training

#### Adding Patterns

```python
# Simple pattern mapping
miktos> add_pattern "make {object} transparent" -> "apply_material material=glass target={object}"

# Complex pattern with conditions
miktos> add_pattern "render {quality} quality" -> {
    "high": "set_render_quality samples=1024 resolution=4K",
    "medium": "set_render_quality samples=512 resolution=2K", 
    "low": "set_render_quality samples=128 resolution=1K"
}
```

#### Context Awareness

```python
# Context-dependent commands
miktos> enable_context_awareness true

# Now these work intelligently:
miktos> "make it bigger"  # Scales selected object
miktos> "add some glow"   # Adds emission to selected material
miktos> "duplicate this"  # Duplicates active object
```

---

## ⚙️ Workflow Automation

### Predefined Workflows

#### Product Visualization

```python
# Standard product pipeline
miktos> workflow run product_viz input="model.obj" style="studio"

# Workflow steps:
# 1. Import model with cleanup
# 2. Auto-generate materials
# 3. Studio lighting setup
# 4. Camera positioning
# 5. Render multiple angles
```

#### Architectural Visualization

```python
# Architecture pipeline
miktos> workflow run arch_viz input="building.fbx" time="golden_hour"

# Workflow steps:
# 1. Import with proper scale
# 2. Material assignment by object name
# 3. Environment setup (HDRI)
# 4. Realistic lighting
# 5. Interior/exterior views
```

#### Animation Workflow

```python
# Character animation pipeline
miktos> workflow run char_anim input="character.blend" motion="walk_cycle"

# Workflow steps:
# 1. Load character rig
# 2. Apply motion capture data
# 3. Cleanup and retargeting
# 4. Camera animation
# 5. Export animation
```

### Custom Workflow Creation

#### Workflow Definition

```yaml
# workflow_config.yaml
name: "custom_product_render"
description: "Custom product rendering pipeline"
version: "1.0"

parameters:
  input_file: {type: "file", required: true}
  material_style: {type: "choice", options: ["metallic", "plastic", "glass"]}
  render_quality: {type: "choice", options: ["preview", "final"]}

steps:
  - name: "import_model"
    skill: "import_mesh"
    parameters:
      file: "${input_file}"
      cleanup: true
      
  - name: "apply_materials"
    skill: "auto_material"
    parameters:
      style: "${material_style}"
      
  - name: "setup_lighting"
    skill: "studio_lighting"
    
  - name: "render"
    skill: "batch_render"
    parameters:
      quality: "${render_quality}"
      views: ["front", "back", "side", "top"]
```

#### Workflow Execution

```python
# Load and execute custom workflow
miktos> workflow load "workflow_config.yaml"
miktos> workflow run custom_product_render input="product.obj" material_style="metallic"
```

### Batch Processing

#### File Batch Operations

```python
# Process entire directory
miktos> batch_process directory="./models/" workflow="product_viz"

# With filtering
miktos> batch_process directory="./models/" filter="*.obj" workflow="product_viz"

# Parallel processing
miktos> batch_process directory="./models/" workflow="product_viz" parallel=true workers=4
```

#### Queue Management

```python
# Add to processing queue
miktos> queue add workflow="arch_viz" input="building1.fbx"
miktos> queue add workflow="arch_viz" input="building2.fbx"

# Monitor queue
miktos> queue status
miktos> queue progress

# Process queue
miktos> queue process
```

---

## 🚀 Performance Optimization

### System Optimization

#### Hardware Configuration

```python
# GPU optimization
miktos> config set render.device "GPU"
miktos> config set render.gpu_memory_limit "8GB"

# CPU optimization  
miktos> config set performance.cpu_threads 8
miktos> config set performance.priority "high"
```

#### Memory Optimization

```python
# Memory optimization
miktos> config set memory.auto_cleanup true
miktos> config set memory.threshold "80%"

# Manual optimization
miktos> optimize memory
miktos> optimize scene
miktos> cleanup unused
```

### Rendering Optimization

#### Quality vs Speed Settings

```python
# Fast preview mode
miktos> render_mode preview
miktos> set_samples 32
miktos> set_resolution 1080p

# Production quality
miktos> render_mode production  
miktos> set_samples 1024
miktos> set_resolution 4K
miktos> enable_denoising true
```

#### Optimization Techniques

```python
# Level of detail optimization
miktos> enable_lod auto_threshold=0.1

# Culling optimization
miktos> enable_culling frustum=true occlusion=true

# Texture optimization
miktos> optimize_textures compression=true max_size=2K
```

### Workflow Optimization

#### Caching

```python
# Enable operation caching
miktos> config set cache.enabled true
miktos> config set cache.size "2GB"

# Cache management
miktos> cache clear
miktos> cache stats
miktos> cache optimize
```

#### Profiling

```python
# Enable profiling
miktos> profile start

# Run operations
miktos> create_complex_scene

# View profile results
miktos> profile report
miktos> profile export "performance_report.json"
```

---

## 🔧 Troubleshooting

### Common Issues

#### Connection Problems

**Issue**: "Cannot connect to Blender"

**Solution**:

- Check Blender installation path
- Verify Blender version compatibility
- Restart Blender addon

```python
# Diagnostic commands
miktos> diagnostic blender_connection
miktos> config verify blender_path
miktos> restart blender_addon
```

#### Performance Issues

**Issue**: "Slow command execution"

**Solution**:

- Enable parallel processing
- Increase memory allocation
- Optimize scene complexity

```python
# Performance diagnostics
miktos> diagnostic performance
miktos> profile last_operation
miktos> optimize system
```

#### Memory Problems

**Issue**: "Out of memory errors"

**Solution**:

- Enable auto-cleanup
- Reduce batch size
- Optimize texture sizes

```python
# Memory diagnostics
miktos> diagnostic memory
miktos> cleanup force
miktos> config set memory.aggressive_cleanup true
```

### Debug Mode

#### Enabling Debug Output

```python
# Enable debug logging
miktos> config set logging.level DEBUG
miktos> config set logging.verbose true

# Debug specific subsystems
miktos> debug enable blender_operations
miktos> debug enable ai_processing
miktos> debug enable skill_execution
```

#### Log Analysis

```python
# View recent logs
miktos> logs show recent
miktos> logs show errors

# Export logs
miktos> logs export "debug_session.log"

# Search logs
miktos> logs search "error" time_range="last_hour"
```

### Recovery Operations

#### Scene Recovery

```python
# Auto-save recovery
miktos> recover autosave

# Backup recovery
miktos> recover backup list
miktos> recover backup restore "backup_20231225_143022"
```

#### System Reset

```python
# Soft reset (keeps configuration)
miktos> reset soft

# Hard reset (factory defaults)
miktos> reset hard

# Reset specific subsystem
miktos> reset skills_library
miktos> reset viewer_state
```

---

## 📚 API Reference

### Core Classes

#### MiktosAgent

The main agent class for command processing.

```python
from miktos import MiktosAgent

# Initialize agent
agent = MiktosAgent()

# Process commands
result = agent.execute("create cube")
print(result.success)  # True
print(result.message)  # "Created cube 'Cube.001'"
```

#### SkillManager

Manages the skills library and execution.

```python
from miktos.core import SkillManager

# Initialize skill manager
skills = SkillManager()

# List available skills
available = skills.list_skills()

# Execute skill directly
result = skills.execute_skill("create_cube", size=2.0)
```

#### BlenderBridge

Interface to Blender operations.

```python
from miktos.integrations import BlenderBridge

# Initialize bridge
bridge = BlenderBridge()

# Direct Blender operations
bridge.create_object("cube", location=[0, 0, 0])
bridge.apply_material("metal", target="Cube")
```

### REST API

#### Authentication

```python
# API key authentication
headers = {
    "Authorization": "Bearer your_api_key",
    "Content-Type": "application/json"
}
```

#### Endpoints

##### Execute Command

```python
POST /api/v1/execute
{
    "command": "create metallic cube",
    "parameters": {
        "size": 2.0,
        "material": "chrome"
    }
}
```

##### Get Scene Status

```python
GET /api/v1/scene/status
Response:
{
    "objects": 5,
    "materials": 3,
    "lights": 2,
    "cameras": 1,
    "render_settings": {...}
}
```

##### Export Scene

```python
POST /api/v1/scene/export
{
    "format": "gltf",
    "options": {
        "include_materials": true,
        "include_animations": false
    }
}
```

### WebSocket API

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = function() {
    console.log('Connected to Miktos');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

#### Command Execution

```javascript
// Send command
ws.send(JSON.stringify({
    type: 'execute',
    command: 'create sphere',
    id: 'cmd_001'
}));

// Response
{
    type: 'result',
    id: 'cmd_001',
    success: true,
    data: {
        object_id: 'Sphere.001',
        location: [0, 0, 0]
    }
}
```

#### Real-time Updates

```javascript
// Subscribe to scene updates
ws.send(JSON.stringify({
    type: 'subscribe',
    events: ['object_created', 'object_modified', 'render_complete']
}));

// Receive updates
{
    type: 'event',
    event: 'object_created',
    data: {
        object_id: 'Cube.002',
        timestamp: '2023-12-25T14:30:22Z'
    }
}
```

---

## 🚀 Deployment Guide

### Development Deployment

#### Local Development Setup

```bash
# Clone and setup
git clone https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# Development environment
python -m venv venv
source venv/bin/activate
pip install -e .[dev]

# Start development server
python main.py --dev
```

#### Development Configuration

```yaml
# config/development.yaml
mode: development
debug: true
auto_reload: true

blender:
  path: "/Applications/Blender.app/Contents/MacOS/Blender"
  addon_auto_install: true

viewer:
  port: 8080
  debug_toolbar: true

logging:
  level: DEBUG
  console_output: true
```

### Production Deployment

#### Server Requirements

**Minimum Production Server:**

- 4 CPU cores
- 16GB RAM
- 50GB SSD storage
- GPU with 4GB VRAM (recommended)

**Recommended Production Server:**

- 8+ CPU cores
- 32GB RAM
- 100GB SSD storage
- GPU with 8GB+ VRAM

#### Docker Deployment

```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    blender \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt
RUN npm install

# Configure production
COPY config/production.yaml config/config.yaml

# Expose ports
EXPOSE 8080 8081

# Start services
CMD ["python", "main.py", "--production"]
```

```bash
# Build and run
docker build -t miktos-platform -f Dockerfile.production .
docker run -d -p 8080:8080 -p 8081:8081 miktos-platform
```

#### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: miktos-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: miktos-platform
  template:
    metadata:
      labels:
        app: miktos-platform
    spec:
      containers:
      - name: miktos
        image: miktos-platform:latest
        ports:
        - containerPort: 8080
        - containerPort: 8081
        env:
        - name: MIKTOS_MODE
          value: "production"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
---
apiVersion: v1
kind: Service
metadata:
  name: miktos-service
spec:
  selector:
    app: miktos-platform
  ports:
  - name: web
    port: 80
    targetPort: 8080
  - name: api
    port: 8081
    targetPort: 8081
  type: LoadBalancer
```

### Cloud Deployment

#### AWS Deployment

```bash
# Using AWS ECS
aws ecs create-cluster --cluster-name miktos-cluster

# Task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Service creation
aws ecs create-service \
    --cluster miktos-cluster \
    --service-name miktos-service \
    --task-definition miktos-platform:1 \
    --desired-count 2
```

#### Google Cloud Deployment

```bash
# Using Google Cloud Run
gcloud builds submit --tag gcr.io/PROJECT-ID/miktos-platform

gcloud run deploy miktos-platform \
    --image gcr.io/PROJECT-ID/miktos-platform \
    --platform managed \
    --region us-central1 \
    --memory 4Gi \
    --cpu 2
```

#### Azure Deployment

```bash
# Using Azure Container Instances
az group create --name miktos-rg --location eastus

az container create \
    --resource-group miktos-rg \
    --name miktos-platform \
    --image miktos-platform:latest \
    --cpu 2 \
    --memory 4 \
    --ports 8080 8081
```

### Monitoring and Maintenance

#### Health Checks

```python
# Health check endpoint
GET /health
Response:
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 3600,
    "blender_status": "connected",
    "skills_loaded": 52,
    "memory_usage": "2.1GB",
    "cpu_usage": "15%"
}
```

#### Monitoring Setup

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'miktos-platform'
    static_configs:
      - targets: ['miktos-platform:8081']
    metrics_path: '/metrics'
```

#### Log Management

```bash
# Centralized logging with ELK stack
docker run -d --name elasticsearch \
    -p 9200:9200 \
    elasticsearch:7.10.0

docker run -d --name kibana \
    -p 5601:5601 \
    --link elasticsearch:elasticsearch \
    kibana:7.10.0

# Configure Miktos to send logs to Elasticsearch
export MIKTOS_LOG_OUTPUT=elasticsearch
export MIKTOS_ES_HOST=localhost:9200
```

### Performance Tuning

#### Production Optimizations

```yaml
# config/production.yaml
performance:
  parallel_processing: true
  max_workers: 8
  memory_limit: "8GB"
  cache_size: "2GB"
  
render:
  gpu_acceleration: true
  device: "CUDA"
  memory_limit: "6GB"
  
database:
  connection_pool: 20
  query_timeout: 30

logging:
  level: INFO
  rotation: daily
  max_files: 30
```

#### Load Balancing

```nginx
# nginx.conf
upstream miktos_backend {
    server miktos-1:8080;
    server miktos-2:8080;
    server miktos-3:8080;
}

server {
    listen 80;
    server_name miktos.yourdomain.com;
    
    location / {
        proxy_pass http://miktos_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /ws {
        proxy_pass http://miktos_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📞 Support & Community

### Getting Help

#### Documentation Resources

- **Complete API Documentation**: [api.miktos.com](https://api.miktos.com)
- **Video Tutorials**: [tutorials.miktos.com](https://tutorials.miktos.com)
- **Community Wiki**: [wiki.miktos.com](https://wiki.miktos.com)

#### Support Channels

- **GitHub Issues**: Report bugs and feature requests
- **Discord Community**: Real-time chat and support
- **Stack Overflow**: Tag questions with `miktos-platform`
- **Email Support**: [support@miktos.com](mailto:support@miktos.com)

#### Training Resources

- **Beginner Course**: "Getting Started with Miktos"
- **Advanced Workshop**: "Custom Skill Development"
- **Enterprise Training**: Custom on-site training available

### Contributing

#### Development Process

1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

#### Contribution Guidelines

- Follow Python PEP 8 style guide
- Add documentation for new features
- Include unit tests
- Update changelog

#### Community Resources

- **Developer Docs**: [dev.miktos.com](https://dev.miktos.com)
- **Contribution Guide**: [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)

---

## 📄 License & Legal

### Software License

Miktos AI Bridge Platform is licensed under the MIT License. See [LICENSE](./LICENSE) for full terms.

### Third-Party Licenses

- **Blender**: GPL v3
- **Node.js**: MIT License
- **Python**: PSF License

### Privacy Policy

Data handling and privacy information available at [privacy.miktos.com](https://privacy.miktos.com).

---

**© 2023 Miktos Universe. All rights reserved.**

*This documentation is continuously updated. For the latest version, visit [docs.miktos.com](https://docs.miktos.com).*
