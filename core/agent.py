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
from .llm_integration import LLMIntegration  # type: ignore
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
        agent_config = config.get('agent', {})
        self.nlp_processor = NLPProcessor(agent_config.get('nlp', {}))
        self.command_parser = CommandParser(agent_config.get('parser', {}))
        self.safety_manager = SafetyManager(agent_config.get('safety', {}))
        self.learning_engine = LearningEngine(agent_config.get('learning', {}))
        
        # Initialize LLM integration (Priority 2 Enhancement)
        self.llm_integration = LLMIntegration(agent_config)
        
        # Initialize integration components
        self.blender_bridge = BlenderBridge(config.get('blender', {}))
        self.skill_manager = SkillManager(agent_config.get('skills', {}))
        
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
        Execute a natural language command with enhanced LLM intelligence
        
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
            # Step 1: Enhanced Natural Language Processing with LLM
            self.logger.info(f"Processing command: {command_text}")
            
            # Traditional NLP processing
            nlp_result = await self.nlp_processor.process(command_text, context)
            
            # Enhanced LLM understanding (Priority 2 Enhancement)
            enhanced_understanding = await self.llm_integration.enhance_command_understanding(
                command_text, 
                context or {}, 
                self.session_id or "default"
            )
            
            # Merge traditional NLP with LLM insights
            merged_result = self._merge_nlp_results(nlp_result, enhanced_understanding)
            
            # Step 2: Command Parsing and Intent Recognition  
            # Convert between module types by passing through dict representation
            parsed_command = await self.command_parser.parse(merged_result)  # type: ignore
            
            # Step 3: Safety Validation
            # Ensure compatibility between command parser and safety manager types
            safety_check = await self.safety_manager.validate_command(parsed_command)  # type: ignore
            if not safety_check.is_safe:
                error_message = safety_check.reason or "Unknown safety issue"
                return ExecutionResult(
                    success=False,
                    message=f"Safety check failed: {error_message}",
                    errors=[error_message]
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
            
            # Store for learning (cast to avoid type conflicts)
            await self.learning_engine.record_execution(command, result)  # type: ignore
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
    
    def _merge_nlp_results(self, nlp_result, enhanced_understanding: Dict[str, Any]):
        """
        Merge traditional NLP results with LLM enhanced understanding
        """
        # Create a copy of the original NLP result
        merged = nlp_result.__dict__.copy() if hasattr(nlp_result, '__dict__') else {}
        
        # Enhance with LLM insights
        if enhanced_understanding.get('confidence', 0) > merged.get('confidence', 0):
            merged['intent'] = enhanced_understanding.get('enhanced_intent', merged.get('intent', 'unknown'))
            merged['confidence'] = enhanced_understanding.get('confidence', merged.get('confidence', 0.5))
        
        # Merge entities and parameters
        if 'parameters' in enhanced_understanding:
            merged['entities'] = merged.get('entities', {})
            merged['entities'].update(enhanced_understanding['parameters'])
        
        # Add LLM suggestions
        merged['suggestions'] = enhanced_understanding.get('suggestions', [])
        merged['llm_metadata'] = enhanced_understanding.get('metadata', {})
        
        # Return an NLPResult-like object
        from .nlp_processor import NLPResult
        return NLPResult(
            intent=merged.get('intent', 'unknown'),
            entities=merged.get('entities', {}),
            confidence=merged.get('confidence', 0.5),
            context=merged.get('context', {}),
            processed_text=merged.get('processed_text', ''),
            suggestions=merged.get('suggestions', []),
            original_text=merged.get('original_text', '')
        )
    
    async def generate_workflow(self, task_description: str) -> Dict[str, Any]:
        """
        Generate an intelligent workflow for complex tasks using LLM
        """
        try:
            available_skills = await self.skill_manager.get_available_skills()
            
            # Convert skill dicts to skill names for LLM
            skill_names = []
            if isinstance(available_skills, list):
                for skill in available_skills:
                    if isinstance(skill, dict):
                        skill_names.append(skill.get('name', str(skill)))
                    else:
                        skill_names.append(str(skill))
            
            # Get basic scene state
            scene_state = {"objects": [], "materials": [], "lights": []}
            
            workflow = await self.llm_integration.generate_workflow(
                task_description,
                skill_names,
                scene_state,
                self.session_id or "default"
            )
            
            self.logger.info(f"Generated workflow for: {task_description}")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Workflow generation failed: {e}")
            return {
                'steps': [{'description': f'Complete task: {task_description}'}],
                'estimated_total_time': 60,
                'complexity': 'unknown'
            }
    
    async def get_intelligent_suggestions(self, partial_command: str) -> List[str]:
        """
        Get intelligent command suggestions using both traditional NLP and LLM
        """
        try:
            # Get traditional suggestions
            basic_suggestions = await self.nlp_processor.get_suggestions(partial_command)
            
            # Get LLM-enhanced suggestions with basic context
            context = {"session_id": self.session_id, "recent_commands": len(self.command_history)}
            enhanced_understanding = await self.llm_integration.enhance_command_understanding(
                partial_command,
                context,
                self.session_id or "default"
            )
            
            llm_suggestions = enhanced_understanding.get('suggestions', [])
            
            # Combine and deduplicate
            all_suggestions = list(set(basic_suggestions + llm_suggestions))
            return all_suggestions[:10]  # Limit to top 10
            
        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {e}")
            return await self.nlp_processor.get_suggestions(partial_command)


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
