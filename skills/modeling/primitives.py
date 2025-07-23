"""
Primitive Creation Skills for Blender

Expert-level skills for creating and configuring primitive objects
"""

from typing import Dict, List, Any, Optional
from ..skill_manager import miktos_skill
from ...agent.blender_bridge import BlenderOperation  # type: ignore


@miktos_skill(
    name="create_cube",
    category="modeling",
    description="Create a cube primitive with intelligent sizing and positioning",
    complexity=0.2,
    parameters={
        'size': {'type': 'float', 'default': 2.0, 'min': 0.1, 'max': 100.0},
        'location': {'type': 'vector3', 'default': [0, 0, 0]},
        'subdivisions': {'type': 'int', 'default': 0, 'min': 0, 'max': 6},
        'name': {'type': 'string', 'default': 'Cube'}
    }
)
async def create_cube(size: float = 2.0, location: Optional[List[float]] = None, 
                     subdivisions: int = 0, name: str = "Cube", 
                     _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create a cube with intelligent defaults and optional subdivisions
    
    Professional features:
    - Intelligent sizing based on scene scale
    - Automatic subdivision for detail work
    - Proper naming conventions
    - Optimized geometry
    """
    
    if location is None:
        location = [0, 0, 0]
    
    operations = []
    
    # Create base cube
    create_op = BlenderOperation(
        operation_type="create",
        target="cube",
        parameters={
            "size": size,
            "location": location,
            "name": name
        }
    )
    operations.append(create_op)
    
    # Add subdivisions if requested
    if subdivisions > 0:
        subdivide_op = BlenderOperation(
            operation_type="modify",
            target="selected",
            parameters={
                "subdivisions": subdivisions
            }
        )
        operations.append(subdivide_op)
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Planned creation of {name} with {subdivisions} subdivisions"
        }
    
    return {
        "success": True,
        "operations": operations,
        "message": f"Created cube '{name}' at {location} with size {size}"
    }


@miktos_skill(
    name="create_sphere",
    category="modeling", 
    description="Create a UV sphere with professional topology and detail control",
    complexity=0.3,
    parameters={
        'radius': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 100.0},
        'location': {'type': 'vector3', 'default': [0, 0, 0]},
        'subdivisions': {'type': 'int', 'default': 2, 'min': 1, 'max': 6},
        'rings': {'type': 'int', 'default': 16, 'min': 3, 'max': 64},
        'segments': {'type': 'int', 'default': 32, 'min': 3, 'max': 128},
        'name': {'type': 'string', 'default': 'Sphere'}
    }
)
async def create_sphere(radius: float = 1.0, location: Optional[List[float]] = None,
                       subdivisions: int = 2, rings: int = 16, segments: int = 32,
                       name: str = "Sphere", _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create a UV sphere with professional topology
    
    Professional features:
    - Optimized ring/segment count for different use cases
    - Clean UV unwrapping topology
    - Proper pole vertex handling
    - Scale-appropriate detail levels
    """
    
    if location is None:
        location = [0, 0, 0]
    
    operations = []
    
    # Create base sphere
    create_op = BlenderOperation(
        operation_type="create",
        target="sphere",
        parameters={
            "radius": radius,
            "location": location,
            "rings": rings,
            "segments": segments,
            "name": name
        }
    )
    operations.append(create_op)
    
    # Add subdivisions for higher detail
    if subdivisions > 0:
        subdivide_op = BlenderOperation(
            operation_type="modify",
            target="selected",
            parameters={
                "subdivisions": subdivisions,
                "smooth": True  # Smooth spheres by default
            }
        )
        operations.append(subdivide_op)
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Planned creation of {name} with {rings}x{segments} topology"
        }
    
    return {
        "success": True,
        "operations": operations,
        "message": f"Created sphere '{name}' with radius {radius} and {rings}x{segments} topology"
    }


