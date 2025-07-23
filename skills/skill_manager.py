"""
Miktos Skills Manager

Manages and executes expert-level Blender automation skills.
Each skill is a specialized function that performs specific 3D operations.
"""

import asyncio
import importlib
import importlib.util
import inspect
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path

from core.nlp_processor import NLPIntent  # type: ignore
from agent.blender_bridge import BlenderOperation, ExecutionPlan  # type: ignore


@dataclass
class Skill:
    """Represents a single automation skill"""
    name: str
    category: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    complexity: float  # 0.0 to 1.0
    success_rate: float = 1.0
    average_execution_time: float = 0.0
    usage_count: int = 0


@dataclass
class SkillResult:
    """Result of skill execution"""
    skill_name: str
    success: bool
    operations: List[BlenderOperation]
    message: str
    execution_time: float = 0.0
    errors: Optional[List[str]] = None


class SkillManager:
    """
    Manages the library of Blender automation skills
    Handles skill discovery, selection, and execution planning
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.skills: Dict[str, Skill] = {}
        
        # Setup logging
        self.logger = logging.getLogger('SkillManager')
        
        # Load skills from library
        self._load_skills()
    
    def _load_skills(self):
        """Load all available skills from the skills library"""
        skills_dir = Path(__file__).parent.parent / "skills"
        
        # Load modeling skills
        self._load_skill_module(skills_dir / "modeling" / "primitives.py")
        self._load_skill_module(skills_dir / "modeling" / "mesh_operations.py")
        self._load_skill_module(skills_dir / "modeling" / "modifiers.py")
        
        # Load material skills
        self._load_skill_module(skills_dir / "materials" / "pbr_materials.py")
        self._load_skill_module(skills_dir / "materials" / "procedural_textures.py")
        
        # Load lighting skills
        self._load_skill_module(skills_dir / "lighting" / "studio_lighting.py")
        self._load_skill_module(skills_dir / "lighting" / "environment_lighting.py")
        
        self.logger.info(f"Loaded {len(self.skills)} skills")
    
    def _load_skill_module(self, module_path: Path):
        """Load skills from a specific module"""
        if not module_path.exists():
            return
        
        try:
            # Import module dynamically
            spec = importlib.util.spec_from_file_location("skill_module", module_path)
            if spec is None or spec.loader is None:
                self.logger.warning(f"Could not create spec for {module_path}")
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find skill functions
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and hasattr(obj, '_miktos_skill'):
                    skill_info = obj._miktos_skill
                    
                    skill = Skill(
                        name=skill_info['name'],
                        category=skill_info['category'],
                        description=skill_info['description'],
                        function=obj,
                        parameters=skill_info.get('parameters', {}),
                        complexity=skill_info.get('complexity', 0.5)
                    )
                    
                    self.skills[skill.name] = skill
                    self.logger.debug(f"Loaded skill: {skill.name}")
                    
        except Exception as e:
            self.logger.error(f"Failed to load skill module {module_path}: {e}")
    
    async def create_execution_plan(self, parsed_command) -> ExecutionPlan:
        """Create execution plan from parsed command"""
        
        # Find relevant skills
        relevant_skills = await self._find_relevant_skills(parsed_command)
        
        if not relevant_skills:
            raise ValueError("No suitable skills found for command")
        
        # Select best skill combination
        selected_skills = self._select_best_skills(relevant_skills, parsed_command)
        
        # Generate operations
        operations = []
        skills_used = []
        
        for skill in selected_skills:
            skill_result = await self._execute_skill_planning(skill, parsed_command)
            operations.extend(skill_result.operations)
            skills_used.append(skill.name)
        
        # Create execution plan
        plan = ExecutionPlan(
            operations=operations,
            dependencies=self._calculate_dependencies(operations),
            rollback_plan=self._create_rollback_plan(operations),
            skills_used=skills_used,
            estimated_time=sum(skill.average_execution_time for skill in selected_skills)
        )
        
        return plan
    
    async def _find_relevant_skills(self, parsed_command) -> List[Skill]:
        """Find skills relevant to the parsed command"""
        relevant_skills = []
        
        # Extract intents from parsed command
        intents = getattr(parsed_command, 'intents', [])
        
        for intent in intents:
            # Match skills by category and action
            skill_pattern = f"{intent.action}_{intent.target}"
            
            for skill_name, skill in self.skills.items():
                if self._skill_matches_intent(skill, intent):
                    relevant_skills.append(skill)
        
        return relevant_skills
    
    def _skill_matches_intent(self, skill: Skill, intent: NLPIntent) -> bool:
        """Check if a skill matches an intent"""
        # Simple pattern matching
        skill_parts = skill.name.lower().split('_')
        intent_parts = [intent.action.lower(), intent.target.lower()]
        
        # Check for overlap
        return any(part in skill_parts for part in intent_parts)
    
    def _select_best_skills(self, relevant_skills: List[Skill], parsed_command) -> List[Skill]:
        """Select the best skills for execution"""
        if not relevant_skills:
            return []
        
        # Score skills based on success rate, complexity, and relevance
        scored_skills = []
        for skill in relevant_skills:
            score = self._calculate_skill_score(skill, parsed_command)
            scored_skills.append((skill, score))
        
        # Sort by score (highest first)
        scored_skills.sort(key=lambda x: x[1], reverse=True)
        
        # Return top skills (limit to prevent over-complexity)
        max_skills = self.config.get('max_skills_per_command', 3)
        return [skill for skill, score in scored_skills[:max_skills]]
    
    def _calculate_skill_score(self, skill: Skill, parsed_command) -> float:
        """Calculate relevance score for a skill"""
        score = 0.0
        
        # Success rate weight (40%)
        score += skill.success_rate * 0.4
        
        # Inverse complexity weight (30% - prefer simpler skills)
        score += (1.0 - skill.complexity) * 0.3
        
        # Usage frequency weight (20%)
        max_usage = max(s.usage_count for s in self.skills.values()) or 1
        score += (skill.usage_count / max_usage) * 0.2
        
        # Execution time weight (10% - prefer faster skills)
        max_time = max(s.average_execution_time for s in self.skills.values()) or 1
        score += (1.0 - (skill.average_execution_time / max_time)) * 0.1
        
        return score
    
    async def _execute_skill_planning(self, skill: Skill, parsed_command) -> SkillResult:
        """Execute skill in planning mode to get operations"""
        try:
            # Extract parameters from parsed command
            parameters = self._extract_skill_parameters(skill, parsed_command)
            
            # Call skill function in planning mode
            result = await self._call_skill_function(skill, parameters, planning_mode=True)
            
            return SkillResult(
                skill_name=skill.name,
                success=True,
                operations=result.get('operations', []),
                message=result.get('message', f'Planned {skill.name}')
            )
            
        except Exception as e:
            self.logger.error(f"Skill planning failed for {skill.name}: {e}")
            return SkillResult(
                skill_name=skill.name,
                success=False,
                operations=[],
                message=f"Planning failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _extract_skill_parameters(self, skill: Skill, parsed_command) -> Dict[str, Any]:
        """Extract parameters for skill from parsed command"""
        parameters = {}
        
        # Get intents from parsed command
        intents = getattr(parsed_command, 'intents', [])
        
        for intent in intents:
            # Map intent parameters to skill parameters
            for param_name, param_value in intent.parameters.items():
                if param_name in skill.parameters:
                    parameters[param_name] = param_value
        
        # Add default parameters if not provided
        for param_name, param_info in skill.parameters.items():
            if param_name not in parameters:
                parameters[param_name] = param_info.get('default')
        
        return parameters
    
    async def _call_skill_function(self, skill: Skill, parameters: Dict[str, Any], planning_mode: bool = False) -> Dict[str, Any]:
        """Call a skill function with parameters"""
        try:
            # Add planning mode flag
            parameters['_planning_mode'] = planning_mode
            
            # Call function
            if asyncio.iscoroutinefunction(skill.function):
                result = await skill.function(**parameters)
            else:
                result = skill.function(**parameters)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Skill function call failed: {e}")
            raise
    
    def _calculate_dependencies(self, operations: List[BlenderOperation]) -> Dict[str, List[str]]:
        """Calculate dependencies between operations"""
        dependencies = {}
        
        # Simple dependency analysis
        for i, operation in enumerate(operations):
            op_id = f"op_{i}"
            dependencies[op_id] = []
            
            # If operation modifies an object, it depends on object creation
            if operation.operation_type == 'modify':
                for j, prev_op in enumerate(operations[:i]):
                    if prev_op.operation_type == 'create':
                        dependencies[op_id].append(f"op_{j}")
        
        return dependencies
    
    def _create_rollback_plan(self, operations: List[BlenderOperation]) -> List[BlenderOperation]:
        """Create rollback plan for operations"""
        rollback_operations = []
        
        # Reverse operations for rollback
        for operation in reversed(operations):
            if operation.operation_type == 'create':
                # Rollback: delete created object
                rollback_op = BlenderOperation(
                    operation_type='delete',
                    target=operation.target,
                    parameters={'object_name': operation.parameters.get('name')}
                )
                rollback_operations.append(rollback_op)
        
        return rollback_operations
    
    async def get_available_skills(self) -> List[Dict[str, Any]]:
        """Get list of available skills"""
        skills_list = []
        
        for skill in self.skills.values():
            skills_list.append({
                'name': skill.name,
                'category': skill.category,
                'description': skill.description,
                'complexity': skill.complexity,
                'success_rate': skill.success_rate,
                'usage_count': skill.usage_count
            })
        
        return skills_list
    
    def update_skill_performance(self, skill_name: str, success: bool, execution_time: float):
        """Update skill performance metrics"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            
            # Update usage count
            skill.usage_count += 1
            
            # Update success rate
            total_executions = skill.usage_count
            if success:
                skill.success_rate = ((skill.success_rate * (total_executions - 1)) + 1.0) / total_executions
            else:
                skill.success_rate = (skill.success_rate * (total_executions - 1)) / total_executions
            
            # Update average execution time
            skill.average_execution_time = ((skill.average_execution_time * (total_executions - 1)) + execution_time) / total_executions
    
    async def suggest_skills(self, query: str) -> List[str]:
        """Suggest skills based on a query"""
        suggestions = []
        query_lower = query.lower()
        
        for skill in self.skills.values():
            # Check name, category, and description
            if (query_lower in skill.name.lower() or 
                query_lower in skill.category.lower() or 
                query_lower in skill.description.lower()):
                suggestions.append(skill.name)
        
        return suggestions[:10]  # Return top 10 matches


# Skill decorator
def miktos_skill(name: str, category: str, description: str, complexity: float = 0.5, **kwargs):
    """Decorator to mark functions as Miktos skills"""
    def decorator(func):
        func._miktos_skill = {
            'name': name,
            'category': category,
            'description': description,
            'complexity': complexity,
            **kwargs
        }
        return func
    return decorator


if __name__ == "__main__":
    # Test the skill manager
    async def test_skill_manager():
        config = {'max_skills_per_command': 3}
        manager = SkillManager(config)
        
        # List available skills
        skills = await manager.get_available_skills()
        print(f"Available skills: {len(skills)}")
        for skill in skills[:5]:
            print(f"- {skill['name']}: {skill['description']}")
        
        # Test skill suggestions
        suggestions = await manager.suggest_skills("create cube")
        print(f"Suggestions for 'create cube': {suggestions}")
    
    asyncio.run(test_skill_manager())
