"""
PBR Materials Skills for Blender

Expert-level skills for creating physically-based rendering materials
"""

from typing import Dict, List, Any, Optional
from skills.skill_manager import miktos_skill  # type: ignore
from agent.blender_bridge import BlenderOperation  # type: ignore


@miktos_skill(
    name="create_metal_material",
    category="materials",
    description="Create realistic metal PBR material with proper metallic workflow",
    complexity=0.6,
    parameters={
        'name': {'type': 'string', 'default': 'Metal_Material'},
        'base_color': {'type': 'color', 'default': [0.7, 0.7, 0.7, 1.0]},
        'metallic': {'type': 'float', 'default': 1.0, 'min': 0.0, 'max': 1.0},
        'roughness': {'type': 'float', 'default': 0.1, 'min': 0.0, 'max': 1.0},
        'ior': {'type': 'float', 'default': 1.45, 'min': 1.0, 'max': 3.0},
        'apply_to_active': {'type': 'bool', 'default': True}
    }
)
async def create_metal_material(name: str = "Metal_Material", base_color: Optional[List[float]] = None,
                               metallic: float = 1.0, roughness: float = 0.1,
                               ior: float = 1.45, apply_to_active: bool = True,
                               _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create realistic metal material using PBR principles
    
    Features:
    - Physically accurate metallic workflow
    - Proper fresnel reflections (IOR)
    - Energy conservation
    - Industry-standard parameter ranges
    """
    
    if base_color is None:
        base_color = [0.7, 0.7, 0.7, 1.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create metal PBR material '{name}' with {roughness} roughness",
            "complexity": 0.6
        }
    
    # Create new material
    operations.append(BlenderOperation(
        operation_type="create_material",
        target="scene",
        parameters={
            "name": name,
            "use_nodes": True
        }
    ))
    
    # Set up PBR metal shader
    operations.append(BlenderOperation(
        operation_type="setup_pbr_shader",
        target="material",
        parameters={
            "material_name": name,
            "base_color": base_color,
            "metallic": metallic,
            "roughness": roughness,
            "ior": ior,
            "specular": 0.5,  # Standard for metals
            "transmission": 0.0
        }
    ))
    
    # Apply to active object if requested
    if apply_to_active:
        operations.append(BlenderOperation(
            operation_type="assign_material",
            target="object",
            parameters={"material_name": name}
        ))
    
    return {
        "operations": operations,
        "message": f"Created metal PBR material '{name}' with {roughness} roughness",
        "success": True
    }


@miktos_skill(
    name="create_glass_material",
    category="materials",
    description="Create realistic glass material with transmission and refraction",
    complexity=0.7,
    parameters={
        'name': {'type': 'string', 'default': 'Glass_Material'},
        'base_color': {'type': 'color', 'default': [1.0, 1.0, 1.0, 1.0]},
        'transmission': {'type': 'float', 'default': 1.0, 'min': 0.0, 'max': 1.0},
        'roughness': {'type': 'float', 'default': 0.0, 'min': 0.0, 'max': 1.0},
        'ior': {'type': 'float', 'default': 1.45, 'min': 1.0, 'max': 3.0},
        'alpha': {'type': 'float', 'default': 0.1, 'min': 0.0, 'max': 1.0},
        'apply_to_active': {'type': 'bool', 'default': True}
    }
)
async def create_glass_material(name: str = "Glass_Material", base_color: Optional[List[float]] = None,
                               transmission: float = 1.0, roughness: float = 0.0,
                               ior: float = 1.45, alpha: float = 0.1,
                               apply_to_active: bool = True,
                               _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create realistic glass material with proper transmission
    
    Features:
    - Physical transmission model
    - Accurate refraction (IOR)
    - Surface roughness control
    - Alpha blending support
    """
    
    if base_color is None:
        base_color = [1.0, 1.0, 1.0, 1.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create glass material '{name}' with {transmission} transmission",
            "complexity": 0.7
        }
    
    # Create new material
    operations.append(BlenderOperation(
        operation_type="create_material",
        target="scene",
        parameters={
            "name": name,
            "use_nodes": True,
            "blend_method": "BLEND"
        }
    ))
    
    # Set up glass shader
    operations.append(BlenderOperation(
        operation_type="setup_glass_shader",
        target="material",
        parameters={
            "material_name": name,
            "base_color": base_color,
            "transmission": transmission,
            "roughness": roughness,
            "ior": ior,
            "alpha": alpha
        }
    ))
    
    # Apply to active object if requested
    if apply_to_active:
        operations.append(BlenderOperation(
            operation_type="assign_material",
            target="object",
            parameters={"material_name": name}
        ))
    
    return {
        "operations": operations,
        "message": f"Created glass material '{name}' with {transmission} transmission",
        "success": True
    }


@miktos_skill(
    name="create_fabric_material",
    category="materials",
    description="Create realistic fabric material with proper subsurface scattering",
    complexity=0.5,
    parameters={
        'name': {'type': 'string', 'default': 'Fabric_Material'},
        'base_color': {'type': 'color', 'default': [0.8, 0.2, 0.2, 1.0]},
        'subsurface': {'type': 'float', 'default': 0.3, 'min': 0.0, 'max': 1.0},
        'subsurface_color': {'type': 'color', 'default': [0.9, 0.3, 0.3, 1.0]},
        'roughness': {'type': 'float', 'default': 0.8, 'min': 0.0, 'max': 1.0},
        'sheen': {'type': 'float', 'default': 0.5, 'min': 0.0, 'max': 1.0},
        'apply_to_active': {'type': 'bool', 'default': True}
    }
)
async def create_fabric_material(name: str = "Fabric_Material", base_color: Optional[List[float]] = None,
                                subsurface: float = 0.3, subsurface_color: Optional[List[float]] = None,
                                roughness: float = 0.8, sheen: float = 0.5,
                                apply_to_active: bool = True,
                                _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create realistic fabric material with subsurface properties
    
    Features:
    - Subsurface scattering for realistic light penetration
    - Sheen for fabric highlights
    - High roughness for matte finish
    - Proper energy conservation
    """
    
    if base_color is None:
        base_color = [0.8, 0.2, 0.2, 1.0]
    if subsurface_color is None:
        subsurface_color = [0.9, 0.3, 0.3, 1.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create fabric material '{name}' with {subsurface} subsurface",
            "complexity": 0.5
        }
    
    # Create new material
    operations.append(BlenderOperation(
        operation_type="create_material",
        target="scene",
        parameters={
            "name": name,
            "use_nodes": True
        }
    ))
    
    # Set up fabric shader
    operations.append(BlenderOperation(
        operation_type="setup_fabric_shader",
        target="material",
        parameters={
            "material_name": name,
            "base_color": base_color,
            "subsurface": subsurface,
            "subsurface_color": subsurface_color,
            "roughness": roughness,
            "sheen": sheen,
            "metallic": 0.0,  # Fabrics are non-metallic
            "specular": 0.5
        }
    ))
    
    # Apply to active object if requested
    if apply_to_active:
        operations.append(BlenderOperation(
            operation_type="assign_material",
            target="object",
            parameters={"material_name": name}
        ))
    
    return {
        "operations": operations,
        "message": f"Created fabric material '{name}' with {subsurface} subsurface",
        "success": True
    }
