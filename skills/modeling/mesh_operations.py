"""
Mesh Operations Skills for Blender

Expert-level skills for advanced mesh manipulation and editing
"""

from typing import Dict, List, Any, Optional
from skills.skill_manager import miktos_skill  # type: ignore
from agent.blender_bridge import BlenderOperation  # type: ignore


@miktos_skill(
    name="extrude_faces",
    category="modeling",
    description="Extrude selected faces with intelligent direction and scaling",
    complexity=0.4,
    parameters={
        'distance': {'type': 'float', 'default': 1.0, 'min': -10.0, 'max': 10.0},
        'scale': {'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 5.0},
        'direction': {'type': 'vector3', 'default': [0, 0, 1]},
        'individual_faces': {'type': 'bool', 'default': False}
    }
)
async def extrude_faces(distance: float = 1.0, scale: float = 1.0, 
                       direction: Optional[List[float]] = None,
                       individual_faces: bool = False,
                       _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Extrude faces with professional precision
    
    Features:
    - Smart direction detection (normal/custom)
    - Uniform or individual face extrusion
    - Automatic face cleanup
    - Scaling during extrusion
    """
    
    if direction is None:
        direction = [0, 0, 1]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Extrude faces {distance} units with {scale}x scaling",
            "complexity": 0.4
        }
    
    # Enter edit mode if needed
    operations.append(BlenderOperation(
        operation_type="mode_change",
        target="object",
        parameters={"mode": "EDIT"}
    ))
    
    # Extrude faces
    operations.append(BlenderOperation(
        operation_type="extrude",
        target="faces",
        parameters={
            "distance": distance,
            "scale": scale,
            "direction": direction,
            "individual": individual_faces
        }
    ))
    
    # Clean up geometry
    operations.append(BlenderOperation(
        operation_type="cleanup",
        target="mesh",
        parameters={"remove_doubles": True, "threshold": 0.001}
    ))
    
    return {
        "operations": operations,
        "message": f"Extruded faces {distance} units with {scale}x scaling",
        "success": True
    }


@miktos_skill(
    name="inset_faces",
    category="modeling",
    description="Inset faces with thickness and depth control",
    complexity=0.3,
    parameters={
        'thickness': {'type': 'float', 'default': 0.1, 'min': 0.001, 'max': 2.0},
        'depth': {'type': 'float', 'default': 0.0, 'min': -2.0, 'max': 2.0},
        'individual_faces': {'type': 'bool', 'default': True},
        'even_offset': {'type': 'bool', 'default': True}
    }
)
async def inset_faces(thickness: float = 0.1, depth: float = 0.0,
                     individual_faces: bool = True, even_offset: bool = True,
                     _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create face insets with professional control
    
    Features:
    - Even offset for uniform thickness
    - Individual or connected face insets
    - Depth control for advanced effects
    - Automatic boundary handling
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Inset faces with {thickness} thickness",
            "complexity": 0.3
        }
    
    # Enter edit mode
    operations.append(BlenderOperation(
        operation_type="mode_change",
        target="object",
        parameters={"mode": "EDIT"}
    ))
    
    # Inset faces
    operations.append(BlenderOperation(
        operation_type="inset",
        target="faces",
        parameters={
            "thickness": thickness,
            "depth": depth,
            "individual": individual_faces,
            "even_offset": even_offset
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Created face insets with {thickness} thickness and {depth} depth",
        "success": True
    }


@miktos_skill(
    name="loop_cut",
    category="modeling",
    description="Add edge loops with intelligent positioning and smoothing",
    complexity=0.5,
    parameters={
        'number_cuts': {'type': 'int', 'default': 1, 'min': 1, 'max': 20},
        'smoothness': {'type': 'float', 'default': 0.0, 'min': -1.0, 'max': 1.0},
        'falloff': {'type': 'string', 'default': 'SMOOTH', 'options': ['SMOOTH', 'SPHERE', 'ROOT', 'INVERSE_SQUARE']},
        'even_offset': {'type': 'bool', 'default': True}
    }
)
async def loop_cut(number_cuts: int = 1, smoothness: float = 0.0,
                  falloff: str = "SMOOTH", even_offset: bool = True,
                  _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Add edge loops with advanced positioning control
    
    Features:
    - Multiple cuts with even distribution
    - Smoothness factor for curved surfaces
    - Falloff patterns for natural flow
    - Edge flow preservation
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Add {number_cuts} edge loops with {smoothness} smoothness",
            "complexity": 0.5
        }
    
    # Enter edit mode
    operations.append(BlenderOperation(
        operation_type="mode_change",
        target="object",
        parameters={"mode": "EDIT"}
    ))
    
    # Add loop cuts
    operations.append(BlenderOperation(
        operation_type="loop_cut",
        target="mesh",
        parameters={
            "number_cuts": number_cuts,
            "smoothness": smoothness,
            "falloff": falloff,
            "even_offset": even_offset
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Added {number_cuts} edge loops with {smoothness} smoothness",
        "success": True
    }


@miktos_skill(
    name="bevel_edges",
    category="modeling",
    description="Bevel edges with advanced profile and segment control",
    complexity=0.6,
    parameters={
        'amount': {'type': 'float', 'default': 0.1, 'min': 0.001, 'max': 5.0},
        'segments': {'type': 'int', 'default': 2, 'min': 1, 'max': 20},
        'profile': {'type': 'float', 'default': 0.5, 'min': 0.0, 'max': 1.0},
        'clamp_overlap': {'type': 'bool', 'default': True},
        'loop_slide': {'type': 'bool', 'default': True}
    }
)
async def bevel_edges(amount: float = 0.1, segments: int = 2, profile: float = 0.5,
                     clamp_overlap: bool = True, loop_slide: bool = True,
                     _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Create professional bevels with advanced control
    
    Features:
    - Profile control for convex/concave bevels
    - Segment control for smooth curves
    - Overlap clamping for clean geometry
    - Loop slide for natural edge flow
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Bevel edges with {amount} amount and {segments} segments",
            "complexity": 0.6
        }
    
    # Enter edit mode
    operations.append(BlenderOperation(
        operation_type="mode_change",
        target="object",
        parameters={"mode": "EDIT"}
    ))
    
    # Bevel edges
    operations.append(BlenderOperation(
        operation_type="bevel",
        target="edges",
        parameters={
            "amount": amount,
            "segments": segments,
            "profile": profile,
            "clamp_overlap": clamp_overlap,
            "loop_slide": loop_slide
        }
    ))
    
    return {
        "operations": operations,
        "message": f"Applied bevel with {amount} amount and {segments} segments",
        "success": True
    }
