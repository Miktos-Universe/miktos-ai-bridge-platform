"""
Miktos AI Bridge Platform

Intelligent Blender automation through natural language processing.
Provides seamless integration between AI agents and 3D workflows.
"""

__version__ = "1.0.0"
__author__ = "Miktos Team"
__email__ = "contact@miktos.ai"

# Import main components for easy access
from core.agent import MiktosAgent
from viewer.real_time_viewer import RealTimeViewer  # type: ignore

__all__ = [
    "MiktosAgent",
    "RealTimeViewer"
]
