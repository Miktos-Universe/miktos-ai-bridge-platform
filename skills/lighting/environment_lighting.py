"""
Environment Lighting Skills for Blender

Expert-level skills for realistic environment and HDRI lighting
"""

from typing import Dict, List, Any, Optional
from skills.skill_manager import miktos_skill  # type: ignore
from agent.blender_bridge import BlenderOperation  # type: ignore


@miktos_skill(
    name="setup_hdri_lighting",
    category="lighting",
    description="Set up realistic HDRI environment lighting with proper exposure",
    complexity=0.6,
    parameters={
        'hdri_path': {'type': 'string', 'default': ''},
        'strength': {'type': 'float', 'default': 1.0, 'min': 0.0, 'max': 10.0},
        'rotation': {'type': 'float', 'default': 0.0, 'min': 0.0, 'max': 360.0},
        'background_strength': {'type': 'float', 'default': 1.0, 'min': 0.0, 'max': 10.0},
        'color_saturation': {'type': 'float', 'default': 1.0, 'min': 0.0, 'max': 2.0},
        'exposure': {'type': 'float', 'default': 0.0, 'min': -10.0, 'max': 10.0}
    }
)
async def setup_hdri_lighting(hdri_path: str = "", strength: float = 1.0,
                             rotation: float = 0.0, background_strength: float = 1.0,
                             color_saturation: float = 1.0, exposure: float = 0.0,
                             _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Set up realistic HDRI environment lighting
    
    Features:
    - HDRI texture loading and setup
    - Independent lighting and background control
    - Color saturation adjustment
    - Exposure compensation
    - Rotation for optimal lighting direction
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Setup HDRI environment lighting with {strength} strength",
            "complexity": 0.6
        }
    
    # Set world shader to use nodes
    operations.append(BlenderOperation(
        operation_type="setup_world_nodes",
        target="world",
        parameters={"use_nodes": True}
    ))
    
    # Load HDRI texture
    if hdri_path:
        operations.append(BlenderOperation(
            operation_type="load_hdri",
            target="world",
            parameters={
                "hdri_path": hdri_path,
                "name": "Environment_Texture"
            }
        ))
    
    # Set up environment shader
    operations.append(BlenderOperation(
        operation_type="setup_environment_shader",
        target="world",
        parameters={
            "strength": strength,
            "rotation": rotation,
            "background_strength": background_strength,
            "color_saturation": color_saturation,
            "exposure": exposure
        }
    ))
    
    # Configure film exposure
    operations.append(BlenderOperation(
        operation_type="set_film_exposure",
        target="scene",
        parameters={"exposure": exposure}
    ))
    
    return {
        "operations": operations,
        "message": f"Set up HDRI environment lighting with {strength} strength",
        "success": True
    }


