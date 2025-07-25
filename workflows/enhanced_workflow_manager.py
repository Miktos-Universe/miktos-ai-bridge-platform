"""
Enhanced Workflow Manager for Miktos AI Bridge Platform
Priority 2: Intelligence Layer Enhancement

Provides sophisticated workflow management with LLM-enhanced templates,
context-aware suggestions, and automated workflow optimization.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    estimated_time: int  # seconds
    node_type: str
    required_inputs: List[str]
    outputs: List[str]
    
    
@dataclass
class WorkflowTemplate:
    """Enhanced workflow template with metadata and optimization hints"""
    id: str
    name: str
    description: str
    category: str
    complexity: str  # simple, intermediate, advanced, expert
    steps: List[WorkflowStep]
    parameters: Dict[str, Any]
    estimated_total_time: int
    success_rate: float
    usage_count: int
    tags: List[str]
    created_at: str
    updated_at: str
    version: str
    author: str
    requirements: List[str]  # Required models, plugins, etc.


class EnhancedWorkflowManager:
    """
    Enhanced workflow management system with LLM integration and
    intelligent template generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.usage_analytics = {}
        self.performance_metrics = {}
        
        # Load built-in templates
        self._initialize_enhanced_templates()
        
        # Template generation via LLM (if available)
        self.llm_enabled = self.config.get('llm', {}).get('enabled', False)
    
    def _initialize_enhanced_templates(self):
        """Initialize comprehensive set of workflow templates"""
        
        # 1. Basic Object Creation Workflow
        self.templates["basic_object_creation"] = WorkflowTemplate(
            id="basic_object_creation",
            name="Basic Object Creation",
            description="Create primitive objects with basic materials",
            category="modeling",
            complexity="simple",
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Create Object",
                    description="Create primitive mesh object",
                    parameters={
                        "type": "cube",
                        "location": [0, 0, 0],
                        "scale": [1, 1, 1]
                    },
                    dependencies=[],
                    estimated_time=5,
                    node_type="object_creation",
                    required_inputs=[],
                    outputs=["mesh_object"]
                ),
                WorkflowStep(
                    id="step_2", 
                    name="Apply Basic Material",
                    description="Add and configure basic material",
                    parameters={
                        "material_type": "principled_bsdf",
                        "base_color": [0.8, 0.8, 0.8, 1.0]
                    },
                    dependencies=["step_1"],
                    estimated_time=10,
                    node_type="material_creation",
                    required_inputs=["mesh_object"],
                    outputs=["material"]
                )
            ],
            parameters={
                "object_type": "cube",
                "material_color": [0.8, 0.8, 0.8, 1.0],
                "enable_subdivision": False
            },
            estimated_total_time=15,
            success_rate=0.95,
            usage_count=0,
            tags=["basic", "object", "material", "modeling"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            version="1.0",
            author="Miktos AI",
            requirements=[]
        )
        
        # 2. Advanced PBR Material Workflow
        self.templates["advanced_pbr_material"] = WorkflowTemplate(
            id="advanced_pbr_material",
            name="Advanced PBR Material Setup",
            description="Create photorealistic materials with texture maps",
            category="materials",
            complexity="intermediate", 
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Load Base Color Texture",
                    description="Load and configure base color texture",
                    parameters={
                        "texture_path": "",
                        "colorspace": "sRGB",
                        "interpolation": "Linear"
                    },
                    dependencies=[],
                    estimated_time=10,
                    node_type="texture_loading",
                    required_inputs=[],
                    outputs=["base_color_texture"]
                ),
                WorkflowStep(
                    id="step_2",
                    name="Load Normal Map",
                    description="Configure normal map for surface detail",
                    parameters={
                        "texture_path": "",
                        "colorspace": "Non-Color",
                        "strength": 1.0
                    },
                    dependencies=[],
                    estimated_time=10,
                    node_type="normal_mapping",
                    required_inputs=[],
                    outputs=["normal_map"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="Setup Material Properties",
                    description="Configure metallic, roughness, and other PBR properties",
                    parameters={
                        "metallic": 0.0,
                        "roughness": 0.5,
                        "specular": 0.5,
                        "ior": 1.45
                    },
                    dependencies=["step_1", "step_2"],
                    estimated_time=15,
                    node_type="pbr_setup",
                    required_inputs=["base_color_texture", "normal_map"],
                    outputs=["pbr_material"]
                )
            ],
            parameters={
                "material_name": "PBR_Material",
                "use_normal_map": True,
                "use_roughness_map": True,
                "use_metallic_map": False
            },
            estimated_total_time=35,
            success_rate=0.88,
            usage_count=0,
            tags=["pbr", "material", "texture", "photorealistic", "advanced"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            version="1.2",
            author="Miktos AI",
            requirements=["Blender 3.6+", "Principled BSDF"]
        )
        
        # 3. Professional Lighting Setup
        self.templates["professional_lighting"] = WorkflowTemplate(
            id="professional_lighting",
            name="Professional Three-Point Lighting",
            description="Setup industry-standard three-point lighting system",
            category="lighting",
            complexity="intermediate",
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Create Key Light",
                    description="Primary light source at 45-degree angle",
                    parameters={
                        "type": "sun",
                        "energy": 5.0,
                        "angle": 0.533,
                        "location": [4, -4, 6],
                        "rotation": [0.6155, 0.0556, 0.7854]
                    },
                    dependencies=[],
                    estimated_time=15,
                    node_type="light_creation",
                    required_inputs=[],
                    outputs=["key_light"]
                ),
                WorkflowStep(
                    id="step_2",
                    name="Create Fill Light",
                    description="Secondary light to reduce harsh shadows",
                    parameters={
                        "type": "area",
                        "energy": 2.0,
                        "size": 2.0,
                        "location": [-4, -2, 4],
                        "rotation": [0.4636, -0.5236, 0]
                    },
                    dependencies=[],
                    estimated_time=15,
                    node_type="light_creation", 
                    required_inputs=[],
                    outputs=["fill_light"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="Create Rim Light",
                    description="Backlight for edge definition and separation",
                    parameters={
                        "type": "spot",
                        "energy": 3.0,
                        "spot_size": 0.785,
                        "location": [0, 4, 2],
                        "rotation": [-0.7854, 0, 0]
                    },
                    dependencies=[],
                    estimated_time=15,
                    node_type="light_creation",
                    required_inputs=[],
                    outputs=["rim_light"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="Configure Shadows",
                    description="Optimize shadow settings for quality",
                    parameters={
                        "shadow_soft_size": 0.1,
                        "contact_shadows": True,
                        "cascade_size": 0.1
                    },
                    dependencies=["step_1", "step_2", "step_3"],
                    estimated_time=10,
                    node_type="shadow_config",
                    required_inputs=["key_light", "fill_light", "rim_light"],
                    outputs=["lighting_setup"]
                )
            ],
            parameters={
                "color_temperature": 6500,
                "use_soft_shadows": True,
                "ambient_occlusion": True,
                "bloom_enabled": False
            },
            estimated_total_time=55,
            success_rate=0.92,
            usage_count=0,
            tags=["lighting", "three-point", "professional", "shadows", "cinematic"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            version="1.1",
            author="Miktos AI",
            requirements=["Cycles Render Engine"]
        )
        
        # 4. Procedural Animation Workflow
        self.templates["procedural_animation"] = WorkflowTemplate(
            id="procedural_animation",
            name="Procedural Animation Setup",
            description="Create procedural animations with drivers and modifiers",
            category="animation",
            complexity="advanced",
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Setup Empty Controller",
                    description="Create empty object for animation control",
                    parameters={
                        "name": "Animation_Controller",
                        "location": [0, 0, 0],
                        "custom_properties": {
                            "rotation_speed": 1.0,
                            "amplitude": 2.0
                        }
                    },
                    dependencies=[],
                    estimated_time=10,
                    node_type="empty_creation",
                    required_inputs=[],
                    outputs=["controller"]
                ),
                WorkflowStep(
                    id="step_2",
                    name="Add Wave Modifier",
                    description="Apply wave modifier for procedural deformation",
                    parameters={
                        "use_z": False,
                        "use_x": True,
                        "height": 0.5,
                        "width": 1.0,
                        "speed": 1.0,
                        "start_position_object": "Animation_Controller"
                    },
                    dependencies=["step_1"],
                    estimated_time=20,
                    node_type="modifier_add",
                    required_inputs=["controller", "target_object"],
                    outputs=["wave_modifier"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="Setup Driver System",
                    description="Create drivers for parameter control",
                    parameters={
                        "driver_type": "AVERAGE",
                        "expression": "var * frame / 24",
                        "variables": ["rotation_speed"]
                    },
                    dependencies=["step_2"],
                    estimated_time=25,
                    node_type="driver_setup",
                    required_inputs=["wave_modifier", "controller"],
                    outputs=["driver_system"]
                )
            ],
            parameters={
                "frame_start": 1,
                "frame_end": 250,
                "playback_speed": 24,
                "loop_animation": True
            },
            estimated_total_time=55,
            success_rate=0.78,
            usage_count=0,
            tags=["animation", "procedural", "drivers", "modifiers", "advanced"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(), 
            version="1.0",
            author="Miktos AI",
            requirements=["Blender 3.0+", "Animation Workspace"]
        )
        
        # 5. Particle System Effects
        self.templates["particle_effects"] = WorkflowTemplate(
            id="particle_effects",
            name="Particle System Effects",
            description="Create complex particle systems for visual effects",
            category="effects",
            complexity="advanced",
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Create Emitter Object",
                    description="Setup particle emitter geometry",
                    parameters={
                        "type": "plane",
                        "subdivisions": 10,
                        "location": [0, 0, 0],
                        "scale": [2, 2, 1]
                    },
                    dependencies=[],
                    estimated_time=10,
                    node_type="emitter_setup",
                    required_inputs=[],
                    outputs=["emitter"]
                ),
                WorkflowStep(
                    id="step_2",
                    name="Configure Particle System",
                    description="Setup particle emission parameters",
                    parameters={
                        "type": "EMITTER",
                        "count": 1000,
                        "emit_from": "FACE",
                        "distribution": "RAND",
                        "lifetime": 100,
                        "normal_factor": 1.0
                    },
                    dependencies=["step_1"],
                    estimated_time=20,
                    node_type="particle_system",
                    required_inputs=["emitter"],
                    outputs=["particle_system"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="Add Physics Forces",
                    description="Configure gravity and force fields",
                    parameters={
                        "gravity": -9.81,
                        "wind_factor": 0.1,
                        "turbulence": 0.5,
                        "brownian_factor": 0.1
                    },
                    dependencies=["step_2"],
                    estimated_time=15,
                    node_type="physics_forces",
                    required_inputs=["particle_system"],
                    outputs=["physics_setup"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="Setup Particle Rendering",
                    description="Configure particle visualization",
                    parameters={
                        "render_as": "OBJECT",
                        "instance_object": "Cube",
                        "scale": 0.1,
                        "scale_randomness": 0.5
                    },
                    dependencies=["step_3"],
                    estimated_time=15,
                    node_type="particle_render",
                    required_inputs=["physics_setup"],
                    outputs=["render_setup"]
                )
            ],
            parameters={
                "particle_count": 1000,
                "simulation_start": 1,
                "simulation_end": 250,
                "use_collision": False
            },
            estimated_total_time=60,
            success_rate=0.82,
            usage_count=0,
            tags=["particles", "effects", "simulation", "physics", "advanced"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            version="1.0",
            author="Miktos AI",
            requirements=["Blender 3.0+", "Physics Properties"]
        )
        
        logger.info(f"Initialized {len(self.templates)} enhanced workflow templates")
    
    async def list_templates(self, category: Optional[str] = None, complexity: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available workflow templates with filtering"""
        templates = []
        
        for template in self.templates.values():
            # Apply filters
            if category and template.category != category:
                continue
            if complexity and template.complexity != complexity:
                continue
                
            templates.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "complexity": template.complexity,
                "estimated_time": template.estimated_total_time,
                "success_rate": template.success_rate,
                "usage_count": template.usage_count,
                "tags": template.tags,
                "version": template.version,
                "requirements": template.requirements
            })
        
        # Sort by usage count and success rate
        templates.sort(key=lambda x: (x["usage_count"], x["success_rate"]), reverse=True)
        return templates
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed template information"""
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        return asdict(template)
    
    async def recommend_templates(self, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend templates based on user context and history"""
        recommendations = []
        
        # Get user preferences from context
        user_skill_level = user_context.get('skill_level', 'intermediate')
        recent_categories = user_context.get('recent_categories', [])
        current_project_type = user_context.get('project_type', 'general')
        
        # Score templates based on relevance
        for template in self.templates.values():
            score = 0
            
            # Skill level matching
            if template.complexity == user_skill_level:
                score += 3
            elif abs(self._complexity_to_number(template.complexity) - 
                    self._complexity_to_number(user_skill_level)) <= 1:
                score += 1
            
            # Category relevance
            if template.category in recent_categories:
                score += 2
            
            # Success rate bonus
            score += template.success_rate * 2
            
            # Usage popularity
            score += min(template.usage_count / 100, 1.0)
            
            recommendations.append({
                "template": asdict(template),
                "score": score,
                "reason": self._generate_recommendation_reason(template, user_context)
            })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]
    
    def _complexity_to_number(self, complexity: str) -> int:
        """Convert complexity string to number for comparison"""
        mapping = {"simple": 1, "intermediate": 2, "advanced": 3, "expert": 4}
        return mapping.get(complexity, 2)
    
    def _generate_recommendation_reason(self, template: WorkflowTemplate, context: Dict[str, Any]) -> str:
        """Generate human-readable recommendation reason"""
        reasons = []
        
        if template.complexity == context.get('skill_level'):
            reasons.append(f"matches your {template.complexity} skill level")
        
        if template.category in context.get('recent_categories', []):
            reasons.append(f"aligns with your recent {template.category} work")
        
        if template.success_rate > 0.9:
            reasons.append("has high success rate")
        
        if template.usage_count > 50:
            reasons.append("is popular among users")
        
        return ", ".join(reasons) if reasons else "general recommendation"
    
    async def create_custom_template(
        self, 
        name: str, 
        description: str, 
        steps: List[Dict[str, Any]], 
        category: str = "custom",
        complexity: str = "intermediate"
    ) -> str:
        """Create custom workflow template"""
        template_id = f"custom_{uuid.uuid4().hex[:8]}"
        
        # Convert step dictionaries to WorkflowStep objects
        workflow_steps = []
        for i, step_data in enumerate(steps):
            workflow_steps.append(WorkflowStep(
                id=step_data.get('id', f"step_{i+1}"),
                name=step_data.get('name', f"Step {i+1}"),
                description=step_data.get('description', ''),
                parameters=step_data.get('parameters', {}),
                dependencies=step_data.get('dependencies', []),
                estimated_time=step_data.get('estimated_time', 30),
                node_type=step_data.get('node_type', 'custom'),
                required_inputs=step_data.get('required_inputs', []),
                outputs=step_data.get('outputs', [])
            ))
        
        # Calculate total estimated time
        total_time = sum(step.estimated_time for step in workflow_steps)
        
        # Create template
        template = WorkflowTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            complexity=complexity,
            steps=workflow_steps,
            parameters={},
            estimated_total_time=total_time,
            success_rate=0.7,  # Default for new templates
            usage_count=0,
            tags=["custom"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            version="1.0",
            author="User",
            requirements=[]
        )
        
        self.templates[template_id] = template
        logger.info(f"Created custom template: {name} ({template_id})")
        
        return template_id
    
    async def optimize_template(self, template_id: str, performance_data: Dict[str, Any]) -> bool:
        """Optimize template based on performance data"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        
        # Update success rate based on recent executions
        if 'success_count' in performance_data and 'total_executions' in performance_data:
            new_success_rate = performance_data['success_count'] / performance_data['total_executions']
            template.success_rate = (template.success_rate * 0.7) + (new_success_rate * 0.3)
        
        # Update estimated times based on actual execution times
        if 'average_execution_time' in performance_data:
            template.estimated_total_time = int(performance_data['average_execution_time'])
        
        # Update usage count
        template.usage_count += performance_data.get('new_usage_count', 1)
        
        # Mark as updated
        template.updated_at = datetime.now().isoformat()
        
        logger.info(f"Optimized template {template_id}: success_rate={template.success_rate:.2f}")
        return True
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get workflow analytics and insights"""
        total_templates = len(self.templates)
        categories = {}
        complexity_distribution = {}
        total_usage = 0
        
        for template in self.templates.values():
            # Category distribution
            categories[template.category] = categories.get(template.category, 0) + 1
            
            # Complexity distribution  
            complexity_distribution[template.complexity] = \
                complexity_distribution.get(template.complexity, 0) + 1
            
            # Total usage
            total_usage += template.usage_count
        
        # Calculate averages
        avg_success_rate = sum(t.success_rate for t in self.templates.values()) / total_templates
        avg_execution_time = sum(t.estimated_total_time for t in self.templates.values()) / total_templates
        
        return {
            "total_templates": total_templates,
            "total_usage": total_usage,
            "average_success_rate": avg_success_rate,
            "average_execution_time": avg_execution_time,
            "category_distribution": categories,
            "complexity_distribution": complexity_distribution,
            "most_popular_templates": [
                {"id": t.id, "name": t.name, "usage_count": t.usage_count}
                for t in sorted(self.templates.values(), key=lambda x: x.usage_count, reverse=True)[:5]
            ],
            "highest_success_rate": [
                {"id": t.id, "name": t.name, "success_rate": t.success_rate}
                for t in sorted(self.templates.values(), key=lambda x: x.success_rate, reverse=True)[:5]
            ]
        }
