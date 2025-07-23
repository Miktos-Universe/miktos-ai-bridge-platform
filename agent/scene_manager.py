"""
Scene Manager for Miktos AI Bridge Platform

Manages 3D scene state synchronization between Blender and the platform.
Handles object tracking, scene diff detection, and state consistency.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class SceneObject:
    """Represents a 3D object in the scene."""
    name: str
    object_type: str
    location: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    material: Optional[str] = None
    visible: bool = True
    selected: bool = False
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    last_modified: datetime = field(default_factory=datetime.now)


@dataclass
class SceneState:
    """Complete state of the 3D scene."""
    objects: Dict[str, SceneObject] = field(default_factory=dict)
    active_object: Optional[str] = None
    selected_objects: List[str] = field(default_factory=list)
    viewport_settings: Dict[str, Any] = field(default_factory=dict)
    render_settings: Dict[str, Any] = field(default_factory=dict)
    frame_current: int = 1
    frame_start: int = 1
    frame_end: int = 250
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SceneDiff:
    """Represents changes between two scene states."""
    added_objects: List[str] = field(default_factory=list)
    removed_objects: List[str] = field(default_factory=list)
    modified_objects: List[str] = field(default_factory=list)
    selection_changed: bool = False
    active_object_changed: bool = False
    viewport_changed: bool = False
    render_settings_changed: bool = False


class SceneManager:
    """
    Manages 3D scene state and synchronization.
    
    Responsibilities:
    - Track scene object changes
    - Detect modifications and generate diffs
    - Maintain scene state consistency
    - Optimize update notifications
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('SceneManager')
        
        # Scene state tracking
        self.current_state = SceneState()
        self.previous_state = SceneState()
        self.state_history: List[SceneState] = []
        
        # Change tracking
        self.tracked_objects: Set[str] = set()
        self.change_callbacks: List[Callable] = []
        self.auto_sync_enabled = self.config.get('auto_sync', True)
        self.max_history_size = self.config.get('max_history_size', 100)
        
        # Performance settings
        self.update_throttle = self.config.get('update_throttle_ms', 100)
        self.last_update_time = datetime.now()
        
    async def update_scene_state(self, scene_data: Dict[str, Any]) -> SceneDiff:
        """
        Update scene state from Blender data and return differences.
        
        Args:
            scene_data: Raw scene data from Blender
            
        Returns:
            SceneDiff: Changes detected since last update
        """
        try:
            # Store previous state
            self.previous_state = self._deep_copy_state(self.current_state)
            
            # Parse new scene state
            new_state = self._parse_scene_data(scene_data)
            
            # Generate diff
            diff = self._calculate_diff(self.current_state, new_state)
            
            # Update current state
            self.current_state = new_state
            
            # Add to history
            self._add_to_history(new_state)
            
            # Notify callbacks if there are changes
            if self._has_significant_changes(diff):
                await self._notify_change_callbacks(diff)
            
            self.logger.debug(f"Scene updated: {len(diff.added_objects)} added, "
                            f"{len(diff.removed_objects)} removed, "
                            f"{len(diff.modified_objects)} modified")
            
            return diff
            
        except Exception as e:
            self.logger.error(f"Failed to update scene state: {e}")
            return SceneDiff()
    
    def _parse_scene_data(self, scene_data: Dict[str, Any]) -> SceneState:
        """Parse raw Blender scene data into SceneState."""
        state = SceneState()
        
        # Parse objects
        objects_data = scene_data.get('objects', [])
        for obj_data in objects_data:
            obj = SceneObject(
                name=obj_data.get('name', ''),
                object_type=obj_data.get('type', 'UNKNOWN'),
                location=obj_data.get('location', [0.0, 0.0, 0.0]),
                rotation=obj_data.get('rotation_euler', [0.0, 0.0, 0.0]),
                scale=obj_data.get('scale', [1.0, 1.0, 1.0]),
                visible=obj_data.get('visible', True),
                selected=obj_data.get('select_get', False),
                parent=obj_data.get('parent', {}).get('name') if obj_data.get('parent') else None
            )
            
            # Parse material
            if obj_data.get('material_slots'):
                materials = [slot.get('material', {}).get('name') 
                           for slot in obj_data['material_slots'] 
                           if slot.get('material')]
                if materials:
                    obj.material = materials[0]  # Use first material
            
            state.objects[obj.name] = obj
        
        # Parse selection and active object
        state.selected_objects = [obj.name for obj in state.objects.values() if obj.selected]
        state.active_object = scene_data.get('active_object', {}).get('name')
        
        # Parse frame settings
        state.frame_current = scene_data.get('frame_current', 1)
        state.frame_start = scene_data.get('frame_start', 1)
        state.frame_end = scene_data.get('frame_end', 250)
        
        # Parse viewport settings
        state.viewport_settings = scene_data.get('viewport', {})
        state.render_settings = scene_data.get('render', {})
        
        state.timestamp = datetime.now()
        return state
    
    def _calculate_diff(self, old_state: SceneState, new_state: SceneState) -> SceneDiff:
        """Calculate differences between two scene states."""
        diff = SceneDiff()
        
        old_objects = set(old_state.objects.keys())
        new_objects = set(new_state.objects.keys())
        
        # Object additions and removals
        diff.added_objects = list(new_objects - old_objects)
        diff.removed_objects = list(old_objects - new_objects)
        
        # Modified objects
        common_objects = old_objects & new_objects
        for obj_name in common_objects:
            if self._object_changed(old_state.objects[obj_name], 
                                  new_state.objects[obj_name]):
                diff.modified_objects.append(obj_name)
        
        # Selection changes
        diff.selection_changed = (
            set(old_state.selected_objects) != set(new_state.selected_objects)
        )
        
        # Active object changes
        diff.active_object_changed = (
            old_state.active_object != new_state.active_object
        )
        
        # Viewport and render setting changes
        diff.viewport_changed = (
            old_state.viewport_settings != new_state.viewport_settings
        )
        diff.render_settings_changed = (
            old_state.render_settings != new_state.render_settings
        )
        
        return diff
    
    def _object_changed(self, old_obj: SceneObject, new_obj: SceneObject) -> bool:
        """Check if an object has changed significantly."""
        # Check key properties for changes
        tolerance = 1e-6
        
        # Location changes
        if not self._vectors_equal(old_obj.location, new_obj.location, tolerance):
            return True
        
        # Rotation changes
        if not self._vectors_equal(old_obj.rotation, new_obj.rotation, tolerance):
            return True
        
        # Scale changes
        if not self._vectors_equal(old_obj.scale, new_obj.scale, tolerance):
            return True
        
        # Material changes
        if old_obj.material != new_obj.material:
            return True
        
        # Visibility changes
        if old_obj.visible != new_obj.visible:
            return True
        
        # Parent changes
        if old_obj.parent != new_obj.parent:
            return True
        
        return False
    
    def _vectors_equal(self, vec1: List[float], vec2: List[float], tolerance: float) -> bool:
        """Check if two vectors are equal within tolerance."""
        if len(vec1) != len(vec2):
            return False
        
        return all(abs(a - b) < tolerance for a, b in zip(vec1, vec2))
    
    def _has_significant_changes(self, diff: SceneDiff) -> bool:
        """Check if diff contains significant changes worth notifying about."""
        return (
            len(diff.added_objects) > 0 or
            len(diff.removed_objects) > 0 or
            len(diff.modified_objects) > 0 or
            diff.selection_changed or
            diff.active_object_changed
        )
    
    async def _notify_change_callbacks(self, diff: SceneDiff):
        """Notify registered callbacks about scene changes."""
        for callback in self.change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(diff)
                else:
                    callback(diff)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
    
    def _add_to_history(self, state: SceneState):
        """Add state to history with size limit."""
        self.state_history.append(self._deep_copy_state(state))
        
        # Maintain history size limit
        while len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)
    
    def _deep_copy_state(self, state: SceneState) -> SceneState:
        """Create a deep copy of scene state."""
        import copy
        return copy.deepcopy(state)
    
    def register_change_callback(self, callback: Callable):
        """Register a callback for scene changes."""
        self.change_callbacks.append(callback)
    
    def unregister_change_callback(self, callback: Callable):
        """Unregister a scene change callback."""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
    
    def get_object(self, name: str) -> Optional[SceneObject]:
        """Get object by name."""
        return self.current_state.objects.get(name)
    
    def get_selected_objects(self) -> List[SceneObject]:
        """Get currently selected objects."""
        return [self.current_state.objects[name] 
                for name in self.current_state.selected_objects 
                if name in self.current_state.objects]
    
    def get_active_object(self) -> Optional[SceneObject]:
        """Get the active object."""
        if self.current_state.active_object:
            return self.current_state.objects.get(self.current_state.active_object)
        return None
    
    def get_objects_by_type(self, object_type: str) -> List[SceneObject]:
        """Get all objects of a specific type."""
        return [obj for obj in self.current_state.objects.values() 
                if obj.object_type == object_type]
    
    def get_scene_summary(self) -> Dict[str, Any]:
        """Get a summary of the current scene."""
        objects_by_type = {}
        for obj in self.current_state.objects.values():
            obj_type = obj.object_type
            if obj_type not in objects_by_type:
                objects_by_type[obj_type] = 0
            objects_by_type[obj_type] += 1
        
        return {
            'total_objects': len(self.current_state.objects),
            'objects_by_type': objects_by_type,
            'selected_count': len(self.current_state.selected_objects),
            'active_object': self.current_state.active_object,
            'frame_current': self.current_state.frame_current,
            'last_update': self.current_state.timestamp.isoformat()
        }
    
    def export_scene_state(self) -> Dict[str, Any]:
        """Export current scene state to dict."""
        return {
            'objects': {
                name: {
                    'name': obj.name,
                    'type': obj.object_type,
                    'location': obj.location,
                    'rotation': obj.rotation,
                    'scale': obj.scale,
                    'material': obj.material,
                    'visible': obj.visible,
                    'selected': obj.selected,
                    'parent': obj.parent,
                    'children': obj.children
                }
                for name, obj in self.current_state.objects.items()
            },
            'active_object': self.current_state.active_object,
            'selected_objects': self.current_state.selected_objects,
            'frame_current': self.current_state.frame_current,
            'timestamp': self.current_state.timestamp.isoformat()
        }
    
    def clear_history(self):
        """Clear scene state history."""
        self.state_history.clear()
        self.logger.debug("Scene history cleared")
    
    def reset_state(self):
        """Reset scene state to empty."""
        self.current_state = SceneState()
        self.previous_state = SceneState()
        self.clear_history()
        self.logger.debug("Scene state reset")
