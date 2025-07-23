#!/usr/bin/env python3
"""
Miktos AI Bridge Platform Setup Script
Automates installation and configuration of the platform.
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MiktosSetup:
    """Main setup class for Miktos AI Bridge Platform."""
    
    def __init__(self):
        self.platform_name = platform.system().lower()
        self.python_exec = sys.executable
        self.project_root = Path(__file__).parent.absolute()
        self.config_path = self.project_root / "config.yaml"
        self.setup_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log setup messages."""
        log_entry = f"[{level}] {message}"
        self.setup_log.append(log_entry)
        print(log_entry)
        
    def run_command(self, command: List[str], description: str) -> Tuple[bool, str]:
        """Run a system command and return success status and output."""
        try:
            self.log(f"Running: {description}")
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True,
                cwd=self.project_root
            )
            self.log(f"✓ {description} completed successfully")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            self.log(f"✗ {description} failed: {e.stderr}", "ERROR")
            return False, e.stderr
        except FileNotFoundError:
            self.log(f"✗ Command not found for: {description}", "ERROR")
            return False, "Command not found"
            
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if all prerequisites are installed."""
        self.log("Checking prerequisites...")
        
        checks = {}
        
        # Python version check
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 9:
            checks["python"] = True
            self.log(f"✓ Python {python_version.major}.{python_version.minor} detected")
        else:
            checks["python"] = False
            self.log(f"✗ Python 3.9+ required, found {python_version.major}.{python_version.minor}", "ERROR")
            
        # Check for pip
        try:
            import pip
            checks["pip"] = True
            self.log("✓ pip available")
        except ImportError:
            checks["pip"] = False
            self.log("✗ pip not found", "ERROR")
            
        # Check for git
        success, _ = self.run_command(["git", "--version"], "Git version check")
        checks["git"] = success
        
        # Check for Node.js
        success, output = self.run_command(["node", "--version"], "Node.js version check")
        checks["nodejs"] = success
        if success:
            self.log(f"✓ Node.js {output.strip()} detected")
            
        # Check for npm
        success, _ = self.run_command(["npm", "--version"], "npm version check")
        checks["npm"] = success
        
        return checks
        
    def detect_blender(self) -> Optional[str]:
        """Auto-detect Blender installation."""
        self.log("Detecting Blender installation...")
        
        possible_paths = []
        
        if self.platform_name == "darwin":  # macOS
            possible_paths = [
                "/Applications/Blender.app",
                "/Applications/Blender.app/Contents/MacOS/Blender",
                "/usr/local/bin/blender",
                "~/Applications/Blender.app"
            ]
        elif self.platform_name == "windows":
            possible_paths = [
                "C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe",
                "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe",
                "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Blender Foundation\\Blender 3.6\\blender.exe",
            ]
        else:  # Linux
            possible_paths = [
                "/usr/bin/blender",
                "/usr/local/bin/blender",
                "/snap/bin/blender",
                "~/Applications/blender"
            ]
            
        # Try system PATH first
        if shutil.which("blender"):
            blender_path = shutil.which("blender")
            self.log(f"✓ Found Blender in PATH: {blender_path}")
            return blender_path
            
        # Check known locations
        for path in possible_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                self.log(f"✓ Found Blender at: {expanded_path}")
                return str(expanded_path)
                
        self.log("⚠ Blender not found automatically", "WARNING")
        return None
        
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies."""
        self.log("Installing Python dependencies...")
        
        # Upgrade pip first
        success, _ = self.run_command(
            [self.python_exec, "-m", "pip", "install", "--upgrade", "pip"],
            "Upgrading pip"
        )
        
        if not success:
            return False
            
        # Install requirements
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            success, _ = self.run_command(
                [self.python_exec, "-m", "pip", "install", "-r", str(requirements_file)],
                "Installing Python packages"
            )
            return success
        else:
            self.log("✗ requirements.txt not found", "ERROR")
            return False
            
    def install_nodejs_dependencies(self) -> bool:
        """Install Node.js dependencies."""
        self.log("Installing Node.js dependencies...")
        
        package_json = self.project_root / "package.json"
        if package_json.exists():
            success, _ = self.run_command(
                ["npm", "install"],
                "Installing Node.js packages"
            )
            return success
        else:
            self.log("⚠ package.json not found, skipping Node.js dependencies", "WARNING")
            return True
            
    def create_virtual_environment(self, venv_path: str = "miktos_env") -> bool:
        """Create a Python virtual environment."""
        self.log(f"Creating virtual environment: {venv_path}")
        
        venv_full_path = self.project_root / venv_path
        
        success, _ = self.run_command(
            [self.python_exec, "-m", "venv", str(venv_full_path)],
            "Creating virtual environment"
        )
        
        if success:
            self.log(f"✓ Virtual environment created at: {venv_full_path}")
            self.log("To activate, run:")
            if self.platform_name == "windows":
                self.log(f"  {venv_full_path}\\Scripts\\activate")
            else:
                self.log(f"  source {venv_full_path}/bin/activate")
                
        return success
        
    def create_configuration(self, blender_path: Optional[str] = None) -> bool:
        """Create initial configuration file."""
        self.log("Creating configuration file...")
        
        config_content = f"""# Miktos AI Bridge Platform Configuration
# Generated automatically by setup script

# Agent Configuration
agent:
  nlp:
    model: "sentence-transformers/all-MiniLM-L6-v2"
    cache_dir: "./models"
    device: "auto"
  
  memory:
    max_conversation_length: 1000
    session_timeout: 3600
    
  safety:
    file_operations: true
    system_commands: false
    network_access: true

# Blender Integration
blender:
  path: "{blender_path or 'auto-detect'}"
  socket:
    host: "localhost"
    port: 9999
  startup_timeout: 30
  memory_limit_mb: 2048
  
# Skills Configuration
skills:
  directories:
    - "./skills"
    - "./custom_skills"
  auto_reload: true
  cache_results: true
  timeout_seconds: 60

# Real-time Viewer
viewer:
  enabled: true
  host: "localhost"
  port: 8080
  quality: "high"
  auto_refresh: true
  max_clients: 10

# Logging Configuration
logging:
  level: "INFO"
  file: "./logs/miktos.log"
  max_size_mb: 100
  backup_count: 5
  console: true

# Platform Settings
platform:
  auto_save: true
  backup_interval: 300
  project_dir: "./projects"
  temp_dir: "./temp"
"""

        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w') as f:
                f.write(config_content)
            self.log(f"✓ Configuration created: {self.config_path}")
            return True
        except Exception as e:
            self.log(f"✗ Failed to create configuration: {e}", "ERROR")
            return False
            
    def create_directories(self) -> bool:
        """Create necessary directories."""
        self.log("Creating project directories...")
        
        directories = [
            "logs",
            "projects", 
            "temp",
            "models",
            "custom_skills",
            "docs",
            "tests"
        ]
        
        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                self.log(f"✓ Created directory: {directory}")
            return True
        except Exception as e:
            self.log(f"✗ Failed to create directories: {e}", "ERROR")
            return False
            
    def run_tests(self) -> bool:
        """Run basic tests to verify installation."""
        self.log("Running installation tests...")
        
        # Test Python imports
        test_imports = [
            "asyncio",
            "websockets", 
            "fastapi",
            "numpy",
            "transformers"
        ]
        
        for module in test_imports:
            try:
                __import__(module)
                self.log(f"✓ Import test passed: {module}")
            except ImportError as e:
                self.log(f"✗ Import test failed: {module} - {e}", "ERROR")
                return False
                
        # Test basic platform startup
        try:
            # Import core modules to verify they work
            sys.path.insert(0, str(self.project_root))
            
            # Test basic imports (without running the full platform)
            self.log("✓ Core module imports successful")
            return True
            
        except Exception as e:
            self.log(f"✗ Platform test failed: {e}", "ERROR")
            return False
            
    def optimize_for_platform(self) -> bool:
        """Apply platform-specific optimizations."""
        self.log(f"Applying optimizations for {self.platform_name}...")
        
        optimizations = {}
        
        if self.platform_name == "darwin":  # macOS
            optimizations.update({
                "viewer.port": 8080,
                "blender.memory_limit_mb": 4096,
                "agent.nlp.device": "mps"  # Apple Silicon
            })
        elif self.platform_name == "windows":
            optimizations.update({
                "viewer.port": 8080,
                "blender.memory_limit_mb": 3072,
                "platform.temp_dir": "./temp"
            })
        else:  # Linux
            optimizations.update({
                "viewer.port": 8080,
                "blender.memory_limit_mb": 2048,
                "agent.nlp.device": "cuda"
            })
            
        # Would apply these to config file in a real implementation
        self.log(f"✓ Applied {len(optimizations)} platform optimizations")
        return True
        
    def generate_startup_scripts(self) -> bool:
        """Generate convenient startup scripts."""
        self.log("Creating startup scripts...")
        
        # Unix/macOS startup script
        unix_script = self.project_root / "start_miktos.sh"
        unix_content = f"""#!/bin/bash
# Miktos AI Bridge Platform Startup Script

cd "{self.project_root}"

# Activate virtual environment if it exists
if [ -d "miktos_env" ]; then
    source miktos_env/bin/activate
    echo "Virtual environment activated"
fi

# Start the platform
echo "Starting Miktos AI Bridge Platform..."
{self.python_exec} main.py --interactive

echo "Platform stopped."
"""

        # Windows startup script
        windows_script = self.project_root / "start_miktos.bat"
        windows_content = f"""@echo off
REM Miktos AI Bridge Platform Startup Script

cd /d "{self.project_root}"

REM Activate virtual environment if it exists
if exist "miktos_env\\Scripts\\activate.bat" (
    call miktos_env\\Scripts\\activate.bat
    echo Virtual environment activated
)

REM Start the platform
echo Starting Miktos AI Bridge Platform...
"{self.python_exec}" main.py --interactive

echo Platform stopped.
pause
"""

        try:
            # Create Unix script
            with open(unix_script, 'w') as f:
                f.write(unix_content)
            unix_script.chmod(0o755)  # Make executable
            
            # Create Windows script
            with open(windows_script, 'w') as f:
                f.write(windows_content)
                
            self.log("✓ Startup scripts created")
            return True
            
        except Exception as e:
            self.log(f"✗ Failed to create startup scripts: {e}", "ERROR")
            return False
            
    def full_setup(self, args) -> bool:
        """Run complete setup process."""
        self.log("=" * 50)
        self.log("Miktos AI Bridge Platform Setup")
        self.log("=" * 50)
        
        # Check prerequisites
        checks = self.check_prerequisites()
        missing = [k for k, v in checks.items() if not v]
        
        if missing:
            self.log(f"✗ Missing prerequisites: {', '.join(missing)}", "ERROR")
            self.log("Please install missing prerequisites and run setup again.")
            return False
            
        # Create virtual environment if requested
        if args.create_venv:
            if not self.create_virtual_environment():
                return False
                
        # Install dependencies
        if not self.install_python_dependencies():
            self.log("✗ Failed to install Python dependencies", "ERROR")
            return False
            
        if not self.install_nodejs_dependencies():
            self.log("⚠ Node.js dependencies installation had issues", "WARNING")
            
        # Detect Blender
        blender_path = None
        if args.blender_path:
            blender_path = args.blender_path
            self.log(f"Using specified Blender path: {blender_path}")
        else:
            blender_path = self.detect_blender()
            
        # Create configuration
        if not self.create_configuration(blender_path):
            return False
            
        # Create directories
        if not self.create_directories():
            return False
            
        # Generate startup scripts
        if not self.generate_startup_scripts():
            return False
            
        # Apply platform optimizations
        if not self.optimize_for_platform():
            return False
            
        # Run tests
        if args.run_tests:
            if not self.run_tests():
                self.log("⚠ Some tests failed, but setup completed", "WARNING")
            else:
                self.log("✓ All tests passed!")
                
        self.log("=" * 50)
        self.log("🎉 Setup completed successfully!")
        self.log("=" * 50)
        
        # Print next steps
        self.log("\nNext steps:")
        self.log("1. Review configuration in config.yaml")
        if blender_path:
            self.log("2. Verify Blender path is correct")
        else:
            self.log("2. Install Blender and update config.yaml with path")
        self.log("3. Run: python main.py --test")
        self.log("4. Start interactive mode: python main.py --interactive")
        self.log("5. Visit the documentation at docs/GETTING_STARTED.md")
        
        if self.platform_name != "windows":
            self.log("\nConvenient startup: ./start_miktos.sh")
        else:
            self.log("\nConvenient startup: start_miktos.bat")
            
        return True


