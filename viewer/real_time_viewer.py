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
import http.server
import socketserver
import threading
from pathlib import Path

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
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.port = config.get('port', 8080)
        self.ws_port = config.get('ws_port', 8081)  # Separate WebSocket port
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
        
        # Connection management
        self.connected_clients = set()
        self.websocket_server = None
        self.http_server = None
        self.is_running = False
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_update = datetime.now()

    def _create_http_handler(self):
        """Create HTTP handler class with access to web directory"""
        web_dir = str(Path(__file__).parent / "web")
        
        class MiktosHTTPHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=web_dir, **kwargs)
            
            def do_GET(self):
                # Handle root path
                if self.path == '/':
                    self.path = '/index.html'
                return super().do_GET()
            
            def log_message(self, format, *args):
                # Suppress HTTP request logging
                pass
                
        return MiktosHTTPHandler

    async def start(self) -> bool:
        """Start the real-time viewer"""
        try:
            # Initialize renderer
            await self.webgl_renderer.initialize()
            
            # Start scene synchronization
            await self.scene_sync.start()
            
            # Start viewport manager
            await self.viewport_manager.start()
            
            # Start HTTP server for web interface
            await self._start_http_server()
            
            # Start WebSocket server for client communication
            await self._start_websocket_server()
            
            # Start update loop
            self.is_running = True
            asyncio.create_task(self._update_loop())
            
            self.viewer_state.is_active = True
            self.logger.info(f"Real-time viewer started on port {self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start real-time viewer: {e}")
            return False

    async def _start_http_server(self):
        """Start HTTP server for serving web interface"""
        def run_http_server():
            handler = self._create_http_handler()
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                self.logger.info(f"HTTP server serving on http://localhost:{self.port}")
                httpd.serve_forever()
        
        # Start HTTP server in a separate thread
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        self.logger.info(f"HTTP server thread started on port {self.port}")

    async def _start_websocket_server(self):
        """Start WebSocket server for real-time communication"""
        if websockets is None:
            self.logger.error("websockets package not available")
            return

        async def handle_client(websocket, path):
            """Handle WebSocket client connections"""
            self.connected_clients.add(websocket)
            self.logger.info(f"Client connected: {websocket.remote_address}")
            
            try:
                # Send initial scene state
                await self._send_scene_state(websocket)
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_client_message(websocket, data)
                    except json.JSONDecodeError:
                        self.logger.warning(f"Invalid JSON from client: {message}")
                    except Exception as e:
                        self.logger.error(f"Error handling client message: {e}")
                        
            except Exception as e:
                # Handle connection closed or other websocket errors
                self.logger.debug(f"Client handler error: {e}")
            finally:
                self.connected_clients.discard(websocket)
                self.logger.info(f"Client disconnected: {websocket.remote_address}")

        self.websocket_server = await websockets.serve(
            handle_client, "localhost", self.ws_port
        )
        self.logger.info(f"WebSocket server started on ws://localhost:{self.ws_port}")

    async def _send_scene_state(self, websocket):
        """Send current scene state to client"""
        scene_data = {
            "type": "scene_state",
            "objects": self.viewer_state.scene_objects,
            "camera": {
                "position": self.viewer_state.camera_position,
                "target": self.viewer_state.camera_target
            },
            "viewport": self.viewer_state.viewport_mode,
            "quality": self.viewer_state.render_quality,
            "fps": self.viewer_state.fps,
            "timestamp": self.viewer_state.last_update.isoformat()
        }
        
        try:
            await websocket.send(json.dumps(scene_data))
        except Exception as e:
            self.logger.error(f"Error sending scene state: {e}")

    async def _handle_client_message(self, websocket, data):
        """Handle messages from WebSocket clients"""
        message_type = data.get("type")
        
        if message_type == "get_scene_state":
            await self._send_scene_state(websocket)
        elif message_type == "reset_view":
            await self._reset_view()
        elif message_type == "set_quality":
            quality = data.get("quality", "high")
            await self._set_quality(quality)
        else:
            self.logger.warning(f"Unknown message type: {message_type}")

    async def _reset_view(self):
        """Reset camera view to default"""
        self.viewer_state.camera_position = [5, 5, 5]
        self.viewer_state.camera_target = [0, 0, 0]
        await self._broadcast_update({
            "type": "camera_reset",
            "position": self.viewer_state.camera_position,
            "target": self.viewer_state.camera_target
        })

    async def _set_quality(self, quality: str):
        """Set render quality"""
        self.viewer_state.render_quality = quality
        await self.webgl_renderer.set_render_quality(quality)
        await self._broadcast_update({
            "type": "quality_changed",
            "quality": quality
        })

    async def _broadcast_update(self, data):
        """Broadcast update to all connected clients"""
        if not self.connected_clients:
            return
            
        message = json.dumps(data)
        disconnected = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message)
            except Exception as e:
                # Handle connection closed or other websocket errors
                self.logger.debug(f"Client disconnected during broadcast: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected

    async def _update_loop(self):
        """Main update loop for the viewer"""
        while self.is_running:
            try:
                # Update frame count and FPS
                self.frame_count += 1
                now = datetime.now()
                
                if (now - self.last_fps_update).total_seconds() >= 1.0:
                    self.viewer_state.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_update = now
                
                # Update viewer state
                self.viewer_state.last_update = now
                
                # Check for recent scene changes
                recent_changes = self.scene_sync.get_recent_changes(limit=5)
                for change_dict in recent_changes:
                    # Convert change dict to ViewerUpdate format
                    update = ViewerUpdate(
                        update_type=change_dict.get('type', 'object_modified'),
                        object_data=change_dict.get('object_data'),
                        timestamp=datetime.fromisoformat(change_dict.get('timestamp', now.isoformat()))
                    )
                    await self._process_scene_update(update)
                
                # Sleep to maintain target FPS
                await asyncio.sleep(1.0 / self.fps_target)
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(1.0)

    async def _process_scene_update(self, update):
        """Process a scene update and broadcast to clients"""
        if update.update_type == "object_added":
            self.viewer_state.scene_objects.append(update.object_data)
        elif update.update_type == "object_modified":
            # Update existing object
            obj_id = update.object_data.get("id")
            for i, obj in enumerate(self.viewer_state.scene_objects):
                if obj.get("id") == obj_id:
                    self.viewer_state.scene_objects[i] = update.object_data
                    break
        elif update.update_type == "object_deleted":
            obj_id = update.object_data.get("id")
            self.viewer_state.scene_objects = [
                obj for obj in self.viewer_state.scene_objects 
                if obj.get("id") != obj_id
            ]
        elif update.update_type == "scene_cleared":
            self.viewer_state.scene_objects = []
        
        # Broadcast update to clients
        await self._broadcast_update({
            "type": "object_update",
            "update_type": update.update_type,
            "object_data": update.object_data,
            "timestamp": update.timestamp.isoformat() if update.timestamp else None
        })

    async def stop(self):
        """Stop the real-time viewer"""
        self.is_running = False
        self.viewer_state.is_active = False
        
        # Close WebSocket server
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        # Disconnect all clients
        for client in list(self.connected_clients):
            await client.close()
        self.connected_clients.clear()
        
        # Stop components
        await self.scene_sync.stop_sync()
        await self.viewport_manager.stop()
        await self.webgl_renderer.cleanup()
        
        self.logger.info("Real-time viewer stopped")

    async def add_object(self, object_data: Dict[str, Any]):
        """Add an object to the scene"""
        update = ViewerUpdate(
            update_type="object_added",
            object_data=object_data,
            timestamp=datetime.now()
        )
        await self._process_scene_update(update)

    async def modify_object(self, object_data: Dict[str, Any]):
        """Modify an existing object in the scene"""
        update = ViewerUpdate(
            update_type="object_modified",
            object_data=object_data,
            timestamp=datetime.now()
        )
        await self._process_scene_update(update)

    async def remove_object(self, object_id: str):
        """Remove an object from the scene"""
        update = ViewerUpdate(
            update_type="object_deleted",
            object_data={"id": object_id},
            timestamp=datetime.now()
        )
        await self._process_scene_update(update)

    async def clear_scene(self):
        """Clear all objects from the scene"""
        update = ViewerUpdate(
            update_type="scene_cleared",
            timestamp=datetime.now()
        )
        await self._process_scene_update(update)

    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot of the current view"""
        try:
            screenshot_data = await self.webgl_renderer.take_screenshot()
            if isinstance(screenshot_data, bytes):
                return base64.b64encode(screenshot_data).decode('utf-8')
            elif isinstance(screenshot_data, str):
                # Already encoded as string
                return screenshot_data
            else:
                # Convert to bytes first
                return base64.b64encode(str(screenshot_data).encode('utf-8')).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None

    async def get_scene_info(self) -> Dict[str, Any]:
        """Get current scene information"""
        return {
            "object_count": len(self.viewer_state.scene_objects),
            "fps": self.viewer_state.fps,
            "quality": self.viewer_state.render_quality,
            "viewport_mode": self.viewer_state.viewport_mode,
            "camera": {
                "position": self.viewer_state.camera_position,
                "target": self.viewer_state.camera_target
            },
            "last_update": self.viewer_state.last_update.isoformat(),
            "connected_clients": len(self.connected_clients)
        }

    def is_client_connected(self) -> bool:
        """Check if any clients are connected"""
        return len(self.connected_clients) > 0

    async def export_scene(self) -> Dict[str, Any]:
        """Export current scene data"""
        return {
            "viewer_state": {
                "is_active": self.viewer_state.is_active,
                "scene_objects": self.viewer_state.scene_objects,
                "camera_position": self.viewer_state.camera_position,
                "camera_target": self.viewer_state.camera_target,
                "viewport_mode": self.viewer_state.viewport_mode,
                "render_quality": self.viewer_state.render_quality,
                "fps": self.viewer_state.fps,
                "last_update": self.viewer_state.last_update.isoformat()
            },
            "performance": {
                "connected_clients": len(self.connected_clients),
                "target_fps": self.fps_target,
                "resolution": self.resolution
            }
        }

    async def update_scene(self, scene_data: Dict[str, Any]):
        """Update the scene with new data from Blender"""
        try:
            # Extract objects from scene data
            objects = scene_data.get('objects', [])
            
            # Update viewer state
            self.viewer_state.scene_objects = objects
            self.viewer_state.last_update = datetime.now()
            
            # Broadcast update to connected clients
            await self._broadcast_update({
                "type": "scene_update",
                "objects": objects,
                "timestamp": self.viewer_state.last_update.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error updating scene: {e}")

    async def get_viewer_state(self) -> Dict[str, Any]:
        """Get the current viewer state (alias for get_scene_info)"""
        return await self.get_scene_info()

    async def set_camera(self, position: List[float], target: List[float]):
        """Set the camera position and target"""
        try:
            self.viewer_state.camera_position = position
            self.viewer_state.camera_target = target
            
            # Broadcast camera update to clients
            await self._broadcast_update({
                "type": "camera_update", 
                "position": position,
                "target": target
            })
            
        except Exception as e:
            self.logger.error(f"Error setting camera: {e}")
