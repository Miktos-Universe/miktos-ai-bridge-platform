"""
Miktos AI Bridge Platform - Core Package

This package contains the core AI agent engine and coordination components.
"""

from .agent import MiktosAgent, AgentCommand, ExecutionResult
from .nlp_processor import NLPProcessor, NLPResult, NLPIntent  # type: ignore
from .command_parser import CommandParser, ParsedCommand, ParsedParameter  # type: ignore
from .safety_manager import SafetyManager, SafetyValidationResult, SafetyViolation  # type: ignore
from .learning_engine import LearningEngine, SkillPerformance, LearningInsight  # type: ignore

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