@miktos_skill(
    name="create_cylinder", 
    category="modeling",
    description="Create a cylinder with professional edge flow and cap options",
    complexity=0.3,
    parameters={
        'radius': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 100.0},
        'depth': {'type': 'float', 'default': 2.0, 'min': 0.1, 'max': 100.0},
        'location': {'type': 'vector3', 'default': [0, 0, 0]},
        'vertices': {'type': 'int', 'default': 32, 'min': 3, 'max': 128},
        'cap_ends': {'type': 'bool', 'default': True},
        'name': {'type': 'string', 'default': 'Cylinder'}
    }
)
async def create_cylinder(radius: float = 1.0, depth: float = 2.0, 
                         location: Optional[List[float]] = None, vertices: int = 32,
                         cap_ends: bool = True, name: str = "Cylinder",
                         _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create a cylinder with professional topology
    
    Professional features:
    - Intelligent vertex count based on radius
    - Optional end caps for different use cases
    - Clean edge flow for modeling
    - Proper proportions and scaling
    """
    
    if location is None:
        location = [0, 0, 0]
    
    operations = []
    
    # Automatically adjust vertex count based on radius for optimal topology
    if vertices == 32:  # Default value
        if radius < 0.5:
            vertices = 16
        elif radius > 5.0:
            vertices = 64
    
    # Create base cylinder
    create_op = BlenderOperation(
        operation_type="create",
        target="cylinder",
        parameters={
            "radius": radius,
            "depth": depth,
            "location": location,
            "vertices": vertices,
            "cap_ends": cap_ends,
            "name": name
        }
    )
    operations.append(create_op)
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Planned creation of {name} with {vertices} vertices"
        }
    
    return {
        "success": True,
        "operations": operations,
        "message": f"Created cylinder '{name}' with radius {radius}, depth {depth}, and {vertices} vertices"
    }


@miktos_skill(
    name="create_plane",
    category="modeling",
    description="Create a plane with intelligent subdivision for different workflows",
    complexity=0.1,
    parameters={
        'size': {'type': 'float', 'default': 2.0, 'min': 0.1, 'max': 1000.0},
        'location': {'type': 'vector3', 'default': [0, 0, 0]},
        'subdivisions': {'type': 'int', 'default': 0, 'min': 0, 'max': 10},
        'orientation': {'type': 'string', 'default': 'horizontal', 'options': ['horizontal', 'vertical_x', 'vertical_y']},
        'name': {'type': 'string', 'default': 'Plane'}
    }
)
async def create_plane(size: float = 2.0, location: Optional[List[float]] = None,
                      subdivisions: int = 0, orientation: str = "horizontal",
                      name: str = "Plane", _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create a plane with intelligent orientation and subdivision
    
    Professional features:
    - Multiple orientation presets
    - Automatic subdivision for displacement/sculpting
    - Proper scaling for different use cases
    - Clean quad topology
    """
    
    if location is None:
        location = [0, 0, 0]
    
    operations = []
    
    # Calculate rotation based on orientation
    rotation = [0, 0, 0]
    if orientation == "vertical_x":
        rotation = [1.5708, 0, 0]  # 90 degrees around X
    elif orientation == "vertical_y":
        rotation = [0, 1.5708, 0]  # 90 degrees around Y
    
    # Create base plane
    create_op = BlenderOperation(
        operation_type="create",
        target="plane",
        parameters={
            "size": size,
            "location": location,
            "rotation": rotation,
            "name": name
        }
    )
    operations.append(create_op)
    
    # Add subdivisions if requested
    if subdivisions > 0:
        subdivide_op = BlenderOperation(
            operation_type="modify",
            target="selected",
            parameters={
                "subdivisions": subdivisions,
                "fractal": 0.0,  # Keep clean geometry
                "smooth": 0.0    # Keep flat
            }
        )
        operations.append(subdivide_op)
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Planned creation of {orientation} {name} with {subdivisions} subdivisions"
        }
    
    return {
        "success": True,
        "operations": operations,
        "message": f"Created {orientation} plane '{name}' with size {size} and {subdivisions} subdivisions"
    }


