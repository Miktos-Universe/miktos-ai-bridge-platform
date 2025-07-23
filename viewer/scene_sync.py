"""
Scene Synchronization for Real-time Viewer

Handles synchronization of 3D scene data between Blender and the WebGL viewer.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SceneObject:
    """Represents a 3D object in the scene"""
    name: str
    object_type: str  # mesh, light, camera, etc.
    transform: Dict[str, List[float]]  # location, rotation, scale
    data: Dict[str, Any]  # mesh data, material data, etc.
    visible: bool = True
    selected: bool = False


@dataclass
class SceneState:
    """Complete state of the 3D scene"""
    objects: Dict[str, SceneObject]
    active_object: Optional[str] = None
    scene_name: str = "Scene"
    frame_current: int = 1
    frame_start: int = 1
    frame_end: int = 250
    timestamp: Optional[datetime] = None


@dataclass
class SceneChange:
    """Represents a change in the scene"""
    change_type: str  # "object_added", "object_modified", "object_deleted", "scene_cleared"
    object_name: Optional[str] = None
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class SceneSync:
    """
    Handles synchronization between Blender scene and real-time viewer.
    Tracks changes and provides efficient updates.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('SceneSync')
        
        # Scene state
        self.current_scene: Optional[SceneState] = None
        self.previous_scene: Optional[SceneState] = None
        
        # Change tracking
        self.change_history: List[SceneChange] = []
        self.max_history_size = config.get('max_history_size', 100)
        
        # Sync settings
        self.sync_interval = config.get('sync_interval', 0.1)  # 100ms
        self.auto_sync = config.get('auto_sync', True)
        self.track_materials = config.get('track_materials', True)
        self.track_animations = config.get('track_animations', True)
        
        # Callbacks
        self.change_callbacks: List[Callable[[SceneChange], None]] = []
        
        # Sync state
        self.is_syncing = False
        self.sync_task: Optional[asyncio.Task] = None
    
    async def start_sync(self):
        """Start automatic scene synchronization"""
        if self.is_syncing:
            return
        
        self.is_syncing = True
        self.sync_task = asyncio.create_task(self._sync_loop())
        self.logger.info("Scene synchronization started")
    
    async def stop_sync(self):
        """Stop automatic scene synchronization"""
        if not self.is_syncing:
            return
        
        self.is_syncing = False
        
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Scene synchronization stopped")
    
    async def _sync_loop(self):
        """Main synchronization loop"""
        while self.is_syncing:
            try:
                await self._perform_sync()
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
                await asyncio.sleep(1.0)  # Wait before retrying
    
    async def _perform_sync(self):
        """Perform a single synchronization cycle"""
        try:
            # Get current scene data (this would normally come from Blender)
            new_scene_data = await self._get_scene_data()
            
            if not new_scene_data:
                return
            
            # Create new scene state
            new_scene = self._create_scene_state(new_scene_data)
            
            # Compare with previous state and detect changes
            if self.current_scene:
                changes = self._detect_changes(self.current_scene, new_scene)
                
                # Process and notify about changes
                for change in changes:
                    await self._process_change(change)
            
            # Update scene state
            self.previous_scene = self.current_scene
            self.current_scene = new_scene
            
        except Exception as e:
            self.logger.error(f"Failed to perform sync: {e}")
    
    async def _get_scene_data(self) -> Optional[Dict[str, Any]]:
        """Get scene data from Blender (mock implementation)"""
        # In a real implementation, this would connect to Blender
        # For now, return None to indicate no data available
        return None
    
    def _create_scene_state(self, scene_data: Dict[str, Any]) -> SceneState:
        """Create a SceneState from raw scene data"""
        objects = {}
        
        # Process objects from scene data
        for obj_name, obj_data in scene_data.get('objects', {}).items():
            scene_obj = SceneObject(
                name=obj_name,
                object_type=obj_data.get('type', 'MESH'),
                transform={
                    'location': obj_data.get('location', [0, 0, 0]),
                    'rotation': obj_data.get('rotation', [0, 0, 0]),
                    'scale': obj_data.get('scale', [1, 1, 1])
                },
                data=obj_data.get('data', {}),
                visible=obj_data.get('visible', True),
                selected=obj_data.get('select', False)
            )
            objects[obj_name] = scene_obj
        
        return SceneState(
            objects=objects,
            active_object=scene_data.get('active_object'),
            scene_name=scene_data.get('scene_name', 'Scene'),
            frame_current=scene_data.get('frame_current', 1),
            frame_start=scene_data.get('frame_start', 1),
            frame_end=scene_data.get('frame_end', 250),
            timestamp=datetime.now()
        )
    
    def _detect_changes(self, old_scene: SceneState, new_scene: SceneState) -> List[SceneChange]:
        """Detect changes between two scene states"""
        changes = []
        
        # Check for new objects
        for obj_name, obj in new_scene.objects.items():
            if obj_name not in old_scene.objects:
                changes.append(SceneChange(
                    change_type="object_added",
                    object_name=obj_name,
                    new_data=self._object_to_dict(obj),
                    timestamp=datetime.now()
                ))
        
        # Check for deleted objects
        for obj_name in old_scene.objects:
            if obj_name not in new_scene.objects:
                changes.append(SceneChange(
                    change_type="object_deleted",
                    object_name=obj_name,
                    old_data=self._object_to_dict(old_scene.objects[obj_name]),
                    timestamp=datetime.now()
                ))
        
        # Check for modified objects
        for obj_name, new_obj in new_scene.objects.items():
            if obj_name in old_scene.objects:
                old_obj = old_scene.objects[obj_name]
                if self._objects_different(old_obj, new_obj):
                    changes.append(SceneChange(
                        change_type="object_modified",
                        object_name=obj_name,
                        old_data=self._object_to_dict(old_obj),
                        new_data=self._object_to_dict(new_obj),
                        timestamp=datetime.now()
                    ))
        
        return changes
    
    def _objects_different(self, obj1: SceneObject, obj2: SceneObject) -> bool:
        """Check if two objects are different"""
        # Compare key properties
        if obj1.object_type != obj2.object_type:
            return True
        
        if obj1.visible != obj2.visible:
            return True
        
        if obj1.selected != obj2.selected:
            return True
        
        # Compare transforms
        for key in ['location', 'rotation', 'scale']:
            if obj1.transform.get(key) != obj2.transform.get(key):
                return True
        
        # Compare data (simplified check)
        if obj1.data != obj2.data:
            return True
        
        return False
    
    def _object_to_dict(self, obj: SceneObject) -> Dict[str, Any]:
        """Convert SceneObject to dictionary"""
        return {
            'name': obj.name,
            'type': obj.object_type,
            'transform': obj.transform,
            'data': obj.data,
            'visible': obj.visible,
            'selected': obj.selected
        }
    
    async def _process_change(self, change: SceneChange):
        """Process a detected change"""
        # Add to history
        self.change_history.append(change)
        
        # Limit history size
        if len(self.change_history) > self.max_history_size:
            self.change_history.pop(0)
        
        # Notify callbacks
        for callback in self.change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change)
                else:
                    callback(change)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
        
        self.logger.debug(f"Processed change: {change.change_type} for {change.object_name}")
    
    def add_change_callback(self, callback: Callable[[SceneChange], None]):
        """Add a callback for scene changes"""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[SceneChange], None]):
        """Remove a change callback"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
    
    async def update_scene_from_blender(self, scene_data: Dict[str, Any]):
        """Manual scene update from Blender data"""
        try:
            new_scene = self._create_scene_state(scene_data)
            
            # Detect changes if we have a previous scene
            if self.current_scene:
                changes = self._detect_changes(self.current_scene, new_scene)
                for change in changes:
                    await self._process_change(change)
            
            # Update current scene
            self.previous_scene = self.current_scene
            self.current_scene = new_scene
            
            self.logger.info("Scene updated from Blender data")
            
        except Exception as e:
            self.logger.error(f"Failed to update scene from Blender: {e}")
    
    def get_current_scene(self) -> Optional[SceneState]:
        """Get the current scene state"""
        return self.current_scene
    
    def get_scene_summary(self) -> Dict[str, Any]:
        """Get a summary of the current scene"""
        if not self.current_scene:
            return {"objects": 0, "scene_name": "None", "status": "no_scene"}
        
        return {
            "objects": len(self.current_scene.objects),
            "scene_name": self.current_scene.scene_name,
            "active_object": self.current_scene.active_object,
            "frame_current": self.current_scene.frame_current,
            "last_update": self.current_scene.timestamp.isoformat() if self.current_scene.timestamp else None,
            "status": "active"
        }
    
    def get_object_data(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific object"""
        if self.current_scene and object_name in self.current_scene.objects:
            return self._object_to_dict(self.current_scene.objects[object_name])
        return None
    
    def get_recent_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scene changes"""
        recent = self.change_history[-limit:] if limit else self.change_history
        return [
            {
                'type': change.change_type,
                'object': change.object_name,
                'timestamp': change.timestamp.isoformat() if change.timestamp else None
            }
            for change in recent
        ]
    
    async def clear_scene(self):
        """Clear the current scene"""
        if self.current_scene:
            # Create a scene cleared change
            change = SceneChange(
                change_type="scene_cleared",
                timestamp=datetime.now()
            )
            
            await self._process_change(change)
            
            # Clear scene state
            self.previous_scene = self.current_scene
            self.current_scene = SceneState(
                objects={},
                timestamp=datetime.now()
            )
            
            self.logger.info("Scene cleared")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        return {
            "is_syncing": self.is_syncing,
            "sync_interval": self.sync_interval,
            "auto_sync": self.auto_sync,
            "change_history_size": len(self.change_history),
            "callbacks_registered": len(self.change_callbacks),
            "current_scene_objects": len(self.current_scene.objects) if self.current_scene else 0
        }


# Utility functions
def create_default_scene() -> SceneState:
    """Create a default empty scene"""
    return SceneState(
        objects={},
        scene_name="Default",
        timestamp=datetime.now()
    )


def scene_to_json(scene: SceneState) -> str:
    """Convert scene state to JSON string"""
    scene_dict = {
        'objects': {name: {
            'name': obj.name,
            'type': obj.object_type,
            'transform': obj.transform,
            'data': obj.data,
            'visible': obj.visible,
            'selected': obj.selected
        } for name, obj in scene.objects.items()},
        'active_object': scene.active_object,
        'scene_name': scene.scene_name,
        'frame_current': scene.frame_current,
        'frame_start': scene.frame_start,
        'frame_end': scene.frame_end,
        'timestamp': scene.timestamp.isoformat() if scene.timestamp else None
    }
    
    return json.dumps(scene_dict, indent=2)


def scene_from_json(json_str: str) -> SceneState:
    """Create scene state from JSON string"""
    data = json.loads(json_str)
    
    objects = {}
    for name, obj_data in data.get('objects', {}).items():
        objects[name] = SceneObject(
            name=obj_data['name'],
            object_type=obj_data['type'],
            transform=obj_data['transform'],
            data=obj_data['data'],
            visible=obj_data.get('visible', True),
            selected=obj_data.get('selected', False)
        )
    
    timestamp = None
    if data.get('timestamp'):
        timestamp = datetime.fromisoformat(data['timestamp'])
    
    return SceneState(
        objects=objects,
        active_object=data.get('active_object'),
        scene_name=data.get('scene_name', 'Scene'),
        frame_current=data.get('frame_current', 1),
        frame_start=data.get('frame_start', 1),
        frame_end=data.get('frame_end', 250),
        timestamp=timestamp or datetime.now()
    )


if __name__ == "__main__":
    # Test scene sync
    print("Scene sync module loaded successfully")
