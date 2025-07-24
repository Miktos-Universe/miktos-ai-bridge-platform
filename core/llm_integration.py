"""
LLM Integration Module for Miktos Agent

Provides enhanced natural language understanding through integration with
large language models like OpenAI GPT, Claude, and local models.
"""

import os
import re
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Optional dependency imports with fallbacks
try:
    import openai  # type: ignore
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None  # type: ignore
    OPENAI_AVAILABLE = False

try:
    import anthropic  # type: ignore
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None  # type: ignore
    ANTHROPIC_AVAILABLE = False


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    FALLBACK = "fallback"


@dataclass
class LLMResponse:
    """Response from LLM processing"""
    content: str
    confidence: float
    provider: LLMProvider
    tokens_used: int = 0
    cost: float = 0.0
    processing_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    """Manages conversation context and memory"""
    messages: List[Dict[str, str]]
    session_id: str
    timestamp: datetime
    max_history: int = 20
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if too long
        if len(self.messages) > self.max_history:
            # Keep system message and trim oldest user/assistant messages
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            self.messages = system_messages + other_messages[-(self.max_history - len(system_messages)):]


class LLMIntegration:
    """
    Enhanced LLM integration for intelligent command understanding
    and workflow automation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('LLMIntegration')
        
        # LLM configuration
        self.llm_config = config.get('llm', {})
        self.provider = LLMProvider(self.llm_config.get('provider', 'fallback'))
        
        # Initialize providers
        self._init_providers()
        
        # Conversation contexts by session
        self.contexts: Dict[str, ConversationContext] = {}
        
        # 3D-specific prompts and templates
        self._load_3d_prompts()
        
        # Usage tracking
        self.usage_stats = {
            'tokens_used': 0,
            'requests_made': 0,
            'cost_accumulated': 0.0
        }
    
    def _init_providers(self):
        """Initialize available LLM providers"""
        self.clients = {}
        
        # OpenAI
        if OPENAI_AVAILABLE and openai and self.llm_config.get('openai', {}).get('enabled', False):
            api_key = self.llm_config.get('openai', {}).get('api_key') or os.getenv('OPENAI_API_KEY')
            if api_key:
                self.clients['openai'] = openai.AsyncOpenAI(api_key=api_key)
                self.logger.info("OpenAI client initialized")
        
        # Anthropic
        if ANTHROPIC_AVAILABLE and anthropic and self.llm_config.get('anthropic', {}).get('enabled', False):
            api_key = self.llm_config.get('anthropic', {}).get('api_key') or os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.clients['anthropic'] = anthropic.AsyncAnthropic(api_key=api_key)
                self.logger.info("Anthropic client initialized")
    
    def _load_3d_prompts(self):
        """Load 3D-specific prompt templates"""
        self.system_prompts = {
            'command_understanding': """You are an expert 3D modeling assistant specialized in Blender operations. 
            Your role is to understand natural language commands and convert them into precise 3D modeling instructions.
            
            Key capabilities:
            - Create, modify, and delete 3D objects (cubes, spheres, cylinders, etc.)
            - Apply materials and textures
            - Set up lighting and cameras
            - Perform modeling operations (extrude, bevel, subdivide)
            - Manage scenes and collections
            
            Always respond with structured JSON containing:
            - intent: The primary action (create, modify, delete, select, etc.)
            - objects: List of objects involved
            - parameters: Specific parameters for the operation
            - confidence: Your confidence in the interpretation (0.0-1.0)
            - suggestions: Alternative interpretations if confidence is low
            
            Focus on precision and clarity in 3D operations.""",
            
            'workflow_generation': """You are a 3D workflow automation expert. Generate efficient workflows for complex 3D tasks.
            
            Break down complex requests into logical steps:
            1. Scene preparation
            2. Object creation/import
            3. Modeling operations
            4. Material application
            5. Lighting setup
            6. Camera positioning
            7. Rendering configuration
            
            Consider dependencies between operations and optimize for efficiency.""",
            
            'context_awareness': """You maintain awareness of the current 3D scene context. Track:
            - Currently selected objects
            - Active materials and textures
            - Lighting setup
            - Camera configuration
            - Recent operations
            
            Use this context to provide intelligent suggestions and resolve ambiguous references."""
        }
        
        self.prompt_templates = {
            'command_analysis': """
            Analyze this 3D modeling command: "{command}"
            
            Current scene context:
            {context}
            
            Provide a detailed analysis including:
            1. Primary intent and action
            2. Target objects or components
            3. Required parameters
            4. Potential ambiguities
            5. Suggested clarifications if needed
            """,
            
            'workflow_generation': """
            Generate a step-by-step workflow for: "{task}"
            
            Available skills: {skills}
            Current scene: {scene_state}
            
            Create an efficient workflow with:
            1. Clear step descriptions
            2. Required parameters for each step
            3. Dependencies between steps
            4. Estimated completion time
            5. Quality checkpoints
            """
        }
    
    async def get_context(self, session_id: str) -> ConversationContext:
        """Get or create conversation context for session"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                messages=[],
                session_id=session_id,
                timestamp=datetime.now(),
                max_history=self.llm_config.get('max_history', 20)
            )
            
            # Add system message
            self.contexts[session_id].add_message(
                "system", 
                self.system_prompts['command_understanding']
            )
        
        return self.contexts[session_id]
    
    async def enhance_command_understanding(
        self, 
        command: str, 
        context: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Use LLM to enhance command understanding beyond traditional NLP
        """
        start_time = datetime.now()
        
        try:
            conversation = await self.get_context(session_id)
            
            # Prepare the prompt with context
            prompt = self.prompt_templates['command_analysis'].format(
                command=command,
                context=json.dumps(context, indent=2)
            )
            
            # Get LLM response
            response = await self._call_llm(prompt, conversation)
            
            # Parse response for structured data
            enhanced_understanding = await self._parse_command_response(response.content)
            
            # Add to conversation history
            conversation.add_message("user", command)
            conversation.add_message("assistant", response.content)
            
            # Track usage
            self._update_usage_stats(response)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'enhanced_intent': enhanced_understanding.get('intent', 'unknown'),
                'confidence': enhanced_understanding.get('confidence', 0.5),
                'parameters': enhanced_understanding.get('parameters', {}),
                'suggestions': enhanced_understanding.get('suggestions', []),
                'objects': enhanced_understanding.get('objects', []),
                'metadata': {
                    'provider': response.provider.value,
                    'tokens_used': response.tokens_used,
                    'processing_time': processing_time,
                    'llm_response': response.content
                }
            }
            
        except Exception as e:
            self.logger.error(f"LLM command enhancement failed: {e}")
            return self._fallback_understanding(command, context)
    
    async def generate_workflow(
        self, 
        task_description: str, 
        available_skills: List[str], 
        scene_state: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Generate intelligent workflows for complex tasks
        """
        try:
            conversation = await self.get_context(session_id)
            
            prompt = self.prompt_templates['workflow_generation'].format(
                task=task_description,
                skills=', '.join(available_skills),
                scene_state=json.dumps(scene_state, indent=2)
            )
            
            response = await self._call_llm(prompt, conversation)
            workflow = await self._parse_workflow_response(response.content)
            
            conversation.add_message("user", f"Generate workflow for: {task_description}")
            conversation.add_message("assistant", response.content)
            
            self._update_usage_stats(response)
            
            return workflow
            
        except Exception as e:
            self.logger.error(f"Workflow generation failed: {e}")
            return self._fallback_workflow(task_description, available_skills)
    
    async def _call_llm(
        self, 
        prompt: str, 
        conversation: ConversationContext
    ) -> LLMResponse:
        """Call the configured LLM provider"""
        
        messages = conversation.messages + [{"role": "user", "content": prompt}]
        
        # Try primary provider
        if self.provider == LLMProvider.OPENAI and 'openai' in self.clients:
            return await self._call_openai(messages)
        elif self.provider == LLMProvider.ANTHROPIC and 'anthropic' in self.clients:
            return await self._call_anthropic(messages)
        
        # Fallback to available provider
        if 'openai' in self.clients:
            return await self._call_openai(messages)
        elif 'anthropic' in self.clients:
            return await self._call_anthropic(messages)
        
        # Final fallback
        return await self._call_fallback(prompt)
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Call OpenAI API"""
        start_time = datetime.now()
        
        response = await self.clients['openai'].chat.completions.create(
            model=self.llm_config.get('openai', {}).get('model', 'gpt-3.5-turbo'),
            messages=messages,
            max_tokens=self.llm_config.get('max_tokens', 1000),
            temperature=self.llm_config.get('temperature', 0.7)
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return LLMResponse(
            content=response.choices[0].message.content,
            confidence=0.9,  # High confidence for GPT
            provider=LLMProvider.OPENAI,
            tokens_used=response.usage.total_tokens,
            processing_time=processing_time
        )
    
    async def _call_anthropic(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Call Anthropic API"""
        start_time = datetime.now()
        
        # Convert messages for Anthropic format
        system_message = None
        conversation_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        response = await self.clients['anthropic'].messages.create(
            model=self.llm_config.get('anthropic', {}).get('model', 'claude-3-sonnet-20240229'),
            system=system_message,
            messages=conversation_messages,
            max_tokens=self.llm_config.get('max_tokens', 1000)
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return LLMResponse(
            content=response.content[0].text,
            confidence=0.9,  # High confidence for Claude
            provider=LLMProvider.ANTHROPIC,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            processing_time=processing_time
        )
    
    async def _call_fallback(self, prompt: str) -> LLMResponse:
        """Fallback response when no LLM is available"""
        return LLMResponse(
            content="LLM enhancement not available. Using basic processing.",
            confidence=0.3,
            provider=LLMProvider.FALLBACK,
            tokens_used=0,
            processing_time=0.0
        )
    
    async def _parse_command_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for command understanding"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback parsing
            return {
                'intent': 'create',
                'confidence': 0.5,
                'parameters': {},
                'suggestions': [],
                'objects': []
            }
        except:
            return {
                'intent': 'unknown',
                'confidence': 0.3,
                'parameters': {},
                'suggestions': [response],
                'objects': []
            }
    
    async def _parse_workflow_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for workflow generation"""
        try:
            # Extract structured workflow from response
            workflow_steps = []
            lines = response.split('\n')
            
            current_step = None
            for line in lines:
                if re.match(r'^\d+\.', line):  # Step number
                    if current_step:
                        workflow_steps.append(current_step)
                    current_step = {
                        'description': line.strip(),
                        'parameters': {},
                        'dependencies': [],
                        'estimated_time': 30  # Default 30 seconds
                    }
                elif current_step and line.strip():
                    # Additional details for current step
                    current_step['description'] += f" {line.strip()}"
            
            if current_step:
                workflow_steps.append(current_step)
            
            return {
                'steps': workflow_steps,
                'estimated_total_time': len(workflow_steps) * 30,
                'complexity': 'medium',
                'success_probability': 0.8
            }
            
        except Exception as e:
            self.logger.error(f"Workflow parsing failed: {e}")
            return self._fallback_workflow("", [])
    
    def _fallback_understanding(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback command understanding without LLM"""
        return {
            'enhanced_intent': 'unknown',
            'confidence': 0.3,
            'parameters': {},
            'suggestions': ['Try rephrasing your command'],
            'objects': [],
            'metadata': {
                'provider': 'fallback',
                'tokens_used': 0,
                'processing_time': 0.0
            }
        }
    
    def _fallback_workflow(self, task: str, skills: List[str]) -> Dict[str, Any]:
        """Fallback workflow generation without LLM"""
        return {
            'steps': [
                {
                    'description': f'Complete task: {task}',
                    'parameters': {},
                    'dependencies': [],
                    'estimated_time': 60
                }
            ],
            'estimated_total_time': 60,
            'complexity': 'unknown',
            'success_probability': 0.5
        }
    
    def _update_usage_stats(self, response: LLMResponse):
        """Update usage statistics"""
        self.usage_stats['tokens_used'] += response.tokens_used
        self.usage_stats['requests_made'] += 1
        self.usage_stats['cost_accumulated'] += response.cost
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self.usage_stats.copy()
    
    async def cleanup_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.contexts:
            del self.contexts[session_id]