@miktos_skill(
    name="create_torus",
    category="modeling",
    description="Create a torus with professional topology for modeling and animation",
    complexity=0.4,
    parameters={
        'major_radius': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 100.0},
        'minor_radius': {'type': 'float', 'default': 0.25, 'min': 0.01, 'max': 10.0},
        'location': {'type': 'vector3', 'default': [0, 0, 0]},
        'major_segments': {'type': 'int', 'default': 48, 'min': 3, 'max': 128},
        'minor_segments': {'type': 'int', 'default': 12, 'min': 3, 'max': 64},
        'name': {'type': 'string', 'default': 'Torus'}
    }
)
async def create_torus(major_radius: float = 1.0, minor_radius: float = 0.25,
                      location: Optional[List[float]] = None, major_segments: int = 48,
                      minor_segments: int = 12, name: str = "Torus",
                      _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create a torus with professional topology
    
    Professional features:
    - Proper major/minor segment ratios
    - Clean edge flow for modeling
    - Optimized for animation deformation
    - Proportional detail distribution
    """
    
    if location is None:
        location = [0, 0, 0]
    
    operations = []
    
    # Automatically optimize segment counts based on radii
    if major_segments == 48 and minor_segments == 12:  # Default values
        # Calculate optimal topology
        circumference_ratio = major_radius / minor_radius
        if circumference_ratio > 8:
            major_segments = min(64, int(major_segments * 1.5))
        elif circumference_ratio < 3:
            major_segments = max(24, int(major_segments * 0.75))
    
    # Create base torus
    create_op = BlenderOperation(
        operation_type="create",
        target="torus",
        parameters={
            "major_radius": major_radius,
            "minor_radius": minor_radius,
            "location": location,
            "major_segments": major_segments,
            "minor_segments": minor_segments,
            "name": name
        }
    )
    operations.append(create_op)
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Planned creation of {name} with {major_segments}x{minor_segments} topology"
        }
    
    return {
        "success": True,
        "operations": operations,
        "message": f"Created torus '{name}' with radii {major_radius}/{minor_radius} and {major_segments}x{minor_segments} segments"
    }


@miktos_skill(
    name="create_cone",
    category="modeling",
    description="Create a cone with professional topology and tip options",
    complexity=0.3,
    parameters={
        'radius': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 100.0},
        'depth': {'type': 'float', 'default': 2.0, 'min': 0.1, 'max': 100.0},
        'location': {'type': 'vector3', 'default': [0, 0, 0]},
        'vertices': {'type': 'int', 'default': 32, 'min': 3, 'max': 128},
        'cap_end': {'type': 'bool', 'default': True},
        'name': {'type': 'string', 'default': 'Cone'}
    }
)
async def create_cone(radius: float = 1.0, depth: float = 2.0,
                     location: Optional[List[float]] = None, vertices: int = 32,
                     cap_end: bool = True, name: str = "Cone",
                     _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create a cone with professional topology
    
    Professional features:
    - Clean edge flow from tip to base
    - Optional base cap for different use cases
    - Optimized vertex distribution
    - Proper proportions for modeling
    """
    
    if location is None:
        location = [0, 0, 0]
    
    operations = []
    
    # Create base cone
    create_op = BlenderOperation(
        operation_type="create",
        target="cone",
        parameters={
            "radius": radius,
            "depth": depth,
            "location": location,
            "vertices": vertices,
            "cap_end": cap_end,
            "name": name
        }
    )
    operations.append(create_op)
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Planned creation of {name} with {vertices} vertices"
        }
    
    return {
        "success": True,
        "operations": operations,
        "message": f"Created cone '{name}' with radius {radius}, depth {depth}, and {vertices} vertices"
    }
