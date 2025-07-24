"""
Modifier Skills for Blender

Expert-level skills for applying and configuring mesh modifiers
"""

from typing import Dict, List, Any, Optional
from skills.skill_manager import miktos_skill  # type: ignore
from agent.blender_bridge import BlenderOperation  # type: ignore


@miktos_skill(
    name="apply_subdivision_surface",
    category="modeling",
    description="Apply subdivision surface modifier with intelligent settings",
    complexity=0.4,
    parameters={
        'levels_viewport': {'type': 'int', 'default': 2, 'min': 0, 'max': 6},
        'levels_render': {'type': 'int', 'default': 3, 'min': 0, 'max': 6},
        'use_creases': {'type': 'bool', 'default': True},
        'boundary_smooth': {'type': 'string', 'default': 'PRESERVE_CORNERS', 
                           'options': ['PRESERVE_CORNERS', 'ALL']},
        'apply_modifier': {'type': 'bool', 'default': False}
    }
)
async def apply_subdivision_surface(levels_viewport: int = 2, levels_render: int = 3,
                                  use_creases: bool = True, boundary_smooth: str = "PRESERVE_CORNERS",
                                  apply_modifier: bool = False,
                                  _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Apply subdivision surface with professional settings
    
    Features:
    - Separate viewport and render levels
    - Crease preservation
    - Boundary smoothing control
    - Optional modifier application
    """
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Apply subdivision surface with {levels_viewport} viewport levels",
            "complexity": 0.4
        }
    
    # Add subdivision surface modifier
    operations.append(BlenderOperation(
        operation_type="add_modifier",
        target="object",
        parameters={
            "type": "SUBSURF",
            "name": "SubSurf",
            "levels": levels_viewport,
            "render_levels": levels_render,
            "use_creases": use_creases,
            "boundary_smooth": boundary_smooth
        }
    ))
    
    # Apply modifier if requested
    if apply_modifier:
        operations.append(BlenderOperation(
            operation_type="apply_modifier",
            target="object",
            parameters={"modifier_name": "SubSurf"}
        ))
    
    return {
        "operations": operations,
        "message": f"Applied subdivision surface with {levels_viewport} viewport levels",
        "success": True
    }


@miktos_skill(
    name="apply_mirror_modifier",
    category="modeling",
    description="Apply mirror modifier with axis and object control",
    complexity=0.3,
    parameters={
        'use_axis': {'type': 'list', 'default': [True, False, False]},
        'use_bisect_axis': {'type': 'list', 'default': [True, False, False]},
        'use_bisect_flip_axis': {'type': 'list', 'default': [False, False, False]},
        'merge_threshold': {'type': 'float', 'default': 0.001, 'min': 0.0, 'max': 1.0},
        'mirror_object': {'type': 'string', 'default': ''},
        'apply_modifier': {'type': 'bool', 'default': False}
    }
)
async def apply_mirror_modifier(use_axis: Optional[List[bool]] = None, use_bisect_axis: Optional[List[bool]] = None,
                               use_bisect_flip_axis: Optional[List[bool]] = None, merge_threshold: float = 0.001,
                               mirror_object: str = "", apply_modifier: bool = False,
                               _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Apply mirror modifier with precise control
    
    Features:
    - Multi-axis mirroring
    - Bisection options
    - Merge threshold control
    - Custom mirror object support
    """
    
    if use_axis is None:
        use_axis = [True, False, False]
    if use_bisect_axis is None:
        use_bisect_axis = [True, False, False]
    if use_bisect_flip_axis is None:
        use_bisect_flip_axis = [False, False, False]
    
    operations = []
    
    if _planning_mode:
        axis_names = ['X', 'Y', 'Z']
        active_axes = [axis_names[i] for i, active in enumerate(use_axis) if active]
        return {
            "operations": operations,
            "message": f"Plan: Apply mirror modifier on {', '.join(active_axes)} axis/axes",
            "complexity": 0.3
        }
    
    # Add mirror modifier
    operations.append(BlenderOperation(
        operation_type="add_modifier",
        target="object",
        parameters={
            "type": "MIRROR",
            "name": "Mirror",
            "use_axis": use_axis,
            "use_bisect_axis": use_bisect_axis,
            "use_bisect_flip_axis": use_bisect_flip_axis,
            "merge_threshold": merge_threshold,
            "mirror_object": mirror_object if mirror_object else None
        }
    ))
    
    # Apply modifier if requested
    if apply_modifier:
        operations.append(BlenderOperation(
            operation_type="apply_modifier",
            target="object",
            parameters={"modifier_name": "Mirror"}
        ))
    
    axis_names = ['X', 'Y', 'Z']
    active_axes = [axis_names[i] for i, active in enumerate(use_axis) if active]
    
    return {
        "operations": operations,
        "message": f"Applied mirror modifier on {', '.join(active_axes)} axis/axes",
        "success": True
    }


@miktos_skill(
    name="apply_array_modifier",
    category="modeling",
    description="Apply array modifier with offset and object control",
    complexity=0.5,
    parameters={
        'count': {'type': 'int', 'default': 3, 'min': 2, 'max': 50},
        'relative_offset': {'type': 'vector3', 'default': [1.0, 0.0, 0.0]},
        'constant_offset': {'type': 'vector3', 'default': [0.0, 0.0, 0.0]},
        'use_merge_vertices': {'type': 'bool', 'default': True},
        'merge_threshold': {'type': 'float', 'default': 0.01, 'min': 0.0, 'max': 1.0},
        'offset_object': {'type': 'string', 'default': ''},
        'apply_modifier': {'type': 'bool', 'default': False}
    }
)
async def apply_array_modifier(count: int = 3, relative_offset: Optional[List[float]] = None,
                              constant_offset: Optional[List[float]] = None, use_merge_vertices: bool = True,
                              merge_threshold: float = 0.01, offset_object: str = "",
                              apply_modifier: bool = False,
                              _planning_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Apply array modifier with advanced offset control
    
    Features:
    - Count-based duplication
    - Relative and constant offsets
    - Vertex merging for seamless arrays
    - Custom offset object support
    """
    
    if relative_offset is None:
        relative_offset = [1.0, 0.0, 0.0]
    if constant_offset is None:
        constant_offset = [0.0, 0.0, 0.0]
    
    operations = []
    
    if _planning_mode:
        return {
            "operations": operations,
            "message": f"Plan: Apply array modifier with {count} copies",
            "complexity": 0.5
        }
    
    # Add array modifier
    operations.append(BlenderOperation(
        operation_type="add_modifier",
        target="object",
        parameters={
            "type": "ARRAY",
            "name": "Array",
            "count": count,
            "relative_offset_displace": relative_offset,
            "constant_offset_displace": constant_offset,
            "use_merge_vertices": use_merge_vertices,
            "merge_threshold": merge_threshold,
            "offset_object": offset_object if offset_object else None
        }
    ))
    
    # Apply modifier if requested
    if apply_modifier:
        operations.append(BlenderOperation(
            operation_type="apply_modifier",
            target="object",
            parameters={"modifier_name": "Array"}
        ))
    
    return {
        "operations": operations,
        "message": f"Applied array modifier with {count} copies",
        "success": True
    }
