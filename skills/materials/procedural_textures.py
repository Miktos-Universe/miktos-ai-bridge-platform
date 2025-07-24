"""
Procedural Textures Skills for Blender

Expert-level skills for creating procedural texture networks
"""

from typing import Dict, List, Any, Optional
from skills.skill_manager import miktos_skill  # type: ignore
from agent.blender_bridge import BlenderOperation  # type: ignore


@miktos_skill(
    name="create_noise_texture",
    category="materials",
    description="Create advanced noise texture with multiple octaves and distortion",
    complexity=0.4,
    parameters={
        'material_name': {'type': 'string', 'default': 'Material'},
        'noise_type': {'type': 'string', 'default': 'PERLIN', 
                      'options': ['PERLIN', 'RIDGED', 'HYBRID', 'FBM', 'HETERO_TERRAIN']},
        'scale': {'type': 'float', 'default': 5.0, 'min': 0.1, 'max': 1000.0},
        'detail': {'type': 'float', 'default': 2.0, 'min': 0.0, 'max': 16.0},
        'roughness': {'type': 'float', 'default': 0.5, 'min': 0.0, 'max': 1.0},
        'distortion': {'type': 'float', 'default': 0.0, 'min': 0.0, 'max': 1000.0}
    }
)
async def create_noise_texture(material_name: str = "Material", noise_type: str = "PERLIN",
                              scale: float = 5.0, detail: float = 2.0, roughness: float = 0.5,
                              distortion: float = 0.0,
                              _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create advanced procedural noise texture
    
    Features:
    - Multiple noise algorithms (Perlin, Ridged, FBM, etc.)
    - Fractal detail control
    - Distortion for complex patterns
    - Scale and roughness control
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create {noise_type} noise texture with {scale} scale",
            "complexity": 0.4
        }
    
    # Add noise texture node
    operations.append(BlenderOperation(
        operation_type="add_texture_node",
        target="material",
        parameters={
            "material_name": material_name,
            "node_type": "ShaderNodeTexNoise",
            "name": "Noise_Texture",
            "inputs": {
                "scale": scale,
                "detail": detail,
                "roughness": roughness,
                "distortion": distortion
            },
            "properties": {
                "noise_type": noise_type
            }
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created {noise_type} noise texture with {scale} scale",
        "success": True
    }


@miktos_skill(
    name="create_brick_texture",
    category="materials",
    description="Create realistic brick texture with mortar and randomization",
    complexity=0.5,
    parameters={
        'material_name': {'type': 'string', 'default': 'Material'},
        'brick_color1': {'type': 'color', 'default': [0.8, 0.2, 0.1, 1.0]},
        'brick_color2': {'type': 'color', 'default': [0.6, 0.15, 0.08, 1.0]},
        'mortar_color': {'type': 'color', 'default': [0.9, 0.9, 0.8, 1.0]},
        'scale': {'type': 'float', 'default': 15.0, 'min': 1.0, 'max': 100.0},
        'mortar_size': {'type': 'float', 'default': 0.02, 'min': 0.0, 'max': 0.1},
        'mortar_smooth': {'type': 'float', 'default': 0.1, 'min': 0.0, 'max': 1.0},
        'bias': {'type': 'float', 'default': 0.0, 'min': -1.0, 'max': 1.0}
    }
)
async def create_brick_texture(material_name: str = "Material", 
                              brick_color1: Optional[List[float]] = None,
                              brick_color2: Optional[List[float]] = None,
                              mortar_color: Optional[List[float]] = None,
                              scale: float = 15.0, mortar_size: float = 0.02,
                              mortar_smooth: float = 0.1, bias: float = 0.0,
                              _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create realistic brick pattern texture
    
    Features:
    - Dual brick colors for variation
    - Mortar color and size control
    - Smoothness and bias adjustments
    - Proper UV scaling
    """
    
    if brick_color1 is None:
        brick_color1 = [0.8, 0.2, 0.1, 1.0]
    if brick_color2 is None:
        brick_color2 = [0.6, 0.15, 0.08, 1.0]
    if mortar_color is None:
        mortar_color = [0.9, 0.9, 0.8, 1.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create brick texture with {scale} scale",
            "complexity": 0.5
        }
    
    # Add brick texture node
    operations.append(BlenderOperation(
        operation_type="add_texture_node",
        target="material",
        parameters={
            "material_name": material_name,
            "node_type": "ShaderNodeTexBrick",
            "name": "Brick_Texture",
            "inputs": {
                "color1": brick_color1,
                "color2": brick_color2,
                "mortar": mortar_color,
                "scale": scale,
                "mortar_size": mortar_size,
                "mortar_smooth": mortar_smooth,
                "bias": bias
            }
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created brick texture with {scale} scale",
        "success": True
    }


@miktos_skill(
    name="create_wood_texture",
    category="materials",
    description="Create realistic wood grain texture with rings and detail",
    complexity=0.6,
    parameters={
        'material_name': {'type': 'string', 'default': 'Material'},
        'ring_scale': {'type': 'float', 'default': 20.0, 'min': 1.0, 'max': 100.0},
        'ring_noise': {'type': 'float', 'default': 0.8, 'min': 0.0, 'max': 2.0},
        'grain_scale': {'type': 'float', 'default': 50.0, 'min': 1.0, 'max': 200.0},
        'grain_strength': {'type': 'float', 'default': 0.3, 'min': 0.0, 'max': 1.0},
        'color_variation': {'type': 'float', 'default': 0.2, 'min': 0.0, 'max': 1.0},
        'base_color': {'type': 'color', 'default': [0.6, 0.3, 0.1, 1.0]}
    }
)
async def create_wood_texture(material_name: str = "Material", ring_scale: float = 20.0,
                             ring_noise: float = 0.8, grain_scale: float = 50.0,
                             grain_strength: float = 0.3, color_variation: float = 0.2,
                             base_color: Optional[List[float]] = None,
                             _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create realistic wood grain procedural texture
    
    Features:
    - Growth ring simulation
    - Grain detail overlay
    - Color variation control
    - Natural wood parameters
    """
    
    if base_color is None:
        base_color = [0.6, 0.3, 0.1, 1.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create wood texture with {ring_scale} ring scale",
            "complexity": 0.6
        }
    
    # Create wood ring pattern
    operations.append(BlenderOperation(
        operation_type="create_wood_shader",
        target="material",
        parameters={
            "material_name": material_name,
            "ring_scale": ring_scale,
            "ring_noise": ring_noise,
            "grain_scale": grain_scale,
            "grain_strength": grain_strength,
            "color_variation": color_variation,
            "base_color": base_color
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created wood texture with {ring_scale} ring scale",
        "success": True
    }
