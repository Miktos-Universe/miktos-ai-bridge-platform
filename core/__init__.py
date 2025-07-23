"""
Miktos AI Bridge Platform - Core Package

This package contains the core AI agent engine and coordination components.
"""

from typing import Any

# Import types from their actual module locations to avoid import conflicts
from .agent import MiktosAgent, AgentCommand, ExecutionResult
from .nlp_processor import NLPProcessor, NLPResult, NLPIntent  # type: ignore
from .command_parser import CommandParser, ParsedCommand, ParsedParameter  # type: ignore
from .safety_manager import SafetyManager  # type: ignore
from .learning_engine import LearningEngine  # type: ignore

# Try to import additional types from their modules, with fallbacks
try:
    from .safety_manager import SafetyValidationResult, SafetyViolation  # type: ignore
except ImportError:
    # Define minimal fallback types if not available
    SafetyValidationResult = Any  # type: ignore
    SafetyViolation = Any  # type: ignore

try:
    from .learning_engine import SkillPerformance, LearningInsight  # type: ignore
except ImportError:
    # Define minimal fallback types if not available
    SkillPerformance = Any  # type: ignore
    LearningInsight = Any  # type: ignore

__all__ = [
    'MiktosAgent',
    'AgentCommand', 
    'ExecutionResult',
    'NLPProcessor',
    'NLPResult', 
    'NLPIntent',
    'CommandParser',
    'ParsedCommand',
    'ParsedParameter',
    'SafetyManager',
    'SafetyValidationResult',
    'SafetyViolation',
    'LearningEngine',
    'SkillPerformance',
    'LearningInsight'
]

__version__ = "1.0.0"
