"""
Miktos AI Bridge Platform - Agent Package

This package contains the core agent components for the Miktos AI Bridge Platform.
Provides Blender integration, scene management, and operation validation.
"""

from .blender_bridge import BlenderBridge, BlenderResult, BlenderOperation, ExecutionPlan
from .scene_manager import SceneManager, SceneObject, SceneState, SceneDiff  # type: ignore
from .operation_validator import OperationValidator, ValidationResult, ParameterConfig  # type: ignore
from .result_analyzer import ResultAnalyzer, AnalysisResult, PerformanceMetrics  # type: ignore

__all__ = [
    'BlenderBridge',
    'BlenderResult', 
    'BlenderOperation',
    'ExecutionPlan',
    'SceneManager',
    'SceneObject',
    'SceneState', 
    'SceneDiff',
    'OperationValidator',
    'ValidationResult',
    'ParameterConfig',
    'ResultAnalyzer',
    'AnalysisResult',
    'PerformanceMetrics'
]

__version__ = "1.0.0"
