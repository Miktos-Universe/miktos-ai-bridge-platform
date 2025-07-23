"""
Miktos AI Bridge Platform - Viewer Package

This package contains the viewer components for real-time 3D visualization.
Provides WebGL rendering, viewport management, and interactive controls.
"""

from .webgl_renderer import WebGLRenderer, RenderObject, Material, LightSource  # type: ignore
from .viewport_manager import ViewportManager, Viewport, ViewportSettings, CameraController  # type: ignore
from .scene_sync import SceneSync, SceneObject, SceneState, SceneChange  # type: ignore
from .real_time_viewer import RealTimeViewer, ViewerState, ViewerUpdate  # type: ignore

__all__ = [
    'WebGLRenderer',
    'RenderObject',
    'Material',
    'LightSource',
    'ViewportManager',
    'Viewport',
    'ViewportSettings',
    'CameraController',
    'SceneSync',
    'SceneObject',
    'SceneState',
    'SceneChange',
    'RealTimeViewer',
    'ViewerState',
    'ViewerUpdate'
]

__version__ = "1.0.0"
