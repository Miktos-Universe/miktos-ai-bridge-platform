"""
Safety Manager for Miktos Agent

Provides comprehensive safety validation for Blender operations,
including parameter validation, destructive operation checks,
and rollback capabilities.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


# Import type definitions from command_parser
@dataclass
class ParsedParameter:
    """Represents a parsed parameter with validation info"""
    name: str
    value: Any
    data_type: str
    confidence: float
    validation_status: str = "valid"  # valid, invalid, needs_validation


@dataclass
class NLPIntent:
    """Represents an identified intent from natural language"""
    action: str  # create, modify, delete, etc.
    target: str  # object, material, light, etc.
    parameters: Dict[str, Any]
    confidence: float
    context_references: Optional[List[str]] = None


@dataclass
class ParsedCommand:
    """Represents a fully parsed command ready for execution"""
    original_text: str
    primary_intent: str
    target_object: str
    parameters: Dict[str, ParsedParameter]
    intents: List[NLPIntent]
    confidence: float
    execution_complexity: float
    required_skills: List[str]
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SafetyLevel(Enum):
    """Safety validation levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    STRICT = "strict"


class OperationType(Enum):
    """Types of operations with different safety requirements"""
    SAFE = "safe"              # Read-only, non-destructive
    MODIFY = "modify"          # Modifies existing objects
    CREATE = "create"          # Creates new objects
    DELETE = "delete"          # Destructive operations
    SYSTEM = "system"          # System-level operations
    EXPERIMENTAL = "experimental"  # Untested or risky operations


@dataclass
class SafetyRule:
    """Represents a safety validation rule"""
    name: str
    description: str
    operation_types: List[OperationType]
    severity: str  # "error", "warning", "info"
    validator_function: str
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class SafetyViolation:
    """Represents a safety rule violation"""
    rule_name: str
    severity: str
    message: str
    parameter: Optional[str] = None
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
    reason: Optional[str] = None
    confidence: float = 1.0


