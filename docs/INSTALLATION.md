# 🚀 Installation Guide - Miktos AI Bridge Platform

## Quick Start (5 minutes)

### Prerequisites

- **Python 3.9+** with pip
- **Blender 3.0+** installed
- **Node.js 18+** (for viewer components)
- **Git** for version control
- **8GB+ RAM** recommended

### One-Line Installation

```bash
# Clone and setup
git clone https://github.com/Miktos-Universe/miktos-workflows.git && cd miktos-workflows && python setup.py --auto
```

### Manual Installation

#### 1. Clone Repository

```bash
git clone https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows
```

#### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv miktos_env
source miktos_env/bin/activate  # On Windows: miktos_env\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for viewer
npm install
```

#### 3. Configure Blender Integration

```bash
# Auto-detect Blender installation
python core/setup.py --detect-blender

# Or specify manually
python core/setup.py --blender-path "/Applications/Blender.app"
```

#### 4. Initialize Platform

```bash
# Run initialization
python main.py --init

# Test installation
python main.py --test
```

## Platform-Specific Installation

### macOS

#### Using Homebrew (Recommended)

```bash
# Install prerequisites
brew install python node blender

# Clone and setup
git clone https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# Install dependencies
pip install -r requirements.txt
npm install

# Auto-configure
python setup.py --platform macos
```

#### Manual macOS Setup

```bash
# Download Blender from blender.org
# Install Python 3.9+ from python.org
# Install Node.js from nodejs.org

# Configure Blender path
python core/setup.py --blender-path "/Applications/Blender.app"
```

### Windows

#### Using Chocolatey (Recommended)

```powershell
# Install prerequisites
choco install python nodejs blender

# Clone and setup
git clone https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# Install dependencies
pip install -r requirements.txt
npm install

# Auto-configure
python setup.py --platform windows
```

#### Manual Windows Setup

```powershell
# Download and install:
# - Python 3.9+ from python.org
# - Node.js from nodejs.org  
# - Blender from blender.org
# - Git from git-scm.com

# Configure Blender path
python core/setup.py --blender-path "C:\Program Files\Blender Foundation\Blender 3.6"
```

### Linux (Ubuntu/Debian)

#### Using Package Manager

```bash
# Install prerequisites
sudo apt update
sudo apt install python3 python3-pip nodejs npm blender git

# Clone and setup
git clone https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# Install dependencies
pip3 install -r requirements.txt
npm install

# Auto-configure
python3 setup.py --platform linux
```

#### Arch Linux

```bash
# Install prerequisites
sudo pacman -S python python-pip nodejs npm blender git

# Follow standard installation steps
```

## Advanced Installation Options

### Docker Installation (Recommended for Production)

```bash
# Build Docker image
docker build -t miktos-platform .

# Run with Docker Compose
docker-compose up -d

# Access platform
docker exec -it miktos-platform python main.py --interactive
```

### Development Installation

```bash
# Clone with development dependencies
git clone --recurse-submodules https://github.com/Miktos-Universe/miktos-workflows.git
cd miktos-workflows

# Install development dependencies
pip install -r requirements-dev.txt
npm install --include=dev

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest tests/
npm test
```

### Custom Skills Installation

```bash
# Create custom skills directory
mkdir -p custom_skills/

# Install community skills
python scripts/install_skills.py --community

# Install specific skill package
python scripts/install_skills.py --package "advanced-modeling"
```

## Configuration

### Initial Configuration

```bash
# Generate default configuration
python main.py --generate-config

# Edit configuration
nano config.yaml  # or use your preferred editor
```

### Essential Configuration Options

```yaml
# Blender Integration
blender:
  path: "/Applications/Blender.app"  # Adjust for your installation
  
# Viewer Settings
viewer:
  port: 8080
  quality: "high"
  
# AI Settings
agent:
  nlp:
    model: "sentence-transformers/all-MiniLM-L6-v2"
```

### Environment Variables

```bash
# Create .env file
cat > .env << EOF
MIKTOS_BLENDER_PATH="/Applications/Blender.app"
MIKTOS_LOG_LEVEL="INFO"
MIKTOS_VIEWER_PORT="8080"
MIKTOS_ENABLE_GPU="true"
EOF
```

## Verification & Testing

### Quick Test

```bash
# Start platform
python main.py --test

# Expected output:
# ✓ Blender connection: OK
# ✓ Skills library: 50+ skills loaded
# ✓ Viewer: Running on http://localhost:8080
# ✓ Agent: Ready for commands
```

### Interactive Test

```bash
# Start interactive mode
python main.py --interactive

# Try test commands:
miktos> create cube
miktos> add material metallic
miktos> status
miktos> quit
```

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_agent.py -v
pytest tests/test_blender_bridge.py -v
pytest tests/test_skills.py -v
```

## Troubleshooting

### Common Issues

#### 1. Blender Not Found

```bash
# Error: "Blender executable not found"
# Solution: Specify Blender path manually
python core/setup.py --blender-path "/path/to/blender"

# Verify Blender installation
which blender  # Linux/macOS
where blender  # Windows
```

#### 2. Port Already in Use

```bash
# Error: "Port 8080 already in use"
# Solution: Change port in config.yaml
viewer:
  port: 8081  # Use different port
```

#### 3. GPU/OpenGL Issues

```bash
# Error: "OpenGL context creation failed"
# Solution: Update graphics drivers and try software rendering
export MIKTOS_FORCE_SOFTWARE_RENDERING=1
python main.py
```

#### 4. Memory Issues

```bash
# Error: "Out of memory"
# Solution: Reduce viewer quality and Blender memory limit
viewer:
  quality: "medium"
blender:
  memory_limit_mb: 1024
```

#### 5. Permission Issues (Linux/macOS)

```bash
# Error: "Permission denied"
# Solution: Fix permissions
chmod +x scripts/*.py
sudo chown -R $USER:$USER ~/.miktos/
```

### Logs and Debugging

```bash
# Enable debug logging
export MIKTOS_LOG_LEVEL=DEBUG

# View logs
tail -f logs/miktos.log

# Component-specific debugging
python main.py --debug-component agent
python main.py --debug-component blender_bridge
```

### Performance Optimization

```bash
# Optimize for your system
python scripts/optimize.py --auto

# Manual optimization
python scripts/optimize.py --cpu-cores 8 --memory-gb 16 --gpu-enabled
```

## Next Steps

1. **Complete the [Getting Started Guide](GETTING_STARTED.md)**
2. **Explore [Skills Development](SKILLS_DEVELOPMENT.md)**
3. **Read [API Documentation](API.md)**
4. **Join the [Community](https://community.miktos.ai)**

## Support

- **GitHub Issues**: [Report bugs](https://github.com/Miktos-Universe/miktos-workflows/issues)
- **Discussions**: [Community Q&A](https://github.com/Miktos-Universe/miktos-workflows/discussions)
- **Discord**: [Real-time chat](https://discord.gg/miktos)
- **Email**: <support@miktos.ai>

---

**Installation complete!** 🎉

Your Miktos AI Bridge Platform is ready to transform your 3D workflow automation.
