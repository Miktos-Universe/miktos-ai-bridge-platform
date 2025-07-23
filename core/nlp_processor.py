"""
Natural Language Processor for Miktos Agent

Handles conversion of natural language commands into structured data
that can be interpreted by the command parser.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

import spacy  # type: ignore
from transformers import pipeline, AutoTokenizer, AutoModel  # type: ignore
import torch  # type: ignore

# Local type definition - compatible with shared types
@dataclass
class NLPResult:
    """Result from natural language processing"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    context: Dict[str, Any]
    processed_text: str
    suggestions: Optional[List[str]] = None
    original_text: str = ""
    intents: Optional[List[Any]] = None  # For backward compatibility
    suggested_skills: Optional[List[str]] = None
    complexity_score: float = 0.5


@dataclass
class NLPIntent:
    """Represents an identified intent from natural language"""
    action: str  # create, modify, delete, etc.
    target: str  # object, material, light, etc.
    parameters: Dict[str, Any]
    confidence: float
    context_references: Optional[List[str]] = None


class NLPProcessor:
    """
    Advanced natural language processor for 3D commands
    Specialized for Blender operations and 3D modeling terminology
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('model', 'sentence-transformers/all-MiniLM-L6-v2')
        
        # Initialize models
        self._load_models()
        
        # 3D-specific vocabulary and patterns
        self._load_3d_vocabulary()
        
        # Command history for context
        self.command_history = []
        self.context_window = config.get('context_window', 5)
    
    def _load_models(self):
        """Load NLP models"""
        try:
            # Load spaCy model for entity recognition
            self.nlp = spacy.load("en_core_web_sm")
            
            # Load transformer model for intent classification
            self.intent_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
            
            # Load sentence transformer for similarity
            from sentence_transformers import SentenceTransformer  # type: ignore
            self.sentence_model = SentenceTransformer(self.model_name)
            
        except Exception as e:
            # Fallback to simpler models
            print(f"Failed to load advanced models: {e}")
            self._load_fallback_models()
    
    def _load_fallback_models(self):
        """Load simpler fallback models"""
        self.nlp = None
        self.intent_classifier = None
        self.sentence_model = None
    
    def _load_3d_vocabulary(self):
        """Load 3D-specific vocabulary and patterns"""
        
        # Action verbs for 3D operations
        self.action_patterns = {
            'create': [
                r'\b(create|add|make|generate|build|spawn)\b',
                r'\bnew\s+(\w+)',
                # Handle simple commands like "cube", "sphere"
                r'^(cube|sphere|cylinder|cone|torus|plane|circle|monkey)$',
                r'^create_(\w+)$',
            ],
            'modify': [
                r'\b(modify|change|alter|edit|update|adjust)\b',
                r'\b(scale|rotate|move|transform)\b',
                r'\b(subdivide|extrude|inset|bevel)\b',
            ],
            'delete': [
                r'\b(delete|remove|clear|destroy)\b',
            ],
            'select': [
                r'\b(select|choose|pick|focus)\b',
            ],
            'material': [
                r'\b(material|shader|texture)\b',
                r'\b(metallic|roughness|emission)\b',
            ],
            'lighting': [
                r'\b(light|lighting|illuminate)\b',
                r'\b(sun|area|point|spot)\s+light',
            ],
            'camera': [
                r'\b(camera|view|perspective)\b',
            ],
            'animation': [
                r'\b(animate|keyframe|timeline)\b',
            ],
            'status': [
                r'^status$',
                r'\b(status|state|info|information)\b',
            ]
        }
        
        # 3D object types
        self.object_types = {
            'primitive': ['cube', 'sphere', 'cylinder', 'plane', 'torus', 'cone'],
            'mesh': ['mesh', 'geometry', 'vertices', 'faces', 'edges'],
            'curve': ['curve', 'bezier', 'nurbs', 'path'],
            'surface': ['surface', 'nurbs surface'],
            'metaball': ['metaball', 'meta'],
            'text': ['text', 'font'],
            'armature': ['armature', 'bone', 'skeleton'],
            'lattice': ['lattice', 'deform'],
            'empty': ['empty', 'null'],
            'camera': ['camera'],
            'light': ['light', 'lamp', 'sun', 'area', 'point', 'spot'],
            'volume': ['volume', 'smoke', 'fire'],
        }
        
        # Material properties
        self.material_properties = {
            'base_color': ['color', 'base color', 'diffuse'],
            'metallic': ['metallic', 'metal'],
            'roughness': ['roughness', 'smooth', 'glossy'],
            'specular': ['specular', 'reflection'],
            'emission': ['emission', 'glow', 'emit'],
            'alpha': ['alpha', 'transparency', 'opacity'],
            'normal': ['normal', 'bump'],
            'displacement': ['displacement', 'height'],
        }
        
        # Numeric patterns
        self.numeric_patterns = [
            r'(\d+\.?\d*)\s*(times?|x)',  # "3 times", "2.5x"
            r'by\s+(\d+\.?\d*)',          # "by 2"
            r'(\d+\.?\d*)\s*(units?|blender\s*units?)',  # "5 units"
            r'(\d+\.?\d*)\s*(degrees?|°)',  # "45 degrees"
            r'(\d+\.?\d*)\s*(percent|%)',   # "50 percent"
        ]
    
    async def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> NLPResult:
        """
        Process natural language text and extract structured information
        
        Args:
            text: Input natural language text
            context: Additional context information
            
        Returns:
            NLPResult with structured data
        """
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Extract entities
        entities = self._extract_entities(cleaned_text)
        
        # Identify intents
        intents = await self._identify_intents(cleaned_text, entities, context)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(cleaned_text)
        
        # Calculate complexity
        complexity = self._calculate_complexity(cleaned_text, intents)
        
        # Suggest relevant skills
        suggested_skills = await self._suggest_skills(intents, entities)
        
        # Extract primary intent (use first intent or default)
        primary_intent = intents[0].action if intents else "unknown"
        
        # Calculate overall confidence (average of intent confidences)
        overall_confidence = sum(intent.confidence for intent in intents) / len(intents) if intents else 0.0
        
        result = NLPResult(
            intent=primary_intent,
            entities=entities,
            confidence=overall_confidence,
            context=context or {},
            processed_text=cleaned_text,
            suggestions=suggested_skills
        )
        
        # Update command history for context
        self.command_history.append(result)
        if len(self.command_history) > self.context_window:
            self.command_history.pop(0)
        
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common abbreviations
        abbreviations = {
            'w/': 'with',
            'wo/': 'without',
            '3d': 'three dimensional',
            'uv': 'uv mapping',
            'pbr': 'physically based rendering',
        }
        
        for abbrev, full in abbreviations.items():
            text = text.replace(abbrev, full)
        
        return text
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using patterns and NLP"""
        entities = {
            'objects': [],
            'materials': [],
            'properties': [],
            'numbers': [],
            'actions': [],
        }
        
        # Extract object types
        for category, objects in self.object_types.items():
            for obj in objects:
                if obj in text:
                    entities['objects'].append(obj)
        
        # Extract material properties
        for prop_type, properties in self.material_properties.items():
            for prop in properties:
                if prop in text:
                    entities['materials'].append(prop_type)
        
        # Extract numbers
        for pattern in self.numeric_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    entities['numbers'].append(match[0])
                else:
                    entities['numbers'].append(match)
        
        # Extract actions
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    entities['actions'].append(action)
        
        # Use spaCy if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['CARDINAL', 'QUANTITY']:
                    entities['numbers'].append(ent.text)
        
        return entities
    
    async def _identify_intents(self, text: str, entities: Dict[str, List[str]], context: Optional[Dict[str, Any]] = None) -> List[NLPIntent]:
        """Identify intents from text and entities"""
        intents = []
        
        # Pattern-based intent recognition
        for action in entities.get('actions', []):
            intent = self._create_intent_from_action(action, text, entities)
            if intent:
                intents.append(intent)
        
        # If no clear intents found, try to infer from context
        if not intents:
            intents = self._infer_intents_from_context(text, entities, context)
        
        return intents
    
    def _create_intent_from_action(self, action: str, text: str, entities: Dict[str, List[str]]) -> Optional[NLPIntent]:
        """Create intent from identified action"""
        
        # Handle special cases for simple commands
        text_lower = text.lower().strip()
        
        # Direct operation name mapping
        if text_lower.startswith('create_'):
            operation_name = text_lower
            object_type = text_lower.replace('create_', '')
            return NLPIntent(
                action="create",
                target=object_type,
                parameters={"operation": operation_name},
                confidence=0.9
            )
        
        # Simple object creation commands
        simple_objects = ['cube', 'sphere', 'cylinder', 'cone', 'torus', 'plane', 'circle', 'monkey']
        if text_lower in simple_objects:
            return NLPIntent(
                action="create",
                target=text_lower,
                parameters={"operation": f"create_{text_lower}"},
                confidence=0.9
            )
        
        # Status command
        if text_lower == 'status':
            return NLPIntent(
                action="status",
                target="platform",
                parameters={},
                confidence=1.0
            )
        
        # Determine target
        target = "object"  # default
        if entities.get('objects'):
            target = entities['objects'][0]
        elif 'material' in entities.get('actions', []):
            target = "material"
        elif 'lighting' in entities.get('actions', []):
            target = "light"
        
        # Extract parameters
        parameters = {}
        
        # Add numeric parameters
        if entities.get('numbers'):
            if 'subdivide' in text:
                parameters['subdivisions'] = int(float(entities['numbers'][0]))
            elif 'scale' in text:
                parameters['scale_factor'] = float(entities['numbers'][0])
            elif 'rotate' in text:
                parameters['rotation_degrees'] = float(entities['numbers'][0])
        
        # Add material parameters
        if entities.get('materials'):
            for material_prop in entities['materials']:
                parameters[material_prop] = self._extract_material_value(material_prop, text)
        
        # Simple confidence scoring
        confidence = 0.8 if entities.get('objects') or entities.get('materials') else 0.6
        
        return NLPIntent(
            action=action,
            target=target,
            parameters=parameters,
            confidence=confidence
        )
    
    def _extract_material_value(self, property_name: str, text: str) -> Any:
        """Extract material property values from text"""
        # Look for numbers near the property
        property_patterns = {
            'metallic': r'metallic\s*(\d*\.?\d+)',
            'roughness': r'roughness\s*(\d*\.?\d+)',
            'emission': r'emission\s*(\d*\.?\d+)',
        }
        
        if property_name in property_patterns:
            match = re.search(property_patterns[property_name], text)
            if match:
                return float(match.group(1))
        
        # Default values for common properties
        defaults = {
            'metallic': 0.0,
            'roughness': 0.5,
            'emission': 0.0,
            'base_color': [0.8, 0.8, 0.8, 1.0],
        }
        
        return defaults.get(property_name, 1.0)
    
    def _infer_intents_from_context(self, text: str, entities: Dict[str, List[str]], context: Optional[Dict[str, Any]] = None) -> List[NLPIntent]:
        """Infer intents when no clear action is found"""
        intents = []
        
        # If objects are mentioned without action, assume creation
        if entities.get('objects') and not entities.get('actions'):
            intent = NLPIntent(
                action='create',
                target=entities['objects'][0],
                parameters={},
                confidence=0.5
            )
            intents.append(intent)
        
        return intents
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of the command (for user experience)"""
        # Simple keyword-based sentiment
        positive_words = ['good', 'great', 'awesome', 'perfect', 'excellent']
        negative_words = ['bad', 'terrible', 'wrong', 'awful', 'horrible']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count + negative_count == 0:
            return 0.0  # Neutral
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _calculate_complexity(self, text: str, intents: List[NLPIntent]) -> float:
        """Calculate complexity score of the command"""
        complexity = 0.0
        
        # Base complexity from text length
        complexity += min(len(text.split()) / 20.0, 0.3)
        
        # Complexity from number of intents
        complexity += min(len(intents) / 5.0, 0.3)
        
        # Complexity from parameter count
        total_params = sum(len(intent.parameters) for intent in intents)
        complexity += min(total_params / 10.0, 0.4)
        
        return min(complexity, 1.0)
    
    async def _suggest_skills(self, intents: List[NLPIntent], entities: Dict[str, List[str]]) -> List[str]:
        """Suggest relevant skills based on intents and entities"""
        suggested_skills = []
        
        for intent in intents:
            skill_category = f"{intent.action}_{intent.target}"
            suggested_skills.append(skill_category)
            
            # Add specific skills based on parameters
            if intent.target == 'object' and intent.action == 'create':
                if entities.get('objects'):
                    obj_type = entities['objects'][0]
                    suggested_skills.append(f"create_{obj_type}")
            
            if intent.target == 'material':
                suggested_skills.extend([
                    'material_pbr',
                    'material_nodes',
                    'texture_mapping'
                ])
            
            if intent.target == 'light':
                suggested_skills.extend([
                    'lighting_setup',
                    'light_positioning',
                    'shadow_control'
                ])
        
        return list(set(suggested_skills))  # Remove duplicates
    
    async def get_suggestions(self, partial_text: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = []
        
        # Common command patterns
        common_patterns = [
            "Create a {object}",
            "Add a {material} material",
            "Set up {lighting} lighting",
            "Delete the selected object",
            "Scale by {factor}",
            "Rotate {degrees} degrees",
            "Subdivide {times} times",
        ]
        
        # Fill in patterns based on partial text
        for pattern in common_patterns:
            if any(word in partial_text.lower() for word in pattern.lower().split()):
                # Try to complete the pattern
                completed = self._complete_pattern(pattern, partial_text)
                if completed:
                    suggestions.append(completed)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _complete_pattern(self, pattern: str, partial_text: str) -> Optional[str]:
        """Complete a pattern based on partial text"""
        # Simple pattern completion
        placeholders = {
            '{object}': ['cube', 'sphere', 'cylinder', 'plane'],
            '{material}': ['metallic', 'glass', 'plastic', 'wood'],
            '{lighting}': ['three-point', 'studio', 'outdoor'],
            '{factor}': ['2', '0.5', '1.5'],
            '{degrees}': ['90', '45', '180'],
            '{times}': ['2', '3', '4'],
        }
        
        for placeholder, options in placeholders.items():
            if placeholder in pattern:
                for option in options:
                    if option in partial_text.lower():
                        return pattern.replace(placeholder, option)
                # Return first option if no match
                return pattern.replace(placeholder, options[0])
        
        return pattern


# Utility functions
def preprocess_command(text: str) -> str:
    """Preprocess command text for better recognition"""
    # Handle common shortcuts
    shortcuts = {
        'sub': 'subdivide',
        'mat': 'material',
        'obj': 'object',
        'del': 'delete',
        'rot': 'rotate',
        'pos': 'position',
        'loc': 'location',
    }
    
    words = text.lower().split()
    processed_words = []
    
    for word in words:
        processed_words.append(shortcuts.get(word, word))
    
    return ' '.join(processed_words)


if __name__ == "__main__":
    # Test the NLP processor
    async def test_nlp():
        config = {'context_window': 5}
        processor = NLPProcessor(config)
        
        test_commands = [
            "Create a cube and subdivide it 3 times",
            "Add a metallic material with 0.1 roughness",
            "Delete the selected object",
            "Set up three-point lighting",
            "Scale the object by 2",
        ]
        
        for command in test_commands:
            result = await processor.process(command)
            print(f"Command: {command}")
            print(f"Intents: {[f'{i.action}_{i.target}' for i in result.intents] if result.intents else ['No intents']}")
            print(f"Entities: {result.entities}")
            print(f"Suggested Skills: {result.suggested_skills or 'None'}")
            print("---")
    
    asyncio.run(test_nlp())