class SafetyManager:
    """
    Advanced safety management system for Blender operations.
    Validates commands against safety rules and provides rollback capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('SafetyManager')
        
        # Safety configuration
        self.validation_level = SafetyLevel(config.get('validation_level', 'normal'))
        self.rollback_enabled = config.get('rollback_enabled', True)
        self.max_operations_per_command = config.get('max_operations_per_command', 10)
        self.destructive_operations_require_confirmation = config.get('destructive_operations_require_confirmation', True)
        self.backup_before_major_changes = config.get('backup_before_major_changes', True)
        
        # Initialize safety rules
        self.safety_rules = self._init_safety_rules()
        
        # Operation tracking
        self.operation_history = []
        self.max_history_size = config.get('max_history_size', 1000)
        
        # Blacklisted operations
        self.blacklisted_operations = config.get('blacklisted_operations', [])
        
        # Parameter limits
        self.parameter_limits = self._init_parameter_limits()
    
    def _init_safety_rules(self) -> List[SafetyRule]:
        """Initialize safety validation rules"""
        rules = []
        
        # Destructive operation rules
        rules.append(SafetyRule(
            name="destructive_operation_warning",
            description="Warn before destructive operations",
            operation_types=[OperationType.DELETE],
            severity="warning",
            validator_function="validate_destructive_operation"
        ))
        
        # Parameter range validation
        rules.append(SafetyRule(
            name="parameter_range_validation",
            description="Validate parameter ranges",
            operation_types=[OperationType.CREATE, OperationType.MODIFY],
            severity="error",
            validator_function="validate_parameter_ranges"
        ))
        
        # Object count limits
        rules.append(SafetyRule(
            name="object_count_limit",
            description="Prevent excessive object creation",
            operation_types=[OperationType.CREATE],
            severity="error",
            validator_function="validate_object_count",
            parameters={"max_objects_per_operation": 100}
        ))
        
        # System resource protection
        rules.append(SafetyRule(
            name="resource_protection",
            description="Protect system resources",
            operation_types=[OperationType.CREATE, OperationType.MODIFY],
            severity="error",
            validator_function="validate_resource_usage"
        ))
        
        # Subdivision safety
        rules.append(SafetyRule(
            name="subdivision_limit",
            description="Prevent excessive subdivision",
            operation_types=[OperationType.MODIFY],
            severity="error",
            validator_function="validate_subdivision_levels",
            parameters={"max_subdivisions": 6}
        ))
        
        # File system safety
        rules.append(SafetyRule(
            name="file_system_safety",
            description="Prevent unauthorized file operations",
            operation_types=[OperationType.SYSTEM],
            severity="error",
            validator_function="validate_file_operations"
        ))
        
        # Animation safety
        rules.append(SafetyRule(
            name="animation_frame_limit",
            description="Prevent excessive animation frames",
            operation_types=[OperationType.CREATE, OperationType.MODIFY],
            severity="warning",
            validator_function="validate_animation_frames",
            parameters={"max_frames": 10000}
        ))
        
        return rules
    
    def _init_parameter_limits(self) -> Dict[str, Dict[str, Union[int, float]]]:
        """Initialize parameter limits for safety validation"""
        return {
            'scale': {
                'min': 0.001,
                'max': 1000.0,
                'warning_threshold': 100.0
            },
            'rotation': {
                'min': -360.0,
                'max': 360.0,
                'warning_threshold': 180.0
            },
            'subdivisions': {
                'min': 0,
                'max': 6,
                'warning_threshold': 4
            },
            'array_count': {
                'min': 1,
                'max': 100,
                'warning_threshold': 50
            },
            'extrude_distance': {
                'min': 0.0,
                'max': 1000.0,
                'warning_threshold': 100.0
            },
            'bevel_offset': {
                'min': 0.0,
                'max': 10.0,
                'warning_threshold': 5.0
            },
            'particle_count': {
                'min': 1,
                'max': 100000,
                'warning_threshold': 10000
            }
        }
    
    async def validate_command(self, parsed_command: ParsedCommand) -> SafetyValidationResult:
        """
        Validate a parsed command against safety rules
        
        Args:
            parsed_command: The parsed command to validate
            
        Returns:
            SafetyValidationResult with validation details
        """
        violations = []
        warnings = []
        auto_corrections = {}
        rollback_required = False
        
        try:
            # Determine operation type
            operation_type = self._determine_operation_type(parsed_command)
            
            # Check if operation is blacklisted
            if self._is_blacklisted_operation(parsed_command):
                return SafetyValidationResult(
                    is_safe=False,
                    safety_level=self.validation_level,
                    violations=[SafetyViolation(
                        rule_name="blacklisted_operation",
                        severity="error",
                        message="Operation is blacklisted",
                        suggested_fix="Use an alternative approach"
                    )],
                    warnings=[],
                    auto_corrections={},
                    rollback_required=False,
                    reason="Blacklisted operation",
                    confidence=1.0
                )
            
            # Apply safety rules
            for rule in self.safety_rules:
                if operation_type in rule.operation_types:
                    rule_violations = await self._apply_safety_rule(rule, parsed_command)
                    violations.extend(rule_violations)
            
            # Validate command complexity
            complexity_violations = self._validate_command_complexity(parsed_command)
            violations.extend(complexity_violations)
            
            # Check for auto-corrections
            auto_corrections = self._generate_auto_corrections(parsed_command, violations)
            
            # Determine if rollback is required
            rollback_required = self._requires_rollback(operation_type, violations)
            
            # Generate warnings
            warnings = self._generate_warnings(parsed_command, violations)
            
            # Determine overall safety
            is_safe = self._is_command_safe(violations, self.validation_level)
            
            # Create reason if unsafe
            reason = None
            if not is_safe:
                error_violations = [v for v in violations if v.severity == "error"]
                if error_violations:
                    reason = f"Safety violations: {', '.join([v.rule_name for v in error_violations])}"
            
            return SafetyValidationResult(
                is_safe=is_safe,
                safety_level=self.validation_level,
                violations=violations,
                warnings=warnings,
                auto_corrections=auto_corrections,
                rollback_required=rollback_required,
                reason=reason,
                confidence=self._calculate_validation_confidence(violations, parsed_command)
            )
        
        except Exception as e:
            self.logger.error(f"Safety validation failed: {e}")
            return SafetyValidationResult(
                is_safe=False,
                safety_level=self.validation_level,
                violations=[SafetyViolation(
                    rule_name="validation_error",
                    severity="error",
                    message=f"Safety validation failed: {str(e)}"
                )],
                warnings=[],
                auto_corrections={},
                rollback_required=True,
                reason="Validation system error",
                confidence=0.0
            )
    
    def _determine_operation_type(self, parsed_command: ParsedCommand) -> OperationType:
        """Determine the type of operation for safety classification"""
        intent = parsed_command.primary_intent.lower()
        
        if 'delete' in intent or 'remove' in intent or 'clear' in intent:
            return OperationType.DELETE
        elif 'create' in intent or 'add' in intent or 'make' in intent:
            return OperationType.CREATE
        elif 'modify' in intent or 'change' in intent or 'edit' in intent:
            return OperationType.MODIFY
        elif 'system' in intent or 'config' in intent:
            return OperationType.SYSTEM
        else:
            return OperationType.SAFE
    
    def _is_blacklisted_operation(self, parsed_command: ParsedCommand) -> bool:
        """Check if operation is blacklisted"""
        for blacklisted in self.blacklisted_operations:
            if blacklisted.lower() in parsed_command.primary_intent.lower():
                return True
            if blacklisted.lower() in parsed_command.original_text.lower():
                return True
        return False
    
    async def _apply_safety_rule(self, rule: SafetyRule, parsed_command: ParsedCommand) -> List[SafetyViolation]:
        """Apply a specific safety rule to a command"""
        violations = []
        
        try:
            # Get validator function
            validator = getattr(self, rule.validator_function, None)
            if not validator:
                self.logger.warning(f"Validator function not found: {rule.validator_function}")
                return violations
            
            # Call validator
            if asyncio.iscoroutinefunction(validator):
                rule_violations = await validator(parsed_command, rule)
            else:
                rule_violations = validator(parsed_command, rule)
            
            violations.extend(rule_violations)
        
        except Exception as e:
            self.logger.error(f"Error applying safety rule {rule.name}: {e}")
            violations.append(SafetyViolation(
                rule_name=rule.name,
                severity="error",
                message=f"Rule validation failed: {str(e)}"
            ))
        
        return violations
    
    # Safety rule validators
    def validate_destructive_operation(self, parsed_command: ParsedCommand, rule: SafetyRule) -> List[SafetyViolation]:
        """Validate destructive operations"""
        violations = []
        
        if self.destructive_operations_require_confirmation:
            # Check if confirmation is present in metadata
            metadata = parsed_command.metadata or {}
            if not metadata.get('user_confirmed', False):
                violations.append(SafetyViolation(
                    rule_name=rule.name,
                    severity="warning",
                    message="Destructive operation requires user confirmation",
                    suggested_fix="Add confirmation flag or use safer alternative",
                    auto_fixable=False
                ))
        
        return violations
    
    def validate_parameter_ranges(self, parsed_command: ParsedCommand, rule: SafetyRule) -> List[SafetyViolation]:
        """Validate parameter ranges against safety limits"""
        violations = []
        
        for param_name, param in parsed_command.parameters.items():
            if param.data_type == 'numeric':
                # Check if parameter has defined limits
                for limit_name, limits in self.parameter_limits.items():
                    if limit_name in param_name.lower():
                        value = param.value
                        
                        if value < limits['min'] or value > limits['max']:
                            violations.append(SafetyViolation(
                                rule_name=rule.name,
                                severity="error",
                                message=f"Parameter {param_name} value {value} outside safe range [{limits['min']}, {limits['max']}]",
                                parameter=param_name,
                                suggested_fix=f"Use value between {limits['min']} and {limits['max']}",
                                auto_fixable=True
                            ))
                        elif value > limits.get('warning_threshold', limits['max']):
                            violations.append(SafetyViolation(
                                rule_name=rule.name,
                                severity="warning",
                                message=f"Parameter {param_name} value {value} exceeds recommended threshold {limits['warning_threshold']}",
                                parameter=param_name,
                                suggested_fix=f"Consider using value below {limits['warning_threshold']}",
                                auto_fixable=True
                            ))
        
        return violations
    
    def validate_object_count(self, parsed_command: ParsedCommand, rule: SafetyRule) -> List[SafetyViolation]:
        """Validate object creation count"""
        violations = []
        
        max_objects = (rule.parameters or {}).get('max_objects_per_operation', 100)
        
        # Check for array/duplicate operations
        for param_name, param in parsed_command.parameters.items():
            if 'count' in param_name.lower() or 'array' in param_name.lower():
                if param.data_type == 'numeric' and param.value > max_objects:
                    violations.append(SafetyViolation(
                        rule_name=rule.name,
                        severity="error",
                        message=f"Object count {param.value} exceeds maximum {max_objects}",
                        parameter=param_name,
                        suggested_fix=f"Reduce count to {max_objects} or less",
                        auto_fixable=True
                    ))
        
        return violations
    
    def validate_resource_usage(self, parsed_command: ParsedCommand, rule: SafetyRule) -> List[SafetyViolation]:
        """Validate resource usage impact"""
        violations = []
        
        # Calculate estimated resource impact
        resource_score = self._calculate_resource_impact(parsed_command)
        
        if resource_score > 0.8:
            violations.append(SafetyViolation(
                rule_name=rule.name,
                severity="warning",
                message=f"High resource usage expected (score: {resource_score:.2f})",
                suggested_fix="Consider breaking operation into smaller steps",
                auto_fixable=False
            ))
        
        return violations
    
    def validate_subdivision_levels(self, parsed_command: ParsedCommand, rule: SafetyRule) -> List[SafetyViolation]:
        """Validate subdivision levels"""
        violations = []
        
        max_subdivisions = (rule.parameters or {}).get('max_subdivisions', 6)
        
        for param_name, param in parsed_command.parameters.items():
            if 'subdivision' in param_name.lower() and param.data_type == 'numeric':
                if param.value > max_subdivisions:
                    violations.append(SafetyViolation(
                        rule_name=rule.name,
                        severity="error",
                        message=f"Subdivision level {param.value} exceeds maximum {max_subdivisions}",
                        parameter=param_name,
                        suggested_fix=f"Use {max_subdivisions} or fewer subdivisions",
                        auto_fixable=True
                    ))
        
        return violations
    
    def validate_file_operations(self, parsed_command: ParsedCommand, rule: SafetyRule) -> List[SafetyViolation]:
        """Validate file system operations"""
        violations = []
        
        # Check for file-related operations in command text
        file_keywords = ['save', 'load', 'import', 'export', 'open', 'write', 'read']
        text_lower = parsed_command.original_text.lower()
        
        for keyword in file_keywords:
            if keyword in text_lower:
                violations.append(SafetyViolation(
                    rule_name=rule.name,
                    severity="warning",
                    message=f"File operation detected: {keyword}",
                    suggested_fix="Ensure file paths are safe and authorized",
                    auto_fixable=False
                ))
                break
        
        return violations
    
    def validate_animation_frames(self, parsed_command: ParsedCommand, rule: SafetyRule) -> List[SafetyViolation]:
        """Validate animation frame counts"""
        violations = []
        
        max_frames = (rule.parameters or {}).get('max_frames', 10000)
        
        # Check for frame-related parameters
        for param_name, param in parsed_command.parameters.items():
            if 'frame' in param_name.lower() and param.data_type == 'numeric':
                if param.value > max_frames:
                    violations.append(SafetyViolation(
                        rule_name=rule.name,
                        severity="warning",
                        message=f"Frame count {param.value} exceeds recommended maximum {max_frames}",
                        parameter=param_name,
                        suggested_fix=f"Consider using {max_frames} or fewer frames",
                        auto_fixable=True
                    ))
        
        return violations
    
    def _validate_command_complexity(self, parsed_command: ParsedCommand) -> List[SafetyViolation]:
        """Validate overall command complexity"""
        violations = []
        
        # Check execution complexity
        if parsed_command.execution_complexity > 0.9:
            violations.append(SafetyViolation(
                rule_name="complexity_warning",
                severity="warning",
                message=f"Very high execution complexity: {parsed_command.execution_complexity:.2f}",
                suggested_fix="Consider breaking into simpler commands",
                auto_fixable=False
            ))
        
        # Check number of operations
        if len(parsed_command.required_skills) > self.max_operations_per_command:
            violations.append(SafetyViolation(
                rule_name="operation_count_limit",
                severity="error",
                message=f"Too many operations required: {len(parsed_command.required_skills)}",
                suggested_fix=f"Limit to {self.max_operations_per_command} operations per command",
                auto_fixable=False
            ))
        
        return violations
    
    def _calculate_resource_impact(self, parsed_command: ParsedCommand) -> float:
        """Calculate estimated resource impact score (0.0 to 1.0)"""
        impact = 0.0
        
        # Base impact from complexity
        impact += parsed_command.execution_complexity * 0.3
        
        # Impact from number of operations
        impact += min(len(parsed_command.required_skills) / 10.0, 0.3)
        
        # Impact from specific parameters
        for param_name, param in parsed_command.parameters.items():
            if param.data_type == 'numeric':
                # High subdivision impact
                if 'subdivision' in param_name.lower():
                    impact += min(param.value / 10.0, 0.4)
                
                # Array/count impact
                elif 'count' in param_name.lower() or 'array' in param_name.lower():
                    impact += min(param.value / 100.0, 0.3)
        
        return min(impact, 1.0)
    
    def _generate_auto_corrections(self, parsed_command: ParsedCommand, violations: List[SafetyViolation]) -> Dict[str, Any]:
        """Generate automatic corrections for fixable violations"""
        corrections = {}
        
        for violation in violations:
            if violation.auto_fixable and violation.parameter:
                param = parsed_command.parameters.get(violation.parameter)
                if param:
                    # Auto-correct parameter ranges
                    if "outside safe range" in violation.message:
                        for limit_name, limits in self.parameter_limits.items():
                            if limit_name in violation.parameter.lower():
                                # Clamp to safe range
                                corrected_value = max(limits['min'], min(param.value, limits['max']))
                                corrections[violation.parameter] = corrected_value
                                break
        
        return corrections
    
    def _requires_rollback(self, operation_type: OperationType, violations: List[SafetyViolation]) -> bool:
        """Determine if rollback is required"""
        if not self.rollback_enabled:
            return False
        
        # Require rollback for destructive operations with errors
        if operation_type == OperationType.DELETE:
            error_violations = [v for v in violations if v.severity == "error"]
            return len(error_violations) > 0
        
        # Require rollback for system operations
        if operation_type == OperationType.SYSTEM:
            return True
        
        return False
    
    def _generate_warnings(self, parsed_command: ParsedCommand, violations: List[SafetyViolation]) -> List[str]:
        """Generate warning messages"""
        warnings = []
        
        # Add warnings from violations
        warning_violations = [v for v in violations if v.severity == "warning"]
        warnings.extend([v.message for v in warning_violations])
        
        # Add general warnings
        if parsed_command.confidence < 0.7:
            warnings.append(f"Low command confidence: {parsed_command.confidence:.2f}")
        
        if parsed_command.execution_complexity > 0.8:
            warnings.append(f"High execution complexity: {parsed_command.execution_complexity:.2f}")
        
        return warnings
    
    def _is_command_safe(self, violations: List[SafetyViolation], safety_level: SafetyLevel) -> bool:
        """Determine if command is safe based on violations and safety level"""
        error_violations = [v for v in violations if v.severity == "error"]
        warning_violations = [v for v in violations if v.severity == "warning"]
        
        # Error violations always make command unsafe
        if error_violations:
            return False
        
        # Check warning threshold based on safety level
        if safety_level == SafetyLevel.STRICT:
            return len(warning_violations) == 0
        elif safety_level == SafetyLevel.HIGH:
            return len(warning_violations) <= 1
        elif safety_level == SafetyLevel.NORMAL:
            return len(warning_violations) <= 3
        else:  # LOW
            return len(warning_violations) <= 5
    
    def _calculate_validation_confidence(self, violations: List[SafetyViolation], parsed_command: ParsedCommand) -> float:
        """Calculate confidence in safety validation"""
        confidence = 1.0
        
        # Reduce confidence for each violation
        error_count = len([v for v in violations if v.severity == "error"])
        warning_count = len([v for v in violations if v.severity == "warning"])
        
        confidence -= error_count * 0.2
        confidence -= warning_count * 0.1
        
        # Factor in command confidence
        confidence *= parsed_command.confidence
        
        return max(confidence, 0.0)
    
    async def create_rollback_plan(self, parsed_command: ParsedCommand) -> Dict[str, Any]:
        """Create a rollback plan for a command"""
        rollback_plan = {
            "enabled": self.rollback_enabled,
            "operations": [],
            "backup_required": self.backup_before_major_changes,
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine rollback operations based on command type
        operation_type = self._determine_operation_type(parsed_command)
        
        if operation_type == OperationType.CREATE:
            rollback_plan["operations"].append({
                "type": "delete_created_objects",
                "description": "Remove objects created by this command"
            })
        
        elif operation_type == OperationType.MODIFY:
            rollback_plan["operations"].append({
                "type": "restore_object_state",
                "description": "Restore objects to previous state"
            })
        
        elif operation_type == OperationType.DELETE:
            rollback_plan["operations"].append({
                "type": "restore_deleted_objects",
                "description": "Restore deleted objects from backup"
            })
            rollback_plan["backup_required"] = True
        
        return rollback_plan
    
    def add_safety_rule(self, rule: SafetyRule):
        """Add a custom safety rule"""
        self.safety_rules.append(rule)
        self.logger.info(f"Added safety rule: {rule.name}")
    
    def remove_safety_rule(self, rule_name: str):
        """Remove a safety rule by name"""
        self.safety_rules = [r for r in self.safety_rules if r.name != rule_name]
        self.logger.info(f"Removed safety rule: {rule_name}")
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety manager status"""
        return {
            "validation_level": self.validation_level.value,
            "rollback_enabled": self.rollback_enabled,
            "active_rules": len(self.safety_rules),
            "operation_history_size": len(self.operation_history),
            "blacklisted_operations": len(self.blacklisted_operations)
        }


# Utility functions
def create_safety_rule(name: str, description: str, operation_types: List[str], 
                      severity: str, validator_function: str, 
                      parameters: Optional[Dict[str, Any]] = None) -> SafetyRule:
    """Create a new safety rule"""
    op_types = [OperationType(op_type) for op_type in operation_types]
    return SafetyRule(
        name=name,
        description=description,
        operation_types=op_types,
        severity=severity,
        validator_function=validator_function,
        parameters=parameters or {}
    )


if __name__ == "__main__":
    # Test the safety manager
    print("Safety manager module loaded successfully")
