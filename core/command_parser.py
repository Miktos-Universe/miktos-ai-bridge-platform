"""
Command Parser for Miktos Agent

Converts natural language processing results into structured commands
that can be executed by the skills system.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NLPIntent:
    """Represents an identified intent from natural language"""
    action: str  # create, modify, delete, etc.
    target: str  # object, material, light, etc.
    parameters: Dict[str, Any]
    confidence: float
    context_references: Optional[List[str]] = None


@dataclass
class NLPResult:
    """Result of natural language processing"""
    original_text: str
    intents: List[NLPIntent]
    entities: Dict[str, List[str]]
    sentiment: float
    complexity_score: float
    suggested_skills: List[str]


@dataclass
class ParsedParameter:
    """Represents a parsed parameter with validation info"""
    name: str
    value: Any
    data_type: str
    confidence: float
    validation_status: str = "valid"  # valid, invalid, needs_validation


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


class CommandParser:
    """
    Advanced command parser that converts NLP results into executable commands.
    Handles parameter extraction, validation, and command structuring.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_complexity = config.get('max_complexity', 0.8)
        self.intent_confidence_threshold = config.get('intent_confidence_threshold', 0.6)
        self.parameter_validation = config.get('parameter_validation', True)
        
        # Parameter type mappings
        self._init_parameter_types()
        
        # Command patterns
        self._init_command_patterns()
        
        # Validation rules
        self._init_validation_rules()
    
    def _init_parameter_types(self):
        """Initialize parameter type definitions"""
        self.parameter_types = {
            'numeric': {
                'patterns': [r'(\d+\.?\d*)', r'(\d+/\d+)', r'(\d+e[+-]?\d+)'],
                'validators': ['positive', 'range', 'integer_only'],
                'converters': ['float', 'int', 'fraction']
            },
            'string': {
                'patterns': [r'"([^"]*)"', r"'([^']*)'", r'(\w+)'],
                'validators': ['non_empty', 'max_length', 'valid_characters'],
                'converters': ['lowercase', 'trim', 'sanitize']
            },
            'boolean': {
                'patterns': [r'\b(true|false|yes|no|on|off|enable|disable)\b'],
                'validators': ['boolean_only'],
                'converters': ['to_boolean']
            },
            'coordinate': {
                'patterns': [r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'],
                'validators': ['valid_3d_coordinate'],
                'converters': ['to_vector3']
            },
            'color': {
                'patterns': [r'#([0-9a-fA-F]{6})', r'rgb\((\d+),\s*(\d+),\s*(\d+)\)'],
                'validators': ['valid_color'],
                'converters': ['to_rgb', 'to_hex']
            }
        }
    
    def _init_command_patterns(self):
        """Initialize command structure patterns"""
        self.command_patterns = {
            'create_object': {
                'required_params': ['object_type'],
                'optional_params': ['position', 'scale', 'rotation', 'name'],
                'complexity_weight': 0.3
            },
            'modify_object': {
                'required_params': ['target', 'modification_type'],
                'optional_params': ['parameters', 'value'],
                'complexity_weight': 0.4
            },
            'apply_material': {
                'required_params': ['material_type'],
                'optional_params': ['target', 'properties'],
                'complexity_weight': 0.5
            },
            'lighting_setup': {
                'required_params': ['lighting_type'],
                'optional_params': ['intensity', 'color', 'position'],
                'complexity_weight': 0.6
            },
            'animation': {
                'required_params': ['animation_type', 'target'],
                'optional_params': ['duration', 'easing', 'keyframes'],
                'complexity_weight': 0.7
            }
        }
    
    def _init_validation_rules(self):
        """Initialize parameter validation rules"""
        self.validation_rules = {
            'object_type': {
                'valid_values': [
                    'cube', 'sphere', 'cylinder', 'cone', 'torus', 'plane',
                    'circle', 'uv_sphere', 'ico_sphere', 'monkey', 'text',
                    'curve', 'surface', 'metaball', 'armature', 'lattice',
                    'empty', 'camera', 'light'
                ],
                'case_sensitive': False
            },
            'material_type': {
                'valid_values': [
                    'metallic', 'dielectric', 'emission', 'glass', 'plastic',
                    'wood', 'metal', 'fabric', 'skin', 'car_paint'
                ],
                'case_sensitive': False
            },
            'lighting_type': {
                'valid_values': [
                    'sun', 'area', 'point', 'spot', 'three_point', 'studio',
                    'natural', 'dramatic', 'soft', 'hard'
                ],
                'case_sensitive': False
            },
            'numeric_range': {
                'scale': {'min': 0.001, 'max': 1000.0},
                'rotation': {'min': -360.0, 'max': 360.0},
                'subdivisions': {'min': 1, 'max': 6},
                'intensity': {'min': 0.0, 'max': 100.0},
                'roughness': {'min': 0.0, 'max': 1.0},
                'metallic': {'min': 0.0, 'max': 1.0}
            }
        }
    
    async def parse(self, nlp_result: NLPResult) -> ParsedCommand:
        """
        Parse NLP result into a structured command
        
        Args:
            nlp_result: Result from natural language processing
            
        Returns:
            ParsedCommand ready for execution
        """
        # Validate input
        if not nlp_result.intents:
            raise ValueError("No intents found in NLP result")
        
        # Select primary intent
        primary_intent = self._select_primary_intent(nlp_result.intents)
        
        # Extract and validate parameters
        parameters = await self._extract_parameters(nlp_result, primary_intent)
        
        # Determine target object
        target_object = self._determine_target_object(nlp_result, primary_intent)
        
        # Calculate execution complexity
        complexity = self._calculate_execution_complexity(nlp_result, parameters)
        
        # Determine required skills
        required_skills = self._determine_required_skills(primary_intent, parameters)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(nlp_result, parameters)
        
        # Create parsed command
        parsed_command = ParsedCommand(
            original_text=nlp_result.original_text,
            primary_intent=f"{primary_intent.action}_{primary_intent.target}",
            target_object=target_object,
            parameters=parameters,
            intents=nlp_result.intents,
            confidence=primary_intent.confidence,
            execution_complexity=complexity,
            required_skills=required_skills,
            dependencies=dependencies,
            metadata={
                'entities': nlp_result.entities,
                'sentiment': nlp_result.sentiment,
                'suggested_skills': nlp_result.suggested_skills,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return parsed_command
    
    def _select_primary_intent(self, intents: List[NLPIntent]) -> NLPIntent:
        """Select the primary intent from multiple intents"""
        if len(intents) == 1:
            return intents[0]
        
        # Sort by confidence and select highest
        sorted_intents = sorted(intents, key=lambda x: x.confidence, reverse=True)
        
        # Validate confidence threshold
        primary = sorted_intents[0]
        if primary.confidence < self.intent_confidence_threshold:
            raise ValueError(f"Primary intent confidence {primary.confidence} below threshold {self.intent_confidence_threshold}")
        
        return primary
    
    async def _extract_parameters(self, nlp_result: NLPResult, primary_intent: NLPIntent) -> Dict[str, ParsedParameter]:
        """Extract and parse parameters from NLP result"""
        parameters = {}
        
        # Start with intent parameters
        for param_name, param_value in primary_intent.parameters.items():
            parsed_param = await self._parse_parameter(param_name, param_value, nlp_result.original_text)
            parameters[param_name] = parsed_param
        
        # Extract additional parameters from entities
        entity_params = self._extract_entity_parameters(nlp_result.entities, nlp_result.original_text)
        parameters.update(entity_params)
        
        # Apply default parameters if missing
        default_params = self._apply_default_parameters(primary_intent, parameters)
        parameters.update(default_params)
        
        return parameters
    
    async def _parse_parameter(self, name: str, value: Any, text: str) -> ParsedParameter:
        """Parse a single parameter with type conversion and validation"""
        # Determine parameter type
        param_type = self._determine_parameter_type(name, value)
        
        # Convert value to appropriate type
        converted_value, confidence = self._convert_parameter_value(value, param_type, text)
        
        # Validate parameter
        validation_status = self._validate_parameter(name, converted_value, param_type)
        
        return ParsedParameter(
            name=name,
            value=converted_value,
            data_type=param_type,
            confidence=confidence,
            validation_status=validation_status
        )
    
    def _determine_parameter_type(self, name: str, value: Any) -> str:
        """Determine the appropriate type for a parameter"""
        # Check for explicit type hints in parameter name
        type_hints = {
            'count': 'numeric',
            'subdivisions': 'numeric',
            'scale': 'numeric',
            'rotation': 'numeric',
            'position': 'coordinate',
            'location': 'coordinate',
            'color': 'color',
            'name': 'string',
            'material': 'string',
            'object_type': 'string'
        }
        
        for hint, param_type in type_hints.items():
            if hint in name.lower():
                return param_type
        
        # Fallback to value-based type detection
        if isinstance(value, (int, float)):
            return 'numeric'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, str):
            # Check if string represents a coordinate
            if re.match(r'-?\d+\.?\d*,\s*-?\d+\.?\d*,\s*-?\d+\.?\d*', value):
                return 'coordinate'
            # Check if string represents a color
            elif re.match(r'#[0-9a-fA-F]{6}|rgb\(\d+,\s*\d+,\s*\d+\)', value):
                return 'color'
            else:
                return 'string'
        
        return 'string'  # Default fallback
    
    def _convert_parameter_value(self, value: Any, param_type: str, text: str) -> tuple[Any, float]:
        """Convert parameter value to appropriate type with confidence score"""
        confidence = 0.8  # Default confidence
        
        try:
            if param_type == 'numeric':
                if isinstance(value, str):
                    # Try to extract number from string
                    match = re.search(r'(\d+\.?\d*)', value)
                    if match:
                        converted = float(match.group(1))
                        # Check if it should be an integer
                        if converted.is_integer():
                            converted = int(converted)
                        return converted, confidence
                    else:
                        return 1.0, 0.3  # Default with low confidence
                return float(value), confidence
            
            elif param_type == 'coordinate':
                if isinstance(value, str):
                    match = re.match(r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)', value)
                    if match:
                        return [float(match.group(1)), float(match.group(2)), float(match.group(3))], confidence
                elif isinstance(value, (list, tuple)) and len(value) == 3:
                    return [float(v) for v in value], confidence
                return [0.0, 0.0, 0.0], 0.3  # Default with low confidence
            
            elif param_type == 'color':
                if isinstance(value, str):
                    # Handle hex colors
                    hex_match = re.match(r'#([0-9a-fA-F]{6})', value)
                    if hex_match:
                        hex_color = hex_match.group(1)
                        r = int(hex_color[0:2], 16) / 255.0
                        g = int(hex_color[2:4], 16) / 255.0
                        b = int(hex_color[4:6], 16) / 255.0
                        return [r, g, b, 1.0], confidence
                    
                    # Handle RGB colors
                    rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', value)
                    if rgb_match:
                        r = int(rgb_match.group(1)) / 255.0
                        g = int(rgb_match.group(2)) / 255.0
                        b = int(rgb_match.group(3)) / 255.0
                        return [r, g, b, 1.0], confidence
                
                return [0.8, 0.8, 0.8, 1.0], 0.3  # Default gray with low confidence
            
            elif param_type == 'boolean':
                if isinstance(value, str):
                    true_values = ['true', 'yes', 'on', 'enable', '1']
                    return value.lower() in true_values, confidence
                return bool(value), confidence
            
            else:  # string type
                return str(value), confidence
        
        except Exception:
            # Fallback to string representation with low confidence
            return str(value), 0.2
    
    def _validate_parameter(self, name: str, value: Any, param_type: str) -> str:
        """Validate a parameter value against rules"""
        if not self.parameter_validation:
            return "valid"
        
        try:
            # Check type-specific validation rules
            if param_type == 'numeric':
                if name in self.validation_rules['numeric_range']:
                    range_rule = self.validation_rules['numeric_range'][name]
                    if not (range_rule['min'] <= value <= range_rule['max']):
                        return f"invalid_range_{range_rule['min']}_{range_rule['max']}"
            
            elif param_type == 'string':
                # Check valid values
                for rule_name, rule in self.validation_rules.items():
                    if rule_name in name and 'valid_values' in rule:
                        valid_values = rule['valid_values']
                        case_sensitive = rule.get('case_sensitive', True)
                        
                        if case_sensitive:
                            if value not in valid_values:
                                return f"invalid_value_{rule_name}"
                        else:
                            if value.lower() not in [v.lower() for v in valid_values]:
                                return f"invalid_value_{rule_name}"
            
            return "valid"
        
        except Exception:
            return "validation_error"
    
    def _extract_entity_parameters(self, entities: Dict[str, List[str]], text: str) -> Dict[str, ParsedParameter]:
        """Extract parameters from entities"""
        parameters = {}
        
        # Extract numeric parameters
        if entities.get('numbers'):
            for i, number in enumerate(entities['numbers']):
                param_name = f"numeric_param_{i}"
                param = ParsedParameter(
                    name=param_name,
                    value=float(number),
                    data_type='numeric',
                    confidence=0.7
                )
                parameters[param_name] = param
        
        # Extract object parameters
        if entities.get('objects'):
            for i, obj in enumerate(entities['objects']):
                param_name = f"object_type" if i == 0 else f"object_type_{i}"
                param = ParsedParameter(
                    name=param_name,
                    value=obj,
                    data_type='string',
                    confidence=0.8
                )
                parameters[param_name] = param
        
        # Extract material parameters
        if entities.get('materials'):
            for i, material in enumerate(entities['materials']):
                param_name = f"material_type" if i == 0 else f"material_type_{i}"
                param = ParsedParameter(
                    name=param_name,
                    value=material,
                    data_type='string',
                    confidence=0.8
                )
                parameters[param_name] = param
        
        return parameters
    
    def _apply_default_parameters(self, intent: NLPIntent, existing_params: Dict[str, ParsedParameter]) -> Dict[str, ParsedParameter]:
        """Apply default parameters based on intent type"""
        defaults = {}
        intent_key = f"{intent.action}_{intent.target}"
        
        # Default parameters for common operations
        default_values = {
            'create_object': {
                'position': [0.0, 0.0, 0.0],
                'scale': [1.0, 1.0, 1.0],
                'rotation': [0.0, 0.0, 0.0]
            },
            'modify_object': {
                'apply_modifiers': False,
                'preserve_original': True
            },
            'material_object': {
                'roughness': 0.5,
                'metallic': 0.0,
                'specular': 0.5
            }
        }
        
        if intent_key in default_values:
            for param_name, default_value in default_values[intent_key].items():
                if param_name not in existing_params:
                    param_type = self._determine_parameter_type(param_name, default_value)
                    defaults[param_name] = ParsedParameter(
                        name=param_name,
                        value=default_value,
                        data_type=param_type,
                        confidence=0.5,  # Lower confidence for defaults
                        validation_status="valid"
                    )
        
        return defaults
    
    def _determine_target_object(self, nlp_result: NLPResult, primary_intent: NLPIntent) -> str:
        """Determine the target object for the command"""
        # Check if target is specified in intent
        if primary_intent.target and primary_intent.target != "object":
            return primary_intent.target
        
        # Check entities for object types
        if nlp_result.entities.get('objects'):
            return nlp_result.entities['objects'][0]
        
        # Check for selection references
        selection_keywords = ['selected', 'active', 'current', 'this', 'that']
        text_lower = nlp_result.original_text.lower()
        
        for keyword in selection_keywords:
            if keyword in text_lower:
                return "selected_object"
        
        # Default to general object
        return "object"
    
    def _calculate_execution_complexity(self, nlp_result: NLPResult, parameters: Dict[str, ParsedParameter]) -> float:
        """Calculate the complexity score for command execution"""
        complexity = 0.0
        
        # Base complexity from NLP result
        complexity += nlp_result.complexity_score * 0.4
        
        # Complexity from number of intents
        complexity += min(len(nlp_result.intents) * 0.1, 0.3)
        
        # Complexity from number of parameters
        complexity += min(len(parameters) * 0.05, 0.2)
        
        # Complexity from parameter validation issues
        invalid_params = sum(1 for p in parameters.values() if p.validation_status != "valid")
        complexity += min(invalid_params * 0.1, 0.1)
        
        return min(complexity, 1.0)
    
    def _determine_required_skills(self, primary_intent: NLPIntent, parameters: Dict[str, ParsedParameter]) -> List[str]:
        """Determine which skills are required for command execution"""
        skills = []
        
        # Map intent to skills
        intent_skill_map = {
            'create': ['modeling_primitives', 'object_creation'],
            'modify': ['mesh_editing', 'transformation'],
            'delete': ['object_management'],
            'material': ['material_creation', 'shader_nodes'],
            'lighting': ['lighting_setup', 'light_control'],
            'animation': ['keyframe_animation', 'timeline_control'],
            'camera': ['camera_control', 'viewport_management']
        }
        
        # Add skills based on action
        action = primary_intent.action.lower()
        for key, skill_list in intent_skill_map.items():
            if key in action:
                skills.extend(skill_list)
        
        # Add skills based on target
        target = primary_intent.target.lower()
        target_skill_map = {
            'cube': ['primitive_creation'],
            'sphere': ['primitive_creation'],
            'material': ['material_system'],
            'light': ['lighting_system'],
            'camera': ['camera_system']
        }
        
        for key, skill_list in target_skill_map.items():
            if key in target:
                skills.extend(skill_list)
        
        # Add skills based on parameters
        if any('subdivisions' in p.name for p in parameters.values()):
            skills.append('subdivision_surface')
        
        if any('material' in p.name for p in parameters.values()):
            skills.append('material_assignment')
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_dependencies(self, nlp_result: NLPResult, parameters: Dict[str, ParsedParameter]) -> List[str]:
        """Extract command dependencies"""
        dependencies = []
        
        # Check for object selection dependencies
        if "selected" in nlp_result.original_text.lower():
            dependencies.append("object_selection")
        
        # Check for material dependencies
        if any('material' in p.name for p in parameters.values()):
            dependencies.append("material_exists")
        
        # Check for context dependencies
        context_keywords = ['this', 'that', 'current', 'active', 'previous']
        text_lower = nlp_result.original_text.lower()
        
        for keyword in context_keywords:
            if keyword in text_lower:
                dependencies.append("context_reference")
                break
        
        return dependencies


# Utility functions
def validate_parsed_command(command: ParsedCommand) -> Dict[str, Any]:
    """Validate a parsed command and return validation report"""
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Check confidence levels
    if command.confidence < 0.6:
        report["warnings"].append(f"Low command confidence: {command.confidence}")
    
    # Check execution complexity
    if command.execution_complexity > 0.8:
        report["warnings"].append(f"High execution complexity: {command.execution_complexity}")
    
    # Check parameter validation
    invalid_params = [p for p in command.parameters.values() if p.validation_status != "valid"]
    if invalid_params:
        report["errors"].extend([f"Invalid parameter: {p.name} - {p.validation_status}" for p in invalid_params])
        report["valid"] = False
    
    # Check required skills availability
    if not command.required_skills:
        report["warnings"].append("No required skills identified")
    
    return report


if __name__ == "__main__":
    # Test the command parser
    print("Command parser module loaded successfully")
