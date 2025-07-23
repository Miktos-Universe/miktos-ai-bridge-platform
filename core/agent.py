"""
Miktos Core Agent Engine

The main AI agent coordinator that orchestrates natural language processing,
command interpretation, and Blender integration.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .nlp_processor import NLPProcessor  # type: ignore
from .command_parser import CommandParser  # type: ignore
from .safety_manager import SafetyManager  # type: ignore
from .learning_engine import LearningEngine  # type: ignore
from agent.blender_bridge import BlenderBridge  # type: ignore
from skills.skill_manager import SkillManager  # type: ignore


@dataclass
class AgentCommand:
    """Represents a user command with metadata"""
    text: str
    timestamp: datetime
    session_id: str
    context: Dict[str, Any]
    priority: str = "normal"  # low, normal, high


@dataclass
class ExecutionResult:
    """Represents the result of command execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    skills_used: Optional[List[str]] = None
    errors: Optional[List[str]] = None


class MiktosAgent:
    """
    Main AI agent that coordinates all subsystems to execute
    natural language commands in Blender.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Miktos agent with configuration"""
        self.config = config
        self.session_id = None
        self.is_running = False
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize core components
        self.nlp_processor = NLPProcessor(config.get('nlp', {}))
        self.command_parser = CommandParser(config.get('parser', {}))
        self.safety_manager = SafetyManager(config.get('safety', {}))
        self.learning_engine = LearningEngine(config.get('learning', {}))
        
        # Initialize integration components
        self.blender_bridge = BlenderBridge(config.get('blender', {}))
        self.skill_manager = SkillManager(config.get('skills', {}))
        
        # Command queue and history
        self.command_queue = asyncio.Queue()
        self.command_history = []
        self.execution_results = []
        
        self.logger.info("Miktos Agent initialized successfully")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('miktos_agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MiktosAgent')
    
    async def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new agent session"""
        if session_id is None:
            session_id = f"session_{datetime.now().isoformat()}"
        
        self.session_id = session_id
        self.is_running = True
        
        # Initialize Blender connection
        try:
            await self.blender_bridge.connect()
            self.logger.info(f"Session {session_id} started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start session: {e}")
            raise
        
        return session_id
    
    async def stop_session(self):
        """Stop the current session"""
        self.is_running = False
        await self.blender_bridge.disconnect()
        self.logger.info(f"Session {self.session_id} stopped")
    
    async def execute_command(self, command_text: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a natural language command
        
        Args:
            command_text: Natural language command from user
            context: Additional context information
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()
        
        # Create command object
        command = AgentCommand(
            text=command_text,
            timestamp=start_time,
            session_id=self.session_id or "unknown",
            context=context or {}
        )
        
        try:
            # Step 1: Natural Language Processing
            self.logger.info(f"Processing command: {command_text}")
            nlp_result = await self.nlp_processor.process(command_text, context)
            
            # Step 2: Command Parsing and Intent Recognition
            parsed_command = await self.command_parser.parse(nlp_result)
            
            # Step 3: Safety Validation
            safety_check = await self.safety_manager.validate_command(parsed_command)
            if not safety_check.is_safe:
                return ExecutionResult(
                    success=False,
                    message=f"Safety check failed: {safety_check.reason}",
                    errors=[safety_check.reason]
                )
            
            # Step 4: Skill Selection and Execution
            execution_plan = await self.skill_manager.create_execution_plan(parsed_command)
            
            # Step 5: Execute in Blender
            blender_result = await self.blender_bridge.execute_plan(execution_plan)
            
            # Step 6: Analyze Results and Learn
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = ExecutionResult(
                success=blender_result.success,
                message=blender_result.message,
                data=blender_result.data,
                execution_time=execution_time,
                skills_used=execution_plan.skills_used,
                errors=blender_result.errors
            )
            
            # Store for learning
            await self.learning_engine.record_execution(command, result)
            self.execution_results.append(result)
            
            self.logger.info(f"Command executed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = ExecutionResult(
                success=False,
                message=f"Execution failed: {str(e)}",
                execution_time=execution_time,
                errors=[str(e)]
            )
            
            self.logger.error(f"Command execution failed: {e}")
            return error_result
    
    async def get_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions based on partial input"""
        return await self.nlp_processor.get_suggestions(partial_command)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "session_id": self.session_id,
            "is_running": self.is_running,
            "commands_executed": len(self.execution_results),
            "success_rate": self._calculate_success_rate(),
            "blender_connected": await self.blender_bridge.is_connected(),
            "available_skills": await self.skill_manager.get_available_skills()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate command success rate"""
        if not self.execution_results:
            return 0.0
        
        successful = sum(1 for result in self.execution_results if result.success)
        return successful / len(self.execution_results)
    
    async def optimize_performance(self):
        """Trigger performance optimization"""
        await self.learning_engine.optimize_skills()
        self.logger.info("Performance optimization completed")
    
    async def export_session_data(self) -> Dict[str, Any]:
        """Export session data for analysis"""
        return {
            "session_id": self.session_id,
            "commands": [
                {
                    "text": cmd.text,
                    "timestamp": cmd.timestamp.isoformat(),
                    "context": cmd.context
                }
                for cmd in self.command_history
            ],
            "results": [
                {
                    "success": result.success,
                    "message": result.message,
                    "execution_time": result.execution_time,
                    "skills_used": result.skills_used
                }
                for result in self.execution_results
            ],
            "performance": {
                "success_rate": self._calculate_success_rate(),
                "average_execution_time": self._calculate_average_execution_time(),
                "most_used_skills": self._get_most_used_skills()
            }
        }
    
    def _calculate_average_execution_time(self) -> float:
        """Calculate average execution time"""
        if not self.execution_results:
            return 0.0
        
        total_time = sum(result.execution_time for result in self.execution_results)
        return total_time / len(self.execution_results)
    
    def _get_most_used_skills(self) -> List[str]:
        """Get list of most frequently used skills"""
        skill_counts = {}
        for result in self.execution_results:
            if result.skills_used:
                for skill in result.skills_used:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        return sorted(skill_counts.keys(), key=lambda x: skill_counts[x], reverse=True)[:10]


# Convenience functions for common operations
async def create_agent(config_path: str = "config.yaml") -> MiktosAgent:
    """Create and initialize a Miktos agent"""
    try:
        import yaml  # type: ignore
    except ImportError:
        raise ImportError("PyYAML not installed. Install with: pip install PyYAML")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    agent = MiktosAgent(config)
    return agent


async def quick_execute(command: str, config_path: str = "config.yaml") -> ExecutionResult:
    """Quick execution of a single command"""
    agent = await create_agent(config_path)
    session_id = await agent.start_session()
    
    try:
        result = await agent.execute_command(command)
        return result
    finally:
        await agent.stop_session()


if __name__ == "__main__":
    # Example usage
    async def main():
        agent = await create_agent()
        session_id = await agent.start_session()
        
        # Example commands
        commands = [
            "Create a cube and subdivide it 3 times",
            "Add a metallic material to the selected object",
            "Create a three-point lighting setup"
        ]
        
        for command in commands:
            result = await agent.execute_command(command)
            print(f"Command: {command}")
            print(f"Result: {result.message}")
            print(f"Success: {result.success}")
            print("---")
        
        await agent.stop_session()
    
    asyncio.run(main())