@miktos_skill(
    name="create_sky_lighting",
    category="lighting",
    description="Create realistic procedural sky lighting with sun and atmosphere",
    complexity=0.5,
    parameters={
        'sky_type': {'type': 'string', 'default': 'PREETHAM', 
                    'options': ['PREETHAM', 'HOSEK_WILKIE', 'NISHITA']},
        'sun_elevation': {'type': 'float', 'default': 45.0, 'min': 0.0, 'max': 90.0},
        'sun_rotation': {'type': 'float', 'default': 0.0, 'min': 0.0, 'max': 360.0},
        'turbidity': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 10.0},
        'ground_albedo': {'type': 'float', 'default': 0.3, 'min': 0.0, 'max': 1.0},
        'strength': {'type': 'float', 'default': 1.0, 'min': 0.0, 'max': 10.0}
    }
)
async def create_sky_lighting(sky_type: str = "PREETHAM", sun_elevation: float = 45.0,
                             sun_rotation: float = 0.0, turbidity: float = 2.0,
                             ground_albedo: float = 0.3, strength: float = 1.0,
                             _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create realistic procedural sky lighting
    
    Features:
    - Multiple sky models (Preetham, Hosek-Wilkie, Nishita)
    - Sun position control
    - Atmospheric turbidity
    - Ground albedo for bounce lighting
    - Physically accurate colors
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create {sky_type} sky lighting with {sun_elevation}° sun elevation",
            "complexity": 0.5
        }
    
    # Set up world nodes
    operations.append(BlenderOperation(
        operation_type="setup_world_nodes",
        target="world",
        parameters={"use_nodes": True}
    ))
    
    # Create sky texture
    operations.append(BlenderOperation(
        operation_type="add_sky_texture",
        target="world",
        parameters={
            "sky_type": sky_type,
            "sun_elevation": sun_elevation,
            "sun_rotation": sun_rotation,
            "turbidity": turbidity,
            "ground_albedo": ground_albedo
        }
    ))
    
    # Set environment strength
    operations.append(BlenderOperation(
        operation_type="set_world_strength",
        target="world",
        parameters={"strength": strength}
    ))
    
    # Add sun lamp for shadows (optional but recommended)
    operations.append(BlenderOperation(
        operation_type="create_sun_light",
        target="scene",
        parameters={
            "elevation": sun_elevation,
            "rotation": sun_rotation,
            "strength": strength * 5.0,  # Sun is typically stronger
            "angle": 0.53  # Realistic sun angular size
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created {sky_type} sky lighting with {sun_elevation}° sun elevation",
        "success": True
    }


@miktos_skill(
    name="create_interior_lighting",
    category="lighting",
    description="Create realistic interior lighting with window light and ambient fill",
    complexity=0.7,
    parameters={
        'window_direction': {'type': 'vector3', 'default': [1.0, 0.0, 0.0]},
        'window_size': {'type': 'float', 'default': 2.0, 'min': 0.5, 'max': 10.0},
        'daylight_strength': {'type': 'float', 'default': 50.0, 'min': 1.0, 'max': 500.0},
        'ambient_strength': {'type': 'float', 'default': 10.0, 'min': 1.0, 'max': 100.0},
        'color_temperature': {'type': 'float', 'default': 6500.0, 'min': 2000.0, 'max': 12000.0},
        'bounce_intensity': {'type': 'float', 'default': 0.3, 'min': 0.0, 'max': 1.0}
    }
)
async def create_interior_lighting(window_direction: Optional[List[float]] = None,
                                  window_size: float = 2.0, daylight_strength: float = 50.0,
                                  ambient_strength: float = 10.0, color_temperature: float = 6500.0,
                                  bounce_intensity: float = 0.3,
                                  _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create realistic interior lighting setup
    
    Features:
    - Directional window light simulation
    - Ambient interior fill lighting
    - Color temperature control
    - Bounce light simulation
    - Natural light distribution
    """
    
    if window_direction is None:
        window_direction = [1.0, 0.0, 0.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create interior lighting with {daylight_strength}W window light",
            "complexity": 0.7
        }
    
    # Create main window light (area light)
    window_location = [d * 5.0 for d in window_direction]  # 5 units from origin
    operations.append(BlenderOperation(
        operation_type="create_light",
        target="scene",
        parameters={
            "type": "AREA",
            "name": "Window_Light",
            "location": window_location,
            "energy": daylight_strength,
            "color_temperature": color_temperature,
            "size": window_size,
            "shape": "RECTANGLE"
        }
    ))
    
    # Point window light inward
    operations.append(BlenderOperation(
        operation_type="orient_light",
        target="light",
        parameters={
            "light_name": "Window_Light",
            "direction": [-d for d in window_direction]  # Inward direction
        }
    ))
    
    # Create ambient fill lights (multiple small area lights)
    for i, (x, y, z) in enumerate([
        [3, 3, 2], [-3, 3, 2], [3, -3, 2], [-3, -3, 2]  # Corner positions
    ]):
        operations.append(BlenderOperation(
            operation_type="create_light",
            target="scene",
            parameters={
                "type": "AREA",
                "name": f"Ambient_Fill_{i+1}",
                "location": [x, y, z],
                "energy": ambient_strength,
                "color_temperature": color_temperature + 200,  # Slightly warmer
                "size": 1.0,
                "shape": "SQUARE"
            }
        ))
    
    # Create bounce light (from floor/walls)
    operations.append(BlenderOperation(
        operation_type="create_light",
        target="scene",
        parameters={
            "type": "AREA",
            "name": "Bounce_Light",
            "location": [0, 0, -1],  # Floor level
            "rotation": [0, 0, 0],  # Pointing up
            "energy": daylight_strength * bounce_intensity,
            "color_temperature": color_temperature + 500,  # Warmer bounce
            "size": 4.0,
            "shape": "SQUARE"
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created interior lighting with {daylight_strength}W window light",
        "success": True
    }
