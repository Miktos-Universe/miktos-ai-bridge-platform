"""
Operation Validator for Miktos AI Bridge Platform

Validates operations before execution to ensure safety and correctness.
Provides pre-execution validation, parameter checking, and safety constraints.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of operation validation."""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    suggestions: Optional[List[str]] = None
    corrected_parameters: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.corrected_parameters is None:
            self.corrected_parameters = {}


class OperationValidator:
    """
    Validates 3D operations before execution.
    
    Provides safety checks, parameter validation, and constraint enforcement
    to prevent invalid operations and protect user data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger('OperationValidator')
        
        # Validation settings
        self.strict_mode = self.config.get('strict_mode', False)
        self.auto_correct = self.config.get('auto_correct', True)
        self.max_objects_per_operation = self.config.get('max_objects_per_operation', 1000)
        self.max_parameter_value = self.config.get('max_parameter_value', 1000000.0)
        
        # Safety constraints
        self.safety_constraints = {
            'max_subdivisions': 6,
            'max_array_count': 100,
            'max_scale_factor': 1000.0,
            'min_scale_factor': 0.001,
            'max_location_distance': 10000.0,
            'max_rotation_degrees': 720.0
        }
        
        # Valid object types
        self.valid_object_types = {
            'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE',
            'LATTICE', 'EMPTY', 'LIGHT', 'CAMERA', 'SPEAKER'
        }
        
        # Valid primitive types
        self.valid_primitives = {
            'cube', 'sphere', 'cylinder', 'cone', 'torus', 'plane',
            'circle', 'uv_sphere', 'ico_sphere', 'monkey'
        }
        
        # Parameter validation rules
        self.parameter_rules = self._init_parameter_rules()
    
    def _init_parameter_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize parameter validation rules."""
        return {
            'location': {
                'type': (list, tuple),
                'length': 3,
                'element_type': (int, float),
                'min_value': -self.safety_constraints['max_location_distance'],
                'max_value': self.safety_constraints['max_location_distance']
            },
            'rotation': {
                'type': (list, tuple),
                'length': 3,
                'element_type': (int, float),
                'min_value': -math.radians(self.safety_constraints['max_rotation_degrees']),
                'max_value': math.radians(self.safety_constraints['max_rotation_degrees'])
            },
            'scale': {
                'type': (list, tuple, int, float),
                'element_type': (int, float),
                'min_value': self.safety_constraints['min_scale_factor'],
                'max_value': self.safety_constraints['max_scale_factor']
            },
            'size': {
                'type': (int, float),
                'min_value': 0.001,
                'max_value': 1000.0
            },
            'subdivisions': {
                'type': int,
                'min_value': 0,
                'max_value': self.safety_constraints['max_subdivisions']
            },
            'array_count': {
                'type': int,
                'min_value': 1,
                'max_value': self.safety_constraints['max_array_count']
            }
        }
    
    async def validate_operation(self, operation: str, parameters: Dict[str, Any]) -> ValidationResult:
        """
        Validate a complete operation with parameters.
        
        Args:
            operation: Operation name (e.g., 'create_cube', 'scale_object')
            parameters: Operation parameters
            
        Returns:
            ValidationResult: Validation result with suggestions
        """
        try:
            # Basic operation validation
            if not self._is_valid_operation(operation):
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Unknown operation: {operation}",
                    suggestions=[
                        "Check operation name spelling",
                        "Use 'list_operations' to see available operations"
                    ]
                )
            
            # Parameter validation
            param_result = await self._validate_parameters(operation, parameters)
            if not param_result.is_valid:
                return param_result
            
            # Operation-specific validation
            specific_result = await self._validate_operation_specific(operation, parameters)
            if not specific_result.is_valid:
                return specific_result
            
            # Safety constraint validation
            safety_result = await self._validate_safety_constraints(operation, parameters)
            if not safety_result.is_valid:
                return safety_result
            
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message="Operation validation passed"
            )
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation system error: {str(e)}"
            )
    
    def _is_valid_operation(self, operation: str) -> bool:
        """Check if operation name is valid."""
        # Define valid operations
        valid_operations = {
            'create_cube', 'create_sphere', 'create_cylinder', 'create_cone',
            'create_torus', 'create_plane', 'create_circle', 'create_monkey',
            'delete_object', 'duplicate_object', 'scale_object', 'move_object',
            'rotate_object', 'apply_material', 'add_modifier', 'subdivide',
            'extrude', 'inset', 'bevel', 'array', 'mirror', 'solidify'
        }
        
        return operation in valid_operations
    
    async def _validate_parameters(self, operation: str, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate operation parameters."""
        corrected = {}
        warnings = []
        
        for param_name, param_value in parameters.items():
            # Skip validation for None values
            if param_value is None:
                continue
            
            # Get validation rule for parameter
            if param_name not in self.parameter_rules:
                if self.strict_mode:
                    return ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Unknown parameter: {param_name}"
                    )
                continue
            
            rule = self.parameter_rules[param_name]
            
            # Type validation
            type_result = self._validate_parameter_type(param_name, param_value, rule)
            if not type_result.is_valid:
                if not self.auto_correct:
                    return type_result
                
                # Try to auto-correct
                corrected_value = self._auto_correct_parameter(param_name, param_value, rule)
                if corrected_value is not None:
                    corrected[param_name] = corrected_value
                    warnings.append(f"Auto-corrected {param_name}: {param_value} -> {corrected_value}")
                else:
                    return type_result
            
            # Value range validation
            range_result = self._validate_parameter_range(param_name, param_value, rule)
            if not range_result.is_valid:
                if not self.auto_correct:
                    return range_result
                
                # Try to clamp to valid range
                clamped_value = self._clamp_parameter(param_name, param_value, rule)
                if clamped_value != param_value:
                    corrected[param_name] = clamped_value
                    warnings.append(f"Clamped {param_name}: {param_value} -> {clamped_value}")
        
        # Return result with corrections if any
        severity = ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        message = "Parameters validated"
        if warnings:
            message += f" with corrections: {'; '.join(warnings)}"
        
        return ValidationResult(
            is_valid=True,
            severity=severity,
            message=message,
            corrected_parameters=corrected
        )
    
    def _validate_parameter_type(self, param_name: str, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate parameter type."""
        expected_type = rule.get('type')
        if expected_type is None:
            return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="No type constraint")
        
        # Handle multiple allowed types
        if isinstance(expected_type, (list, tuple)):
            if not any(isinstance(value, t) for t in expected_type):
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter {param_name} must be one of types: {expected_type}, got {type(value)}"
                )
        else:
            if not isinstance(value, expected_type):
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter {param_name} must be {expected_type}, got {type(value)}"
                )
        
        # Validate list/tuple elements
        if isinstance(value, (list, tuple)):
            element_type = rule.get('element_type')
            if element_type:
                for i, element in enumerate(value):
                    if not isinstance(element, element_type):
                        return ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            message=f"Parameter {param_name}[{i}] must be {element_type}, got {type(element)}"
                        )
            
            # Validate length
            expected_length = rule.get('length')
            if expected_length and len(value) != expected_length:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter {param_name} must have length {expected_length}, got {len(value)}"
                )
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Type validation passed")
    
    def _validate_parameter_range(self, param_name: str, value: Any, rule: Dict[str, Any]) -> ValidationResult:
        """Validate parameter value range."""
        min_value = rule.get('min_value')
        max_value = rule.get('max_value')
        
        if isinstance(value, (list, tuple)):
            # Validate each element in range
            for i, element in enumerate(value):
                if isinstance(element, (int, float)):
                    if min_value is not None and element < min_value:
                        return ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            message=f"Parameter {param_name}[{i}] = {element} is below minimum {min_value}"
                        )
                    if max_value is not None and element > max_value:
                        return ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            message=f"Parameter {param_name}[{i}] = {element} is above maximum {max_value}"
                        )
        elif isinstance(value, (int, float)):
            if min_value is not None and value < min_value:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter {param_name} = {value} is below minimum {min_value}"
                )
            if max_value is not None and value > max_value:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter {param_name} = {value} is above maximum {max_value}"
                )
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Range validation passed")
    
    def _auto_correct_parameter(self, param_name: str, value: Any, rule: Dict[str, Any]) -> Any:
        """Attempt to auto-correct parameter value."""
        expected_type = rule.get('type')
        
        # Try type conversion
        if expected_type == float and isinstance(value, (int, str)):
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
        elif expected_type == int and isinstance(value, (float, str)):
            try:
                return int(float(value))
            except (ValueError, TypeError):
                pass
        elif expected_type == (list, tuple) and isinstance(value, (int, float)):
            # Convert single value to list
            expected_length = rule.get('length', 3)
            return [value] * expected_length
        
        return None
    
    def _clamp_parameter(self, param_name: str, value: Any, rule: Dict[str, Any]) -> Any:
        """Clamp parameter value to valid range."""
        min_value = rule.get('min_value')
        max_value = rule.get('max_value')
        
        if isinstance(value, (list, tuple)):
            clamped = []
            for element in value:
                if isinstance(element, (int, float)):
                    clamped_element = element
                    if min_value is not None:
                        clamped_element = max(clamped_element, min_value)
                    if max_value is not None:
                        clamped_element = min(clamped_element, max_value)
                    clamped.append(clamped_element)
                else:
                    clamped.append(element)
            return type(value)(clamped)
        
        elif isinstance(value, (int, float)):
            clamped_value = value
            if min_value is not None:
                clamped_value = max(clamped_value, min_value)
            if max_value is not None:
                clamped_value = min(clamped_value, max_value)
            return clamped_value
        
        return value
    
    async def _validate_operation_specific(self, operation: str, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate operation-specific constraints."""
        
        # Primitive creation validation
        if operation.startswith('create_'):
            primitive_type = operation[7:]  # Remove 'create_' prefix
            if primitive_type in self.valid_primitives:
                return await self._validate_primitive_creation(primitive_type, parameters)
        
        # Object manipulation validation
        elif operation in ['scale_object', 'move_object', 'rotate_object']:
            return await self._validate_object_manipulation(operation, parameters)
        
        # Material operations
        elif operation == 'apply_material':
            return await self._validate_material_application(parameters)
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Operation validation passed")
    
    async def _validate_primitive_creation(self, primitive_type: str, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate primitive creation parameters."""
        
        # Sphere-specific validation
        if primitive_type in ['sphere', 'uv_sphere', 'ico_sphere']:
            radius = parameters.get('radius', 1.0)
            if radius <= 0:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="Sphere radius must be positive",
                    suggestions=["Use positive value for radius parameter"]
                )
        
        # Cylinder-specific validation
        elif primitive_type == 'cylinder':
            radius = parameters.get('radius', 1.0)
            height = parameters.get('height', 2.0)
            if radius <= 0 or height <= 0:
                return ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="Cylinder dimensions must be positive",
                    suggestions=["Use positive values for radius and height"]
                )
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Primitive validation passed")
    
    async def _validate_object_manipulation(self, operation: str, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate object manipulation parameters."""
        
        # Check for object reference
        if 'object_name' not in parameters:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Object manipulation requires object_name parameter",
                suggestions=["Specify which object to manipulate", "Use 'selected' for selected objects"]
            )
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Object manipulation validation passed")
    
    async def _validate_material_application(self, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate material application parameters."""
        
        if 'material_name' not in parameters:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Material application requires material_name parameter",
                suggestions=["Specify material name to apply"]
            )
        
        material_name = parameters['material_name']
        if not isinstance(material_name, str) or not material_name.strip():
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Material name must be a non-empty string"
            )
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Material validation passed")
    
    async def _validate_safety_constraints(self, operation: str, parameters: Dict[str, Any]) -> ValidationResult:
        """Validate safety constraints."""
        
        # Check for potentially dangerous operations
        dangerous_operations = ['delete_all', 'clear_scene', 'reset_scene']
        if operation in dangerous_operations:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Potentially destructive operation: {operation}",
                suggestions=[
                    "Consider backing up your work",
                    "Use more specific delete operations"
                ]
            )
        
        # Check for excessive parameter values
        for param_name, param_value in parameters.items():
            if isinstance(param_value, (int, float)):
                if abs(param_value) > self.max_parameter_value:
                    return ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Parameter {param_name} value {param_value} exceeds safety limit",
                        suggestions=[f"Use values within ±{self.max_parameter_value}"]
                    )
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Safety validation passed")
    
    def validate_object_name(self, name: str) -> ValidationResult:
        """Validate object name."""
        if not isinstance(name, str):
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Object name must be a string"
            )
        
        if not name.strip():
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Object name cannot be empty"
            )
        
        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Object name contains invalid characters: {invalid_chars}"
            )
        
        return ValidationResult(is_valid=True, severity=ValidationSeverity.INFO, message="Object name is valid")
    
    def get_parameter_suggestions(self, operation: str) -> Dict[str, str]:
        """Get parameter suggestions for an operation."""
        suggestions = {}
        
        if operation.startswith('create_'):
            suggestions.update({
                'location': 'Position in 3D space as [x, y, z]',
                'rotation': 'Rotation in radians as [x, y, z]',
                'scale': 'Scale factor as number or [x, y, z]'
            })
        
        return suggestions
