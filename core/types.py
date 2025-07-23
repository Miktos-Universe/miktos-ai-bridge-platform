"""
Shared Type Definitions for Miktos AI Bridge Platform

This module contains common type definitions used across the platform
to ensure type consistency and avoid import conflicts.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


@dataclass
class NLPIntent:
    """Represents an identified intent from natural language"""
    action: str  # create, modify, delete, etc.
    target: str  # object, material, light, etc.
    parameters: Dict[str, Any]
    confidence: float
    context_references: Optional[List[str]] = None
    
    # Alternative naming for compatibility
    intent_name: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    complexity_score: float = 0.5


@dataclass
class NLPResult:
    """Result from natural language processing"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    context: Dict[str, Any]
    processed_text: str
    suggestions: Optional[List[str]] = None
    
    # Additional fields for compatibility
    original_text: str = ""
    intents: Optional[List[Any]] = None  # For backward compatibility
    suggested_skills: Optional[List[str]] = None
    complexity_score: float = 0.5


@dataclass
class ParsedParameter:
    """A parsed command parameter"""
    name: str
    value: Any
    param_type: str
    confidence: float
    source_text: str
    
    # Additional fields for compatibility
    data_type: Optional[str] = None
    validation_status: str = "valid"
    context_references: Optional[List[str]] = None


@dataclass 
class ParsedCommand:
    """A fully parsed command with extracted intent and parameters"""
    original_text: str
    intent: str
    parameters: List[ParsedParameter]
    confidence: float
    execution_complexity: float
    estimated_time: float
    context: Dict[str, Any]
    nlp_result: 'NLPResult'
    
    # Additional fields for compatibility with different modules
    primary_intent: Optional[str] = None
    target_object: Optional[str] = None
    intents: Optional[List['NLPIntent']] = None
    required_skills: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentCommand:
    """Represents a user command with metadata"""
    text: str
    timestamp: datetime
    session_id: str
    context: Dict[str, Any]
    priority: str = "normal"  # low, normal, high


@dataclass
class ExecutionResult:
    """Represents the result of command execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    skills_used: Optional[List[str]] = None
    errors: Optional[List[str]] = None


class SafetyLevel(Enum):
    """Safety validation levels"""
    MINIMAL = "minimal"
    NORMAL = "normal"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class SafetyViolation:
    """Represents a safety rule violation"""
    rule_name: str
    severity: str  # error, warning, info
    message: str
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class SafetyValidationResult:
    """Result of safety validation"""
    is_safe: bool
    safety_level: SafetyLevel
    violations: List[SafetyViolation]
    warnings: List[str]
    auto_corrections: Dict[str, Any]
    rollback_required: bool
    reason: str
    confidence: float


@dataclass
class SkillPerformance:
    """Performance metrics for a skill"""
    skill_id: str
    execution_count: int
    success_rate: float
    average_execution_time: float
    error_patterns: Dict[str, int]
    performance_trend: List[float]
    last_updated: datetime


@dataclass
class LearningInsight:
    """Learning insight from command execution"""
    insight_type: str
    description: str
    confidence: float
    impact: str  # positive, negative, neutral
    suggestions: List[str]
    data: Dict[str, Any]


# NLP Intent constants
class NLPIntentTypes:
    """Common NLP intent types"""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    QUERY = "query"
    NAVIGATE = "navigate"
    RENDER = "render"
    ANIMATE = "animate"
    MATERIAL = "material"
    LIGHTING = "lighting"
    CAMERA = "camera"
    UNKNOWN = "unknown"


# Operation types for Blender bridge
@dataclass
class BlenderOperation:
    """A single Blender operation"""
    operation_type: str  # create, modify, delete, query
    target: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionPlan:
    """Plan for executing multiple operations"""
    operations: List[BlenderOperation]
    dependencies: Dict[str, List[str]]
    rollback_plan: List[BlenderOperation]
    skills_used: List[str]
    estimated_time: float


@dataclass
class OperationResult:
    """Result of a single operation"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    execution_time: float = 0.0


@dataclass
class BlenderExecutionResult:
    """Result from Blender execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    operations_executed: int = 0
    rollback_performed: bool = False
