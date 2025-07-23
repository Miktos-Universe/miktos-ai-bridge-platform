"""
Real-time 3D Viewer for Miktos Platform

WebGL-based 3D viewer that provides live synchronization with Blender scenes
without requiring Blender to be open for preview.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import base64

try:
    import websockets  # type: ignore
except ImportError:
    websockets = None

from .scene_sync import SceneSync  # type: ignore
from .viewport_manager import ViewportManager  # type: ignore
from .webgl_renderer import WebGLRenderer  # type: ignore


@dataclass
class ViewerState:
    """Current state of the 3D viewer"""
    is_active: bool
    scene_objects: List[Dict[str, Any]]
    camera_position: List[float]
    camera_target: List[float]
    viewport_mode: str
    render_quality: str
    fps: float
    last_update: datetime


@dataclass
class ViewerUpdate:
    """Update data for the viewer"""
    update_type: str  # "object_added", "object_modified", "object_deleted", "scene_cleared"
    object_data: Optional[Dict[str, Any]] = None
    scene_state: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class RealTimeViewer:
    """
    Real-time 3D viewer that syncs with Blender operations
    Provides WebGL-based preview without requiring Blender to be open
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.port = config.get('port', 8080)
        self.resolution = config.get('resolution', [1920, 1080])
        self.fps_target = config.get('fps_target', 60)
        self.quality = config.get('quality', 'high')
        
        # Setup logging
        self.logger = logging.getLogger('RealTimeViewer')
        
        # Initialize components
        self.scene_sync = SceneSync(config.get('sync', {}))
        self.viewport_manager = ViewportManager(config.get('viewport', {}))
        self.webgl_renderer = WebGLRenderer(config.get('renderer', {}))
        
        # Viewer state
        self.viewer_state = ViewerState(
            is_active=False,
            scene_objects=[],
            camera_position=[5, 5, 5],
            camera_target=[0, 0, 0],
            viewport_mode='perspective',
            render_quality=self.quality,
            fps=0.0,
            last_update=datetime.now()
        )
        
        # Update queue
        self.update_queue = asyncio.Queue()
        self.is_running = False
        
        # WebSocket server for client communication
        self.websocket_server = None
        self.connected_clients = []
    
    async def start(self) -> bool:
        """Start the real-time viewer"""
        try:
            # Initialize renderer
            await self.webgl_renderer.initialize(self.resolution, self.quality)
            
            # Start scene synchronization
            await self.scene_sync.start()
            
            # Start viewport manager
            await self.viewport_manager.start()
            
            # Start WebSocket server for client communication
            await self._start_websocket_server()
            
            # Start update loop
            self.is_running = True
            asyncio.create_task(self._update_loop())
            
            self.viewer_state.is_active = True
            self.logger.info(f"Real-time viewer started on port {self.port}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start viewer: {e}")
            return False
    
    async def stop(self):
        """Stop the real-time viewer"""
        self.is_running = False
        self.viewer_state.is_active = False
        
        # Stop components
        await self.scene_sync.stop()
        await self.viewport_manager.stop()
        await self.webgl_renderer.cleanup()
        
        # Close WebSocket connections
        for client in self.connected_clients:
            await client.close()
        
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        self.logger.info("Real-time viewer stopped")
    
    async def update_scene(self, scene_state: Dict[str, Any]):
        """Update the viewer with new scene state"""
        update = ViewerUpdate(
            update_type="scene_update",
            scene_state=scene_state,
            timestamp=datetime.now()
        )
        
        await self.update_queue.put(update)
    
    async def add_object(self, object_data: Dict[str, Any]):
        """Add a new object to the viewer"""
        update = ViewerUpdate(
            update_type="object_added",
            object_data=object_data,
            timestamp=datetime.now()
        )
        
        await self.update_queue.put(update)
    
    async def modify_object(self, object_data: Dict[str, Any]):
        """Modify an existing object in the viewer"""
        update = ViewerUpdate(
            update_type="object_modified",
            object_data=object_data,
            timestamp=datetime.now()
        )
        
        await self.update_queue.put(update)
    
    async def delete_object(self, object_name: str):
        """Delete an object from the viewer"""
        update = ViewerUpdate(
            update_type="object_deleted",
            object_data={"name": object_name},
            timestamp=datetime.now()
        )
        
        await self.update_queue.put(update)
    
    async def clear_scene(self):
        """Clear all objects from the viewer"""
        update = ViewerUpdate(
            update_type="scene_cleared",
            timestamp=datetime.now()
        )
        
        await self.update_queue.put(update)
    
    async def set_camera(self, position: List[float], target: List[float]):
        """Set camera position and target"""
        self.viewer_state.camera_position = position
        self.viewer_state.camera_target = target
        
        # Update clients
        await self._broadcast_camera_update()
    
    async def set_viewport_mode(self, mode: str):
        """Set viewport mode (perspective, orthographic, etc.)"""
        if mode in ['perspective', 'orthographic', 'front', 'side', 'top']:
            self.viewer_state.viewport_mode = mode
            await self._broadcast_viewport_update()
    
    async def set_render_quality(self, quality: str):
        """Set render quality (low, medium, high, ultra)"""
        if quality in ['low', 'medium', 'high', 'ultra']:
            self.viewer_state.render_quality = quality
            await self.webgl_renderer.set_quality(quality)
            await self._broadcast_quality_update()
    
    async def take_screenshot(self) -> str:
        """Take a screenshot of the current view"""
        try:
            image_data = await self.webgl_renderer.capture_frame()
            
            # Convert to base64 for transmission
            screenshot_b64 = base64.b64encode(image_data).decode('utf-8')
            
            return screenshot_b64
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return ""
    
    async def get_viewer_state(self) -> Dict[str, Any]:
        """Get current viewer state"""
        return {
            "is_active": self.viewer_state.is_active,
            "object_count": len(self.viewer_state.scene_objects),
            "camera_position": self.viewer_state.camera_position,
            "camera_target": self.viewer_state.camera_target,
            "viewport_mode": self.viewer_state.viewport_mode,
            "render_quality": self.viewer_state.render_quality,
            "fps": self.viewer_state.fps,
            "last_update": self.viewer_state.last_update.isoformat(),
            "connected_clients": len(self.connected_clients)
        }
    
    async def _update_loop(self):
        """Main update loop for the viewer"""
        frame_time = 1.0 / self.fps_target
        last_frame_time = datetime.now()
        
        while self.is_running:
            try:
                current_time = datetime.now()
                delta_time = (current_time - last_frame_time).total_seconds()
                
                # Process queued updates
                await self._process_updates()
                
                # Update renderer if needed
                if delta_time >= frame_time:
                    await self._render_frame()
                    
                    # Calculate FPS
                    self.viewer_state.fps = 1.0 / delta_time if delta_time > 0 else 0
                    self.viewer_state.last_update = current_time
                    last_frame_time = current_time
                
                # Small sleep to prevent CPU hogging
                await asyncio.sleep(0.001)
                
            except Exception as e:
                self.logger.error(f"Update loop error: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_updates(self):
        """Process all queued updates"""
        while not self.update_queue.empty():
            try:
                update = await self.update_queue.get()
                await self._handle_update(update)
                
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self.logger.error(f"Update processing error: {e}")
    
    async def _handle_update(self, update: ViewerUpdate):
        """Handle a specific update"""
        if update.update_type == "scene_update" and update.scene_state is not None:
            await self._handle_scene_update(update.scene_state)
        elif update.update_type == "object_added" and update.object_data is not None:
            await self._handle_object_added(update.object_data)
        elif update.update_type == "object_modified" and update.object_data is not None:
            await self._handle_object_modified(update.object_data)
        elif update.update_type == "object_deleted" and update.object_data is not None:
            await self._handle_object_deleted(update.object_data)
        elif update.update_type == "scene_cleared":
            await self._handle_scene_cleared()
    
    async def _handle_scene_update(self, scene_state: Dict[str, Any]):
        """Handle full scene update"""
        if scene_state and 'objects' in scene_state:
            self.viewer_state.scene_objects = scene_state['objects']
            
            # Update renderer
            await self.webgl_renderer.update_scene(scene_state)
            
            # Broadcast to clients
            await self._broadcast_scene_update(scene_state)
    
    async def _handle_object_added(self, object_data: Dict[str, Any]):
        """Handle object addition"""
        if object_data:
            self.viewer_state.scene_objects.append(object_data)
            
            # Update renderer
            await self.webgl_renderer.add_object(object_data)
            
            # Broadcast to clients
            await self._broadcast_object_update("added", object_data)
    
    async def _handle_object_modified(self, object_data: Dict[str, Any]):
        """Handle object modification"""
        if object_data and 'name' in object_data:
            # Find and update object in scene
            for i, obj in enumerate(self.viewer_state.scene_objects):
                if obj.get('name') == object_data['name']:
                    self.viewer_state.scene_objects[i] = object_data
                    break
            
            # Update renderer
            await self.webgl_renderer.update_object(object_data)
            
            # Broadcast to clients
            await self._broadcast_object_update("modified", object_data)
    
    async def _handle_object_deleted(self, object_data: Dict[str, Any]):
        """Handle object deletion"""
        if object_data and 'name' in object_data:
            object_name = object_data['name']
            
            # Remove from scene objects
            self.viewer_state.scene_objects = [
                obj for obj in self.viewer_state.scene_objects 
                if obj.get('name') != object_name
            ]
            
            # Update renderer
            await self.webgl_renderer.remove_object(object_name)
            
            # Broadcast to clients
            await self._broadcast_object_update("deleted", object_data)
    
    async def _handle_scene_cleared(self):
        """Handle scene clearing"""
        self.viewer_state.scene_objects = []
        
        # Update renderer
        await self.webgl_renderer.clear_scene()
        
        # Broadcast to clients
        await self._broadcast_scene_cleared()
    
    async def _render_frame(self):
        """Render a single frame"""
        try:
            # Update camera
            await self.webgl_renderer.set_camera(
                self.viewer_state.camera_position,
                self.viewer_state.camera_target
            )
            
            # Render frame
            frame_data = await self.webgl_renderer.render_frame()
            
            # Broadcast frame to connected clients if needed
            if self.connected_clients and frame_data:
                await self._broadcast_frame(frame_data)
                
        except Exception as e:
            self.logger.error(f"Frame rendering error: {e}")
    
    async def _start_websocket_server(self):
        """Start WebSocket server for client communication"""
        if websockets is None:
            self.logger.error("websockets package not installed")
            return
        
        async def handle_client(websocket, path):
            """Handle WebSocket client connection"""
            self.connected_clients.append(websocket)
            self.logger.info(f"Client connected: {websocket.remote_address}")
            
            try:
                # Send initial state
                await websocket.send(json.dumps({
                    "type": "initial_state",
                    "data": await self.get_viewer_state()
                }))
                
                # Handle client messages
                async for message in websocket:
                    await self._handle_client_message(websocket, message)
                    
            except Exception as e:
                # Handle ConnectionClosed and other websocket exceptions
                if websockets and "ConnectionClosed" in str(type(e)):
                    pass
                else:
                    self.logger.error(f"Client handling error: {e}")
            finally:
                if websocket in self.connected_clients:
                    self.connected_clients.remove(websocket)
                self.logger.info(f"Client disconnected: {websocket.remote_address}")
        
        self.websocket_server = await websockets.serve(
            handle_client, 
            "localhost", 
            self.port
        )
    
    async def _handle_client_message(self, websocket, message: str):
        """Handle message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == "set_camera":
                position = data.get('position', [5, 5, 5])
                target = data.get('target', [0, 0, 0])
                await self.set_camera(position, target)
                
            elif message_type == "set_viewport_mode":
                mode = data.get('mode', 'perspective')
                await self.set_viewport_mode(mode)
                
            elif message_type == "set_quality":
                quality = data.get('quality', 'high')
                await self.set_render_quality(quality)
                
            elif message_type == "take_screenshot":
                screenshot = await self.take_screenshot()
                await websocket.send(json.dumps({
                    "type": "screenshot",
                    "data": screenshot
                }))
                
        except Exception as e:
            self.logger.error(f"Client message handling error: {e}")
    
    async def _broadcast_scene_update(self, scene_state: Dict[str, Any]):
        """Broadcast scene update to all clients"""
        message = json.dumps({
            "type": "scene_update",
            "data": scene_state
        })
        await self._broadcast_message(message)
    
    async def _broadcast_object_update(self, update_type: str, object_data: Dict[str, Any]):
        """Broadcast object update to all clients"""
        message = json.dumps({
            "type": "object_update",
            "update_type": update_type,
            "data": object_data
        })
        await self._broadcast_message(message)
    
    async def _broadcast_camera_update(self):
        """Broadcast camera update to all clients"""
        message = json.dumps({
            "type": "camera_update",
            "position": self.viewer_state.camera_position,
            "target": self.viewer_state.camera_target
        })
        await self._broadcast_message(message)
    
    async def _broadcast_viewport_update(self):
        """Broadcast viewport mode update to all clients"""
        message = json.dumps({
            "type": "viewport_update",
            "mode": self.viewer_state.viewport_mode
        })
        await self._broadcast_message(message)
    
    async def _broadcast_quality_update(self):
        """Broadcast quality update to all clients"""
        message = json.dumps({
            "type": "quality_update",
            "quality": self.viewer_state.render_quality
        })
        await self._broadcast_message(message)
    
    async def _broadcast_scene_cleared(self):
        """Broadcast scene cleared to all clients"""
        message = json.dumps({
            "type": "scene_cleared"
        })
        await self._broadcast_message(message)
    
    async def _broadcast_frame(self, frame_data: bytes):
        """Broadcast rendered frame to all clients"""
        frame_b64 = base64.b64encode(frame_data).decode('utf-8')
        message = json.dumps({
            "type": "frame_update",
            "data": frame_b64
        })
        await self._broadcast_message(message)
    
    async def _broadcast_message(self, message: str):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            # Send to all clients concurrently
            await asyncio.gather(
                *[client.send(message) for client in self.connected_clients],
                return_exceptions=True
            )


# Factory function
async def create_viewer(config: Dict[str, Any]) -> RealTimeViewer:
    """Create and start a real-time viewer"""
    viewer = RealTimeViewer(config)
    success = await viewer.start()
    
    if not success:
        raise RuntimeError("Failed to start real-time viewer")
    
    return viewer


if __name__ == "__main__":
    # Test the viewer
    async def test_viewer():
        config = {
            'port': 8080,
            'resolution': [1280, 720],
            'fps_target': 30,
            'quality': 'medium'
        }
        
        viewer = await create_viewer(config)
        
        # Simulate some updates
        await viewer.add_object({
            "name": "TestCube",
            "type": "MESH",
            "location": [0, 0, 0],
            "scale": [1, 1, 1],
            "rotation": [0, 0, 0]
        })
        
        await asyncio.sleep(2)
        
        await viewer.modify_object({
            "name": "TestCube",
            "type": "MESH", 
            "location": [2, 0, 0],
            "scale": [1.5, 1.5, 1.5],
            "rotation": [0, 0, 0]
        })
        
        await asyncio.sleep(5)
        await viewer.stop()
    
    asyncio.run(test_viewer())
