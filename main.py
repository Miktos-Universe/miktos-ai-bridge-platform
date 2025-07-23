"""
Main entry point for Miktos AI Bridge Platform

Coordinates all components and provides unified interface for
intelligent Blender automation through natural language.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
try:
    import yaml  # type: ignore
except ImportError:
    print("PyYAML not installed. Install with: pip install PyYAML")
    sys.exit(1)

from core.agent import MiktosAgent
from viewer.real_time_viewer import RealTimeViewer  # type: ignore


class MiktosPlatform:
    """
    Main Miktos Platform coordinator
    Integrates all components for seamless 3D workflow automation
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger('MiktosPlatform')
        
        # Core components
        self.agent: Optional[MiktosAgent] = None
        self.viewer: Optional[RealTimeViewer] = None
        
        # Platform state
        self.is_running = False
        self.current_session = None
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            # Create default config
            default_config = self._get_default_config()
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            return default_config
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'platform': {
                'name': 'Miktos AI Bridge',
                'version': '1.0.0',
                'debug': False
            },
            'agent': {
                'nlp': {
                    'model': 'sentence-transformers/all-MiniLM-L6-v2',
                    'context_window': 5
                },
                'parser': {
                    'max_complexity': 0.8,
                    'safety_checks': True
                },
                'safety': {
                    'validation_level': 'normal',
                    'rollback_enabled': True,
                    'max_operations_per_command': 10
                },
                'learning': {
                    'track_performance': True,
                    'optimize_skills': True,
                    'community_data': False
                }
            },
            'blender': {
                'path': '/Applications/Blender.app',
                'python_path': None,
                'socket_port': 8089,
                'startup_timeout': 30.0,
                'auto_save': True
            },
            'skills': {
                'max_skills_per_command': 3,
                'skill_timeout': 30.0,
                'cache_skills': True
            },
            'viewer': {
                'enabled': True,
                'port': 8080,
                'resolution': [1920, 1080],
                'fps_target': 60,
                'quality': 'high',
                'auto_start': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'miktos.log',
                'max_size_mb': 10,
                'backup_count': 5
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        
        # Configure logging
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'miktos.log')
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get('max_size_mb', 10) * 1024 * 1024,
            backupCount=log_config.get('backup_count', 5)
        )
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start(self) -> bool:
        """Start the Miktos platform"""
        try:
            self.logger.info("Starting Miktos AI Bridge Platform...")
            
            # Initialize agent
            self.agent = MiktosAgent(self.config)
            
            # Initialize viewer if enabled
            if self.config.get('viewer', {}).get('enabled', True):
                self.viewer = RealTimeViewer(self.config.get('viewer', {}))
                if self.viewer and self.config.get('viewer', {}).get('auto_start', True):
                    await self.viewer.start()
            
            self.is_running = True
            self.logger.info("Miktos platform started successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start platform: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the platform gracefully"""
        if not self.is_running:
            return
        
        self.logger.info("Shutting down Miktos platform...")
        self.is_running = False
        
        # Stop current session if active
        if self.current_session and self.agent:
            await self.agent.stop_session()
        
        # Stop viewer
        if self.viewer:
            await self.viewer.stop()
        
        self.logger.info("Miktos platform shutdown complete")
    
    async def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new automation session"""
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        self.current_session = await self.agent.start_session(session_id)
        self.logger.info(f"Started session: {self.current_session}")
        
        return self.current_session
    
    async def stop_session(self):
        """Stop the current session"""
        if self.agent and self.current_session:
            await self.agent.stop_session()
            self.logger.info(f"Stopped session: {self.current_session}")
            self.current_session = None
    
    async def execute_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a natural language command"""
        if not self.agent:
            return {
                "success": False,
                "message": "Agent not initialized",
                "error": "AGENT_NOT_INITIALIZED"
            }
        
        if not self.current_session:
            # Auto-start session if not active
            await self.start_session()
        
        try:
            result = await self.agent.execute_command(command, context or {})
            
            # Update viewer if available and execution was successful
            if self.viewer and result.success:
                # Get updated scene state
                scene_info = await self.agent.blender_bridge.get_scene_info()
                if scene_info:
                    await self.viewer.update_scene(scene_info)
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "execution_time": result.execution_time,
                "skills_used": result.skills_used,
                "errors": result.errors
            }
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "message": f"Execution failed: {str(e)}",
                "error": "EXECUTION_ERROR"
            }
    
    async def get_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions"""
        if self.agent:
            return await self.agent.get_suggestions(partial_command)
        return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get platform status"""
        status = {
            "platform": {
                "running": self.is_running,
                "session_active": self.current_session is not None,
                "current_session": self.current_session
            },
            "agent": None,
            "viewer": None
        }
        
        if self.agent:
            status["agent"] = await self.agent.get_status()
        
        if self.viewer:
            status["viewer"] = await self.viewer.get_viewer_state()
        
        return status
    
    async def export_session_data(self) -> Dict[str, Any]:
        """Export current session data"""
        if self.agent:
            return await self.agent.export_session_data()
        return {}
    
    async def take_screenshot(self) -> str:
        """Take a screenshot of the current 3D view"""
        if self.viewer:
            screenshot = await self.viewer.take_screenshot()
            return screenshot or ""
        return ""
    
    async def set_viewer_camera(self, position: List[float], target: List[float]):
        """Set viewer camera position"""
        if self.viewer:
            await self.viewer.set_camera(position, target)
    
    async def interactive_mode(self):
        """Start interactive command-line mode"""
        print("Miktos AI Bridge Platform - Interactive Mode")
        print("Type 'help' for commands, 'quit' to exit")
        print("-" * 50)
        
        # Start session
        session_id = await self.start_session()
        print(f"Session started: {session_id}")
        
        while self.is_running:
            try:
                # Get user input
                user_input = input("miktos> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    self._print_help()
                elif user_input.lower() == 'status':
                    status = await self.get_status()
                    print(f"Platform Status: {status}")
                elif user_input.lower() == 'screenshot':
                    screenshot = await self.take_screenshot()
                    if screenshot:
                        print("Screenshot taken successfully")
                    else:
                        print("Failed to take screenshot")
                else:
                    # Execute command
                    result = await self.execute_command(user_input)
                    
                    if result["success"]:
                        print(f"✓ {result['message']}")
                        if result.get("execution_time"):
                            print(f"  Execution time: {result['execution_time']:.2f}s")
                        if result.get("skills_used"):
                            print(f"  Skills used: {', '.join(result['skills_used'])}")
                    else:
                        print(f"✗ {result['message']}")
                        if result.get("errors"):
                            for error in result["errors"]:
                                print(f"  Error: {error}")
                
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                print(f"Error: {e}")
        
        # Stop session
        await self.stop_session()
        print("Session ended. Goodbye!")
    
    def _print_help(self):
        """Print help information"""
        help_text = """
Available Commands:
  help        - Show this help message
  status      - Show platform status
  screenshot  - Take a screenshot of the 3D view
  quit        - Exit the platform

Natural Language Commands (examples):
  "Create a cube and subdivide it 3 times"
  "Add a metallic material to the selected object"
  "Set up three-point lighting"
  "Delete the selected object"
  "Scale the object by 2"
  "Rotate the object 45 degrees around Z axis"
  
Camera Controls:
  "Set camera to look at the origin from above"
  "Move camera to [5, 5, 5] looking at [0, 0, 0]"
  
Complex Workflows:
  "Create a simple house with windows and door"
  "Model a car wheel with tire"
  "Set up a product photography scene"
        """
        print(help_text)


# CLI entry point
async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Miktos AI Bridge Platform")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start in interactive mode")
    parser.add_argument("--command", "-c", help="Execute a single command and exit")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Create platform
    platform = MiktosPlatform(args.config)
    
    # Start platform
    success = await platform.start()
    if not success:
        print("Failed to start Miktos platform")
        sys.exit(1)
    
    try:
        if args.command:
            # Execute single command
            result = await platform.execute_command(args.command)
            print(f"Result: {result['message']}")
            print(f"Success: {result['success']}")
            
        elif args.interactive:
            # Interactive mode
            await platform.interactive_mode()
            
        elif args.daemon:
            # Daemon mode - run until interrupted
            print("Miktos platform running in daemon mode...")
            print("Press Ctrl+C to stop")
            
            while platform.is_running:
                await asyncio.sleep(1)
        else:
            # Default: show status and exit
            status = await platform.get_status()
            print("Miktos AI Bridge Platform")
            print(f"Status: {status}")
            print("Use --interactive or --command to interact with the platform")
    
    finally:
        await platform.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