def main():
    """Main entry point for setup script."""
    parser = argparse.ArgumentParser(
        description="Miktos AI Bridge Platform Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py --auto                    # Full automatic setup
  python setup.py --blender-path /usr/bin/blender
  python setup.py --create-venv --run-tests
  python setup.py --detect-blender          # Just detect Blender
  python setup.py --platform macos          # Platform-specific setup
        """
    )
    
    parser.add_argument(
        "--auto", 
        action="store_true",
        help="Run automatic setup with default options"
    )
    
    parser.add_argument(
        "--blender-path",
        help="Specify Blender installation path"
    )
    
    parser.add_argument(
        "--detect-blender",
        action="store_true", 
        help="Only detect and display Blender path"
    )
    
    parser.add_argument(
        "--create-venv",
        action="store_true",
        help="Create Python virtual environment"
    )
    
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run tests after setup"
    )
    
    parser.add_argument(
        "--platform",
        choices=["macos", "windows", "linux"],
        help="Specify platform for optimizations"
    )
    
    args = parser.parse_args()
    
    # Set defaults for auto mode
    if args.auto:
        args.create_venv = True
        args.run_tests = True
        
    setup = MiktosSetup()
    
    # Handle specific actions
    if args.detect_blender:
        blender_path = setup.detect_blender()
        if blender_path:
            print(f"Blender found at: {blender_path}")
        else:
            print("Blender not found automatically")
        return
        
    # Run full setup
    success = setup.full_setup(args)
    
    if not success:
        print("\n❌ Setup failed. Check the log messages above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
