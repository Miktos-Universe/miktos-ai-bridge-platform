"""
Studio Lighting Skills for Blender

Expert-level skills for professional studio lighting setups
"""

from typing import Dict, List, Any, Optional
from skills.skill_manager import miktos_skill  # type: ignore
from agent.blender_bridge import BlenderOperation  # type: ignore


@miktos_skill(
    name="create_three_point_lighting",
    category="lighting",
    description="Create professional three-point lighting setup with key, fill, and rim lights",
    complexity=0.7,
    parameters={
        'target_object': {'type': 'string', 'default': ''},
        'key_power': {'type': 'float', 'default': 100.0, 'min': 1.0, 'max': 1000.0},
        'fill_power': {'type': 'float', 'default': 30.0, 'min': 1.0, 'max': 1000.0},
        'rim_power': {'type': 'float', 'default': 80.0, 'min': 1.0, 'max': 1000.0},
        'key_angle': {'type': 'float', 'default': 45.0, 'min': 0.0, 'max': 90.0},
        'distance': {'type': 'float', 'default': 5.0, 'min': 1.0, 'max': 20.0},
        'color_temperature': {'type': 'float', 'default': 5500.0, 'min': 1000.0, 'max': 12000.0}
    }
)
async def create_three_point_lighting(target_object: str = "", key_power: float = 100.0,
                                     fill_power: float = 30.0, rim_power: float = 80.0,
                                     key_angle: float = 45.0, distance: float = 5.0,
                                     color_temperature: float = 5500.0,
                                     _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create professional three-point lighting setup
    
    Features:
    - Key light (main illumination)
    - Fill light (shadow softening) 
    - Rim light (edge definition)
    - Color temperature control
    - Professional positioning
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create three-point lighting with {key_power}W key light",
            "complexity": 0.7
        }
    
    # Get target object center if specified
    target_location = [0, 0, 0]
    if target_object:
        operations.append(BlenderOperation(
            operation_type="get_object_location",
            target="object",
            parameters={"object_name": target_object}
        ))
    
    # Create key light (main light)
    key_location = [distance * 0.866, -distance * 0.5, distance * 0.866]  # 45° angle
    operations.append(BlenderOperation(
        operation_type="create_light",
        target="scene",
        parameters={
            "type": "AREA",
            "name": "Key_Light",
            "location": key_location,
            "energy": key_power,
            "color_temperature": color_temperature,
            "size": 2.0,
            "shape": "SQUARE"
        }
    ))
    
    # Point key light at target
    operations.append(BlenderOperation(
        operation_type="point_light_at",
        target="light",
        parameters={
            "light_name": "Key_Light",
            "target_location": target_location
        }
    ))
    
    # Create fill light (opposite side, lower power)
    fill_location = [-distance * 0.5, -distance * 0.866, distance * 0.5]
    operations.append(BlenderOperation(
        operation_type="create_light",
        target="scene",
        parameters={
            "type": "AREA",
            "name": "Fill_Light",
            "location": fill_location,
            "energy": fill_power,
            "color_temperature": color_temperature + 500,  # Slightly warmer
            "size": 3.0,
            "shape": "SQUARE"
        }
    ))
    
    # Point fill light at target
    operations.append(BlenderOperation(
        operation_type="point_light_at",
        target="light",
        parameters={
            "light_name": "Fill_Light",
            "target_location": target_location
        }
    ))
    
    # Create rim light (back light for edge definition)
    rim_location = [-distance * 0.5, distance * 0.866, distance * 1.2]
    operations.append(BlenderOperation(
        operation_type="create_light",
        target="scene",
        parameters={
            "type": "SPOT",
            "name": "Rim_Light",
            "location": rim_location,
            "energy": rim_power,
            "color_temperature": color_temperature - 500,  # Slightly cooler
            "spot_size": 60.0,
            "spot_blend": 0.2
        }
    ))
    
    # Point rim light at target
    operations.append(BlenderOperation(
        operation_type="point_light_at",
        target="light",
        parameters={
            "light_name": "Rim_Light",
            "target_location": target_location
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created three-point lighting setup with {key_power}W key light",
        "success": True
    }


@miktos_skill(
    name="create_softbox_lighting",
    category="lighting",
    description="Create professional softbox lighting with diffusion and barn doors",
    complexity=0.5,
    parameters={
        'name': {'type': 'string', 'default': 'Softbox'},
        'location': {'type': 'vector3', 'default': [3.0, -3.0, 2.0]},
        'rotation': {'type': 'vector3', 'default': [45.0, 0.0, 45.0]},
        'power': {'type': 'float', 'default': 150.0, 'min': 1.0, 'max': 1000.0},
        'size': {'type': 'float', 'default': 1.5, 'min': 0.1, 'max': 10.0},
        'color_temperature': {'type': 'float', 'default': 5600.0, 'min': 1000.0, 'max': 12000.0},
        'diffusion': {'type': 'float', 'default': 0.8, 'min': 0.0, 'max': 1.0}
    }
)
async def create_softbox_lighting(name: str = "Softbox", location: Optional[List[float]] = None,
                                 rotation: Optional[List[float]] = None, power: float = 150.0,
                                 size: float = 1.5, color_temperature: float = 5600.0,
                                 diffusion: float = 0.8,
                                 _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create professional softbox lighting setup
    
    Features:
    - Large area light for soft shadows
    - Color temperature control
    - Diffusion parameters
    - Professional positioning
    """
    
    if location is None:
        location = [3.0, -3.0, 2.0]
    if rotation is None:
        rotation = [45.0, 0.0, 45.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create {name} softbox with {power}W power",
            "complexity": 0.5
        }
    
    # Create area light (softbox)
    operations.append(BlenderOperation(
        operation_type="create_light",
        target="scene",
        parameters={
            "type": "AREA",
            "name": name,
            "location": location,
            "rotation": rotation,
            "energy": power,
            "color_temperature": color_temperature,
            "size": size,
            "shape": "RECTANGLE"
        }
    ))
    
    # Add light modifier for diffusion
    operations.append(BlenderOperation(
        operation_type="modify_light",
        target="light",
        parameters={
            "light_name": name,
            "spread": diffusion * 180.0,  # Convert to spread angle
            "use_custom_distance": True,
            "cutoff_distance": size * 10
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created {name} softbox with {power}W power and {size}m size",
        "success": True
    }


@miktos_skill(
    name="create_rim_lighting",
    category="lighting",
    description="Create dramatic rim lighting for edge definition and separation",
    complexity=0.4,
    parameters={
        'target_object': {'type': 'string', 'default': ''},
        'intensity': {'type': 'float', 'default': 50.0, 'min': 1.0, 'max': 500.0},
        'color': {'type': 'color', 'default': [1.0, 0.9, 0.8, 1.0]},
        'height_offset': {'type': 'float', 'default': 2.0, 'min': 0.0, 'max': 10.0},
        'distance': {'type': 'float', 'default': 4.0, 'min': 1.0, 'max': 20.0},
        'spot_size': {'type': 'float', 'default': 45.0, 'min': 10.0, 'max': 180.0}
    }
)
async def create_rim_lighting(target_object: str = "", intensity: float = 50.0,
                             color: Optional[List[float]] = None, height_offset: float = 2.0,
                             distance: float = 4.0, spot_size: float = 45.0,
                             _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create dramatic rim lighting for edge definition
    
    Features:
    - Automatic positioning behind target
    - Adjustable height and distance
    - Spot light with controlled spread
    - Color temperature options
    """
    
    if color is None:
        color = [1.0, 0.9, 0.8, 1.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Create rim lighting with {intensity}W intensity",
            "complexity": 0.4
        }
    
    # Calculate rim light position (behind and above target)
    rim_location = [0, distance, height_offset]
    if target_object:
        operations.append(BlenderOperation(
            operation_type="calculate_rim_position",
            target="object",
            parameters={
                "target_object": target_object,
                "distance": distance,
                "height_offset": height_offset
            }
        ))
    
    # Create rim light
    operations.append(BlenderOperation(
        operation_type="create_light",
        target="scene",
        parameters={
            "type": "SPOT",
            "name": "Rim_Light",
            "location": rim_location,
            "energy": intensity,
            "color": color[:3],  # RGB only
            "spot_size": spot_size,
            "spot_blend": 0.3,
            "use_custom_distance": True
        }
    ))
    
    # Point light at target if specified
    if target_object:
        operations.append(BlenderOperation(
            operation_type="point_light_at",
            target="light",
            parameters={
                "light_name": "Rim_Light",
                "target_object": target_object
            }
        ))
    
    return {
        "operations": operations,
        "message": f"Created rim lighting with {intensity}W intensity",
        "success": True
    }
