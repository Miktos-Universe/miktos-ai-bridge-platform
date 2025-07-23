"""
Viewport Manager for Miktos AI Bridge Platform

Manages multiple 3D viewports, camera controls, and view configurations.
Handles viewport layout, navigation, and visual settings.
"""

import asyncio
import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ViewportMode(Enum):
    """Viewport display modes."""
    SOLID = "solid"
    WIREFRAME = "wireframe"
    MATERIAL = "material"
    RENDERED = "rendered"


class ProjectionType(Enum):
    """Camera projection types."""
    PERSPECTIVE = "perspective"
    ORTHOGRAPHIC = "orthographic"


@dataclass
class ViewportSettings:
    """Settings for a single viewport."""
    name: str
    mode: ViewportMode = ViewportMode.SOLID
    projection: ProjectionType = ProjectionType.PERSPECTIVE
    show_grid: bool = True
    show_axes: bool = True
    show_gizmos: bool = True
    background_color: List[float] = field(default_factory=lambda: [0.2, 0.2, 0.2, 1.0])
    grid_size: float = 1.0
    grid_subdivisions: int = 10


@dataclass
class CameraController:
    """Camera controller for viewport navigation."""
    position: List[float] = field(default_factory=lambda: [7.5, -7.5, 5.5])
    target: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    up: List[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    distance: float = 13.0
    zoom_speed: float = 1.2
    pan_speed: float = 0.01
    orbit_speed: float = 0.005
    min_distance: float = 0.1
    max_distance: float = 1000.0
    smooth_factor: float = 0.1


@dataclass
class Viewport:
    """3D viewport configuration."""
    id: str
    name: str
    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600
    settings: ViewportSettings = field(default_factory=lambda: ViewportSettings("Main"))
    camera: CameraController = field(default_factory=CameraController)
    active: bool = True
    visible: bool = True


class ViewportManager:
    """
    Manages multiple 3D viewports and camera controls.
    
    Provides viewport layout management, camera navigation,
    and coordinated view updates across multiple viewports.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('ViewportManager')
        
        # Viewport management
        self.viewports: Dict[str, Viewport] = {}
        self.active_viewport_id: Optional[str] = None
        self.layout_mode = self.config.get('layout_mode', 'single')  # 'single', 'quad', 'custom'
        
        # Navigation state
        self.is_navigating = False
        self.navigation_mode = 'orbit'  # 'orbit', 'pan', 'zoom', 'fly'
        self.mouse_sensitivity = self.config.get('mouse_sensitivity', 1.0)
        self.key_navigation_speed = self.config.get('key_navigation_speed', 1.0)
        
        # Viewport synchronization
        self.sync_cameras = self.config.get('sync_cameras', False)
        self.sync_settings = self.config.get('sync_settings', False)
        
        # Performance settings
        self.adaptive_quality = self.config.get('adaptive_quality', True)
        self.target_fps = self.config.get('target_fps', 60)
        self.min_quality = self.config.get('min_quality', 'medium')
        
        # Initialize default viewport
        self._create_default_viewports()
    
    def _create_default_viewports(self):
        """Create default viewport configuration."""
        # Main viewport
        main_viewport = Viewport(
            id="main",
            name="Main View",
            width=self.config.get('width', 1920),
            height=self.config.get('height', 1080)
        )
        
        self.viewports["main"] = main_viewport
        self.active_viewport_id = "main"
        
        # Create additional viewports based on layout
        if self.layout_mode == 'quad':
            self._create_quad_layout()
    
    def _create_quad_layout(self):
        """Create quad viewport layout."""
        base_width = self.config.get('width', 1920) // 2
        base_height = self.config.get('height', 1080) // 2
        
        # Top view (orthographic)
        top_viewport = Viewport(
            id="top",
            name="Top View",
            x=base_width,
            y=0,
            width=base_width,
            height=base_height,
            settings=ViewportSettings(
                name="Top",
                mode=ViewportMode.WIREFRAME
            )
        )
        top_viewport.camera.position = [0, 0, 10]
        top_viewport.camera.target = [0, 0, 0]
        top_viewport.settings.projection = ProjectionType.ORTHOGRAPHIC
        
        # Front view (orthographic)
        front_viewport = Viewport(
            id="front",
            name="Front View",
            x=0,
            y=base_height,
            width=base_width,
            height=base_height,
            settings=ViewportSettings(
                name="Front",
                mode=ViewportMode.WIREFRAME
            )
        )
        front_viewport.camera.position = [0, -10, 0]
        front_viewport.camera.target = [0, 0, 0]
        front_viewport.settings.projection = ProjectionType.ORTHOGRAPHIC
        
        # Side view (orthographic)
        side_viewport = Viewport(
            id="side",
            name="Side View",
            x=base_width,
            y=base_height,
            width=base_width,
            height=base_height,
            settings=ViewportSettings(
                name="Side",
                mode=ViewportMode.WIREFRAME
            )
        )
        side_viewport.camera.position = [10, 0, 0]
        side_viewport.camera.target = [0, 0, 0]
        side_viewport.settings.projection = ProjectionType.ORTHOGRAPHIC
        
        # Update main viewport size
        self.viewports["main"].width = base_width
        self.viewports["main"].height = base_height
        
        # Add viewports
        self.viewports["top"] = top_viewport
        self.viewports["front"] = front_viewport
        self.viewports["side"] = side_viewport
    
    async def set_layout_mode(self, mode: str):
        """Set viewport layout mode."""
        if mode not in ['single', 'quad', 'custom']:
            self.logger.warning(f"Unknown layout mode: {mode}")
            return
        
        self.layout_mode = mode
        
        if mode == 'single':
            # Keep only main viewport
            main_viewport = self.viewports.get("main")
            self.viewports.clear()
            if main_viewport:
                main_viewport.width = self.config.get('width', 1920)
                main_viewport.height = self.config.get('height', 1080)
                main_viewport.x = 0
                main_viewport.y = 0
                self.viewports["main"] = main_viewport
            else:
                self._create_default_viewports()
        elif mode == 'quad':
            self._create_quad_layout()
        
        self.logger.debug(f"Layout mode set to: {mode}")
    
    async def set_active_viewport(self, viewport_id: str) -> bool:
        """Set the active viewport."""
        if viewport_id in self.viewports:
            self.active_viewport_id = viewport_id
            self.logger.debug(f"Active viewport set to: {viewport_id}")
            return True
        return False
    
    def get_active_viewport(self) -> Optional[Viewport]:
        """Get the currently active viewport."""
        if self.active_viewport_id:
            return self.viewports.get(self.active_viewport_id)
        return None
    
    async def update_viewport_camera(self, viewport_id: str, position: List[float], 
                                   target: List[float], up: Optional[List[float]] = None) -> bool:
        """Update camera for specific viewport."""
        if viewport_id not in self.viewports:
            return False
        
        viewport = self.viewports[viewport_id]
        viewport.camera.position = position[:]
        viewport.camera.target = target[:]
        if up:
            viewport.camera.up = up[:]
        
        # Update distance
        viewport.camera.distance = self._calculate_distance(position, target)
        
        # Sync other cameras if enabled
        if self.sync_cameras:
            await self._sync_cameras(viewport_id)
        
        return True
    
    def _calculate_distance(self, position: List[float], target: List[float]) -> float:
        """Calculate distance between camera position and target."""
        dx = position[0] - target[0]
        dy = position[1] - target[1]
        dz = position[2] - target[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    async def _sync_cameras(self, source_viewport_id: str):
        """Synchronize cameras across viewports."""
        source_viewport = self.viewports.get(source_viewport_id)
        if not source_viewport:
            return
        
        for viewport_id, viewport in self.viewports.items():
            if viewport_id != source_viewport_id and viewport.settings.projection == ProjectionType.PERSPECTIVE:
                viewport.camera.target = source_viewport.camera.target[:]
                viewport.camera.distance = source_viewport.camera.distance
    
    async def orbit_camera(self, viewport_id: str, delta_x: float, delta_y: float):
        """Orbit camera around target."""
        if viewport_id not in self.viewports:
            return
        
        viewport = self.viewports[viewport_id]
        camera = viewport.camera
        
        # Calculate spherical coordinates
        target = camera.target
        position = camera.position
        
        # Vector from target to camera
        dx = position[0] - target[0]
        dy = position[1] - target[1]
        dz = position[2] - target[2]
        
        # Convert to spherical coordinates
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        theta = math.atan2(dy, dx)  # Azimuth
        phi = math.acos(dz / distance) if distance > 0 else 0  # Polar angle
        
        # Apply rotation
        theta += delta_x * camera.orbit_speed * self.mouse_sensitivity
        phi += delta_y * camera.orbit_speed * self.mouse_sensitivity
        
        # Clamp phi to avoid gimbal lock
        phi = max(0.01, min(math.pi - 0.01, phi))
        
        # Convert back to Cartesian coordinates
        new_x = target[0] + distance * math.sin(phi) * math.cos(theta)
        new_y = target[1] + distance * math.sin(phi) * math.sin(theta)
        new_z = target[2] + distance * math.cos(phi)
        
        camera.position = [new_x, new_y, new_z]
        camera.distance = distance
    
    async def pan_camera(self, viewport_id: str, delta_x: float, delta_y: float):
        """Pan camera (move target and position together)."""
        if viewport_id not in self.viewports:
            return
        
        viewport = self.viewports[viewport_id]
        camera = viewport.camera
        
        # Calculate camera's right and up vectors
        forward = [
            camera.target[0] - camera.position[0],
            camera.target[1] - camera.position[1],
            camera.target[2] - camera.position[2]
        ]
        
        # Normalize forward vector
        forward_len = math.sqrt(sum(x*x for x in forward))
        if forward_len > 0:
            forward = [x / forward_len for x in forward]
        
        # Calculate right vector (cross product of forward and up)
        up = camera.up
        right = [
            forward[1] * up[2] - forward[2] * up[1],
            forward[2] * up[0] - forward[0] * up[2],
            forward[0] * up[1] - forward[1] * up[0]
        ]
        
        # Normalize right vector
        right_len = math.sqrt(sum(x*x for x in right))
        if right_len > 0:
            right = [x / right_len for x in right]
        
        # Calculate actual up vector
        actual_up = [
            right[1] * forward[2] - right[2] * forward[1],
            right[2] * forward[0] - right[0] * forward[2],
            right[0] * forward[1] - right[1] * forward[0]
        ]
        
        # Calculate pan movement
        pan_scale = camera.distance * camera.pan_speed * self.mouse_sensitivity
        move_x = (-delta_x * right[0] + delta_y * actual_up[0]) * pan_scale
        move_y = (-delta_x * right[1] + delta_y * actual_up[1]) * pan_scale
        move_z = (-delta_x * right[2] + delta_y * actual_up[2]) * pan_scale
        
        # Apply movement to both position and target
        camera.position[0] += move_x
        camera.position[1] += move_y
        camera.position[2] += move_z
        camera.target[0] += move_x
        camera.target[1] += move_y
        camera.target[2] += move_z
    
    async def zoom_camera(self, viewport_id: str, delta: float):
        """Zoom camera (change distance to target)."""
        if viewport_id not in self.viewports:
            return
        
        viewport = self.viewports[viewport_id]
        camera = viewport.camera
        
        # Calculate zoom factor
        zoom_factor = camera.zoom_speed ** (-delta * self.mouse_sensitivity)
        new_distance = camera.distance * zoom_factor
        
        # Clamp distance
        new_distance = max(camera.min_distance, min(camera.max_distance, new_distance))
        
        if new_distance != camera.distance:
            # Calculate direction from target to camera
            direction = [
                camera.position[0] - camera.target[0],
                camera.position[1] - camera.target[1],
                camera.position[2] - camera.target[2]
            ]
            
            # Normalize direction
            current_distance = math.sqrt(sum(x*x for x in direction))
            if current_distance > 0:
                direction = [x / current_distance for x in direction]
                
                # Update position based on new distance
                camera.position = [
                    camera.target[0] + direction[0] * new_distance,
                    camera.target[1] + direction[1] * new_distance,
                    camera.target[2] + direction[2] * new_distance
                ]
                camera.distance = new_distance
    
    async def set_viewport_mode(self, viewport_id: str, mode: ViewportMode):
        """Set viewport display mode."""
        if viewport_id in self.viewports:
            self.viewports[viewport_id].settings.mode = mode
            self.logger.debug(f"Viewport {viewport_id} mode set to: {mode.value}")
    
    async def set_viewport_projection(self, viewport_id: str, projection: ProjectionType):
        """Set viewport camera projection."""
        if viewport_id in self.viewports:
            self.viewports[viewport_id].settings.projection = projection
            self.logger.debug(f"Viewport {viewport_id} projection set to: {projection.value}")
    
    async def frame_selected(self, viewport_id: str, objects_bounds: Optional[Dict[str, Any]] = None):
        """Frame selected objects or all objects in viewport."""
        if viewport_id not in self.viewports:
            return
        
        viewport = self.viewports[viewport_id]
        camera = viewport.camera
        
        if objects_bounds:
            # Use provided bounds
            min_bounds = objects_bounds.get('min', [-1, -1, -1])
            max_bounds = objects_bounds.get('max', [1, 1, 1])
        else:
            # Default bounds for empty scene
            min_bounds = [-1, -1, -1]
            max_bounds = [1, 1, 1]
        
        # Calculate center and size
        center = [
            (min_bounds[0] + max_bounds[0]) / 2,
            (min_bounds[1] + max_bounds[1]) / 2,
            (min_bounds[2] + max_bounds[2]) / 2
        ]
        
        size = max(
            max_bounds[0] - min_bounds[0],
            max_bounds[1] - min_bounds[1],
            max_bounds[2] - min_bounds[2]
        )
        
        # Set target to center
        camera.target = center[:]
        
        # Calculate appropriate distance
        if viewport.settings.projection == ProjectionType.PERSPECTIVE:
            # For perspective camera, calculate distance based on FOV
            fov_rad = math.radians(45)  # Default FOV
            distance = (size / 2) / math.tan(fov_rad / 2) * 1.5  # 1.5x for padding
        else:
            # For orthographic camera, set a reasonable distance
            distance = size * 2
        
        # Maintain current viewing direction but adjust distance
        current_direction = [
            camera.position[0] - camera.target[0],
            camera.position[1] - camera.target[1],
            camera.position[2] - camera.target[2]
        ]
        
        current_distance = math.sqrt(sum(x*x for x in current_direction))
        if current_distance > 0:
            direction = [x / current_distance for x in current_direction]
        else:
            # Default direction if camera is at target
            direction = [1, 1, 1]
            dir_len = math.sqrt(sum(x*x for x in direction))
            direction = [x / dir_len for x in direction]
        
        # Set new position
        camera.position = [
            center[0] + direction[0] * distance,
            center[1] + direction[1] * distance,
            center[2] + direction[2] * distance
        ]
        camera.distance = distance
        
        self.logger.debug(f"Framed scene in viewport {viewport_id}")
    
    async def reset_camera(self, viewport_id: str):
        """Reset camera to default position."""
        if viewport_id not in self.viewports:
            return
        
        viewport = self.viewports[viewport_id]
        camera = viewport.camera
        
        # Default camera positions based on viewport type
        if viewport_id == "top":
            camera.position = [0, 0, 10]
            camera.target = [0, 0, 0]
        elif viewport_id == "front":
            camera.position = [0, -10, 0]
            camera.target = [0, 0, 0]
        elif viewport_id == "side":
            camera.position = [10, 0, 0]
            camera.target = [0, 0, 0]
        else:
            # Default perspective view
            camera.position = [7.5, -7.5, 5.5]
            camera.target = [0, 0, 0]
        
        camera.up = [0, 0, 1]
        camera.distance = self._calculate_distance(camera.position, camera.target)
        
        self.logger.debug(f"Reset camera for viewport {viewport_id}")
    
    def get_viewport_layout(self) -> Dict[str, Any]:
        """Get current viewport layout configuration."""
        return {
            "mode": self.layout_mode,
            "active_viewport": self.active_viewport_id,
            "viewports": {
                viewport_id: {
                    "id": viewport.id,
                    "name": viewport.name,
                    "x": viewport.x,
                    "y": viewport.y,
                    "width": viewport.width,
                    "height": viewport.height,
                    "active": viewport.active,
                    "visible": viewport.visible,
                    "mode": viewport.settings.mode.value,
                    "projection": viewport.settings.projection.value,
                    "camera": {
                        "position": viewport.camera.position,
                        "target": viewport.camera.target,
                        "up": viewport.camera.up,
                        "distance": viewport.camera.distance
                    }
                }
                for viewport_id, viewport in self.viewports.items()
            }
        }
    
    def get_camera_data(self, viewport_id: str) -> Optional[Dict[str, Any]]:
        """Get camera data for specific viewport."""
        if viewport_id in self.viewports:
            camera = self.viewports[viewport_id].camera
            return {
                "position": camera.position,
                "target": camera.target,
                "up": camera.up,
                "distance": camera.distance,
                "projection": self.viewports[viewport_id].settings.projection.value
            }
        return None
    
    async def handle_mouse_navigation(self, viewport_id: str, event_type: str, 
                                    x: float, y: float, delta_x: float = 0, delta_y: float = 0, 
                                    wheel_delta: float = 0, buttons: int = 0):
        """Handle mouse navigation events."""
        if viewport_id not in self.viewports:
            return
        
        if event_type == "wheel":
            await self.zoom_camera(viewport_id, wheel_delta)
        elif event_type == "drag":
            if buttons & 1:  # Left button - orbit
                await self.orbit_camera(viewport_id, delta_x, delta_y)
            elif buttons & 2:  # Right button - pan
                await self.pan_camera(viewport_id, delta_x, delta_y)
            elif buttons & 4:  # Middle button - zoom
                await self.zoom_camera(viewport_id, delta_y)
    
    async def handle_keyboard_navigation(self, viewport_id: str, key: str, pressed: bool):
        """Handle keyboard navigation."""
        if not pressed or viewport_id not in self.viewports:
            return
        
        speed = self.key_navigation_speed
        
        if key == "Home":
            await self.frame_selected(viewport_id)
        elif key == "NumpadPeriod":
            await self.frame_selected(viewport_id)
        elif key == "Numpad1":
            # Front view
            await self.set_view_direction(viewport_id, [0, -1, 0])
        elif key == "Numpad3":
            # Side view
            await self.set_view_direction(viewport_id, [1, 0, 0])
        elif key == "Numpad7":
            # Top view
            await self.set_view_direction(viewport_id, [0, 0, 1])
    
    async def set_view_direction(self, viewport_id: str, direction: List[float]):
        """Set camera to look in specific direction."""
        if viewport_id not in self.viewports:
            return
        
        viewport = self.viewports[viewport_id]
        camera = viewport.camera
        
        # Normalize direction
        dir_len = math.sqrt(sum(x*x for x in direction))
        if dir_len > 0:
            direction = [x / dir_len for x in direction]
        
        # Set position based on direction and current distance
        camera.position = [
            camera.target[0] + direction[0] * camera.distance,
            camera.target[1] + direction[1] * camera.distance,
            camera.target[2] + direction[2] * camera.distance
        ]
        
        # Set appropriate up vector
        if abs(direction[2]) > 0.9:  # Looking mostly up or down
            camera.up = [0, 1, 0]
        else:
            camera.up = [0, 0, 1]
    
    async def export_viewport_settings(self) -> Dict[str, Any]:
        """Export all viewport settings."""
        return {
            "layout_mode": self.layout_mode,
            "active_viewport": self.active_viewport_id,
            "sync_cameras": self.sync_cameras,
            "sync_settings": self.sync_settings,
            "mouse_sensitivity": self.mouse_sensitivity,
            "viewports": {
                viewport_id: {
                    "settings": {
                        "mode": viewport.settings.mode.value,
                        "projection": viewport.settings.projection.value,
                        "show_grid": viewport.settings.show_grid,
                        "show_axes": viewport.settings.show_axes,
                        "background_color": viewport.settings.background_color
                    },
                    "camera": {
                        "position": viewport.camera.position,
                        "target": viewport.camera.target,
                        "up": viewport.camera.up,
                        "distance": viewport.camera.distance,
                        "zoom_speed": viewport.camera.zoom_speed,
                        "pan_speed": viewport.camera.pan_speed,
                        "orbit_speed": viewport.camera.orbit_speed
                    }
                }
                for viewport_id, viewport in self.viewports.items()
            }
        }

    async def stop(self):
        """Stop the viewport manager and cleanup resources."""
        self.logger.info("Stopping viewport manager...")
        
        # Reset viewports
        self.viewports.clear()
        self.active_viewport = None
        
        # Reset layout
        self.layout_mode = "single"
        
        self.logger.info("Viewport manager stopped")
