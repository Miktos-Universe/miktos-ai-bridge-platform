# 📡 Miktos AI Bridge Platform - API Reference

## Complete Developer Reference for AI-Powered 3D Automation

This comprehensive API reference provides complete documentation for integrating with and extending the Miktos AI Bridge Platform.

---

## 📋 Table of Contents

1. [Python SDK](#-python-sdk)
2. [REST API](#-rest-api)
3. [WebSocket API](#-websocket-api)
4. [Skills API](#️-skills-api)
5. [Agent Integration](#-agent-integration)
6. [Authentication](#-authentication)
7. [Error Handling](#️-error-handling)
8. [Rate Limiting](#-rate-limiting)

---

## 🐍 Python SDK

### Installation

```bash
pip install miktos-sdk
```

### Basic Usage

```python
from miktos import MiktosAgent, SkillManager
from miktos.core import LLMIntegration, PerformanceMonitor

# Initialize the agent
agent = MiktosAgent(
    config_path="config.yaml",
    auto_optimize=True
)

# Execute commands
result = agent.execute("create metallic cube with size 2x2x2")
print(f"✅ {result.message}")
```

### MiktosAgent Class

#### Constructor

```python
class MiktosAgent:
    def __init__(
        self,
        config_path: Optional[str] = None,
        blender_path: Optional[str] = None,
        auto_optimize: bool = True,
        performance_targets: Optional[Dict] = None
    )
```

**Parameters:**

- `config_path`: Path to YAML configuration file
- `blender_path`: Path to Blender executable
- `auto_optimize`: Enable automatic performance optimization
- `performance_targets`: Custom performance target overrides

#### Core Methods

##### execute()

```python
def execute(
    self,
    command: str,
    context: Optional[Dict] = None,
    session_id: Optional[str] = None
) -> ExecutionResult
```

Execute a natural language command.

**Parameters:**

- `command`: Natural language command string
- `context`: Optional context dictionary
- `session_id`: Session identifier for context continuity

**Returns:** `ExecutionResult` object with execution details

**Example:**

```python
result = agent.execute("create sphere with radius 3")
if result.success:
    print(f"Created object: {result.object_name}")
    print(f"Execution time: {result.execution_time}s")
```

##### execute_batch()

```python
def execute_batch(
    self,
    commands: List[str],
    parallel: bool = False,
    continue_on_error: bool = True
) -> List[ExecutionResult]
```

Execute multiple commands in sequence or parallel.

**Example:**

```python
commands = [
    "create cube",
    "add metallic material",
    "scale 2x"
]
results = agent.execute_batch(commands, parallel=False)
```

##### generate_workflow()

```python
def generate_workflow(
    self,
    description: str,
    complexity: str = "medium",
    output_format: str = "yaml"
) -> Workflow
```

Generate automated workflow from description.

**Example:**

```python
workflow = agent.generate_workflow(
    "Create product photography scene with lighting",
    complexity="advanced"
)
workflow.execute()
```

#### Scene Management

##### get_scene_info()

```python
def get_scene_info(self) -> SceneInfo
```

Get comprehensive scene information.

**Returns:**

```python
@dataclass
class SceneInfo:
    object_count: int
    material_count: int
    light_count: int
    camera_count: int
    scene_bounds: Tuple[float, float, float]
    memory_usage: float
    render_time_estimate: float
```

##### save_scene()

```python
def save_scene(
    self,
    filename: str,
    format: str = "blend",
    include_materials: bool = True
) -> bool
```

Save current scene to file.

##### load_scene()

```python
def load_scene(
    self,
    filename: str,
    merge: bool = False,
    replace_current: bool = True
) -> bool
```

Load scene from file.

#### Performance Management

##### get_performance_stats()

```python
def get_performance_stats(self) -> PerformanceStats
```

Get real-time performance statistics.

**Returns:**

```python
@dataclass
class PerformanceStats:
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    cache_hit_rate: float
    average_execution_time: float
    workflow_success_rate: float
```

##### optimize_performance()

```python
def optimize_performance(
    self,
    strategy: str = "balanced",
    target_time: float = 60.0
) -> OptimizationResult
```

Optimize platform performance.

**Strategies:**

- `"conservative"`: Minimal optimizations, maximum stability
- `"balanced"`: Optimal performance/stability balance
- `"aggressive"`: Maximum performance optimizations

### SkillManager Class

#### SkillManager Methods

##### list_skills()

```python
def list_skills(
    self,
    category: Optional[str] = None,
    difficulty: Optional[str] = None
) -> List[SkillInfo]
```

List available skills.

**Example:**

```python
skills = skill_manager.list_skills(category="modeling")
for skill in skills:
    print(f"{skill.name}: {skill.description}")
```

##### execute_skill()

```python
def execute_skill(
    self,
    skill_name: str,
    parameters: Dict[str, Any],
    context: Optional[Dict] = None
) -> SkillResult
```

Execute skill directly with parameters.

**Example:**

```python
result = skill_manager.execute_skill("create_cube", {
    "size": [2, 2, 2],
    "location": [0, 0, 0],
    "material": "metallic"
})
```

##### register_skill()

```python
def register_skill(
    self,
    name: str,
    function: Callable,
    category: str,
    description: str,
    parameters_schema: Dict
) -> bool
```

Register custom skill.

**Example:**

```python
def custom_modeling_skill(params):
    # Skill implementation
    return SkillResult(success=True, message="Custom skill executed")

skill_manager.register_skill(
    name="custom_modeling",
    function=custom_modeling_skill,
    category="modeling",
    description="Custom modeling operation",
    parameters_schema={
        "type": "object",
        "properties": {
            "complexity": {"type": "string", "enum": ["simple", "complex"]}
        }
    }
)
```

### LLMIntegration Class

#### LLMIntegration Configuration

```python
llm = LLMIntegration(
    model="gpt-4",
    api_key="your-api-key",
    max_tokens=4000,
    temperature=0.1
)
```

#### LLMIntegration Methods

##### process_command()

```python
def process_command(
    self,
    command: str,
    context: Optional[Dict] = None
) -> CommandInterpretation
```

##### generate_workflow_definition()

```python
def generate_workflow(
    self,
    description: str,
    constraints: Optional[Dict] = None
) -> WorkflowDefinition
```

---

## 🌐 REST API

### Base URL

```text
http://localhost:8000/api/v1
```

### Authentication

Include API key in header:

```bash
Authorization: Bearer your-api-key
```

### Core Endpoints

#### Execute Command

```http
POST /execute
Content-Type: application/json

{
  "command": "create metallic cube with size 2x2x2",
  "session_id": "session_123",
  "context": {
    "user_preferences": {
      "units": "metric"
    }
  }
}
```

**Response:**

```json
{
  "success": true,
  "execution_id": "exec_456",
  "result": {
    "message": "Created metallic cube successfully",
    "object_name": "Cube.001",
    "execution_time": 1.23,
    "scene_updated": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Execute Batch Commands

```http
POST /execute/batch
Content-Type: application/json

{
  "commands": [
    "create cube",
    "add metallic material",
    "scale 2x"
  ],
  "parallel": false,
  "continue_on_error": true,
  "session_id": "session_123"
}
```

#### Generate Workflow

```http
POST /workflow/generate
Content-Type: application/json

{
  "description": "Create product photography scene with professional lighting",
  "complexity": "advanced",
  "parameters": {
    "style": "modern",
    "lighting_type": "studio"
  }
}
```

**Response:**

```json
{
  "workflow_id": "workflow_789",
  "name": "Product Photography Scene",
  "steps": [
    {
      "step": 1,
      "command": "create plane with size 10x10",
      "description": "Create background surface"
    },
    {
      "step": 2,
      "command": "set up three-point lighting",
      "description": "Professional lighting setup"
    }
  ],
  "estimated_time": 45.0,
  "difficulty": "advanced"
}
```

#### Execute Workflow

```http
POST /workflow/{workflow_id}/execute
Content-Type: application/json

{
  "parameters": {
    "background_color": "white",
    "product_size": "medium"
  }
}
```

#### Scene Information

```http
GET /scene/info
```

**Response:**

```json
{
  "scene_id": "scene_abc",
  "object_count": 15,
  "material_count": 8,
  "light_count": 3,
  "camera_count": 1,
  "scene_bounds": {
    "min": [-5.0, -5.0, 0.0],
    "max": [5.0, 5.0, 10.0]
  },
  "memory_usage": 245.7,
  "render_stats": {
    "estimated_time": 120.5,
    "complexity": "medium"
  }
}
```

#### Performance Statistics

```http
GET /performance/stats
```

**Response:**

```json
{
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "gpu_usage": 23.1,
  "cache_hit_rate": 0.85,
  "average_execution_time": 2.1,
  "workflow_success_rate": 0.97,
  "uptime": 86400,
  "requests_processed": 1543
}
```

#### Skills Management

```http
GET /skills
GET /skills?category=modeling
GET /skills?difficulty=beginner

POST /skills/{skill_name}/execute
{
  "parameters": {
    "size": [2, 2, 2],
    "material": "metallic"
  }
}
```

### File Operations

#### Upload Scene

```http
POST /scene/upload
Content-Type: multipart/form-data

file: scene.blend
```

#### Download Scene

```http
GET /scene/download?format=blend
GET /scene/download?format=fbx
```

#### Export Render

```http
POST /render/export
Content-Type: application/json

{
  "format": "png",
  "resolution": [1920, 1080],
  "quality": "high",
  "output_path": "/renders/output.png"
}
```

---

## 🔌 WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Message Format

```json
{
  "type": "command_type",
  "data": { },
  "id": "unique_message_id"
}
```

### Message Types

#### Execute Command via WebSocket

```json
{
  "type": "execute",
  "data": {
    "command": "create cube",
    "session_id": "session_123"
  },
  "id": "msg_001"
}
```

#### Subscribe to Updates

```json
{
  "type": "subscribe",
  "data": {
    "events": ["scene_update", "performance_update", "execution_complete"]
  },
  "id": "msg_002"
}
```

#### Real-time Scene Updates

```json
{
  "type": "scene_update",
  "data": {
    "object_added": {
      "name": "Cube.001",
      "type": "MESH",
      "location": [0, 0, 0]
    },
    "scene_stats": {
      "object_count": 16,
      "memory_usage": 248.3
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Performance Updates

```json
{
  "type": "performance_update",
  "data": {
    "cpu_usage": 48.5,
    "memory_usage": 71.2,
    "cache_hit_rate": 0.87
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### JavaScript Client Example

```javascript
class MiktosWebSocketClient {
    constructor(url = 'ws://localhost:8000/ws') {
        this.ws = new WebSocket(url);
        this.messageId = 0;
        this.callbacks = new Map();
        
        this.ws.onmessage = this.handleMessage.bind(this);
    }
    
    send(type, data) {
        const id = ++this.messageId;
        const message = { type, data, id: `msg_${id}` };
        this.ws.send(JSON.stringify(message));
        return id;
    }
    
    execute(command, sessionId = null) {
        return this.send('execute', { command, session_id: sessionId });
    }
    
    subscribe(events) {
        return this.send('subscribe', { events });
    }
    
    handleMessage(event) {
        const message = JSON.parse(event.data);
        console.log('Received:', message);
        
        if (this.callbacks.has(message.type)) {
            this.callbacks.get(message.type)(message.data);
        }
    }
    
    on(eventType, callback) {
        this.callbacks.set(eventType, callback);
    }
}

// Usage
const client = new MiktosWebSocketClient();

client.on('scene_update', (data) => {
    console.log('Scene updated:', data);
});

client.on('execution_complete', (data) => {
    console.log('Command completed:', data);
});

client.subscribe(['scene_update', 'execution_complete']);
client.execute('create metallic cube');
```

---

## 🛠️ Skills API

### Skill Structure

```python
from miktos.skills import BaseSkill, SkillParameter

class CustomModelingSkill(BaseSkill):
    name = "custom_modeling"
    category = "modeling"
    description = "Custom 3D modeling operations"
    difficulty = "intermediate"
    
    parameters = [
        SkillParameter(
            name="object_type",
            type="string",
            description="Type of object to create",
            required=True,
            choices=["cube", "sphere", "cylinder"]
        ),
        SkillParameter(
            name="size",
            type="array",
            description="Object size [x, y, z]",
            default=[1, 1, 1]
        ),
        SkillParameter(
            name="material_type",
            type="string",
            description="Material to apply",
            choices=["metallic", "glass", "wood", "plastic"]
        )
    ]
    
    def execute(self, params: Dict[str, Any]) -> SkillResult:
        try:
            # Skill implementation
            object_type = params["object_type"]
            size = params.get("size", [1, 1, 1])
            material = params.get("material_type")
            
            # Create object
            obj_name = self.create_object(object_type, size)
            
            # Apply material if specified
            if material:
                self.apply_material(obj_name, material)
            
            return SkillResult(
                success=True,
                message=f"Created {object_type} with {material} material",
                data={
                    "object_name": obj_name,
                    "object_type": object_type,
                    "size": size,
                    "material": material
                }
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e),
                message=f"Failed to create {object_type}"
            )
    
    def create_object(self, obj_type: str, size: List[float]) -> str:
        # Blender API calls
        pass
    
    def apply_material(self, obj_name: str, material_type: str):
        # Material application logic
        pass
```

### Skill Registration

```python
# Register skill
skill_manager.register_skill(CustomModelingSkill())

# Verify registration
skills = skill_manager.list_skills(category="modeling")
print(f"Found {len(skills)} modeling skills")
```

### Built-in Skills

#### Modeling Skills

- `create_primitive`: Create basic primitives (cube, sphere, etc.)
- `boolean_operation`: Perform boolean operations
- `subdivision_surface`: Apply subdivision surface modifier
- `extrude_faces`: Extrude selected faces
- `bevel_edges`: Bevel selected edges

#### Material Skills

- `create_pbr_material`: Create PBR material
- `apply_texture`: Apply texture to material
- `create_procedural_material`: Generate procedural materials
- `material_node_setup`: Advanced node-based materials

#### Lighting Skills

- `setup_three_point_lighting`: Professional lighting setup
- `create_hdri_environment`: HDRI environment lighting
- `add_area_light`: Add area light with parameters
- `studio_lighting_setup`: Studio lighting configuration

#### Animation Skills

- `keyframe_animation`: Create keyframe animations
- `path_animation`: Animate objects along paths
- `camera_flythrough`: Create camera animations
- `material_animation`: Animate material properties

#### Rendering Skills

- `render_still`: Render single frame
- `render_animation`: Render animation sequence
- `setup_render_settings`: Configure render parameters
- `batch_render`: Batch rendering operations

---

## 🤖 Agent Integration

### Custom Agent Development

```python
from miktos.agent import BaseAgent, AgentCapability

class CustomAgent(BaseAgent):
    name = "ArchitecturalAgent"
    description = "Specialized agent for architectural workflows"
    
    capabilities = [
        AgentCapability.NATURAL_LANGUAGE_PROCESSING,
        AgentCapability.WORKFLOW_GENERATION,
        AgentCapability.PERFORMANCE_OPTIMIZATION
    ]
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.architectural_library = self.load_architectural_library()
    
    def process_command(self, command: str) -> CommandInterpretation:
        # Custom command processing logic
        interpretation = super().process_command(command)
        
        # Add architectural-specific processing
        if self.is_architectural_command(command):
            interpretation = self.enhance_architectural_interpretation(interpretation)
        
        return interpretation
    
    def generate_workflow(self, description: str) -> Workflow:
        # Custom workflow generation for architectural tasks
        base_workflow = super().generate_workflow(description)
        
        if self.is_architectural_workflow(description):
            base_workflow = self.add_architectural_steps(base_workflow)
        
        return base_workflow
    
    def is_architectural_command(self, command: str) -> bool:
        architectural_keywords = ["building", "house", "room", "floor", "wall", "door", "window"]
        return any(keyword in command.lower() for keyword in architectural_keywords)
```

### Agent Registration

```python
# Register custom agent
agent_manager.register_agent(CustomAgent)

# Use specific agent
architectural_agent = agent_manager.get_agent("ArchitecturalAgent")
result = architectural_agent.execute("create modern house layout")
```

---

## 🔐 Authentication

### API Key Authentication

#### Generating API Keys

```bash
# Generate new API key
python -m miktos.auth generate-key --name "production_client" --permissions "execute,read,write"

# List API keys
python -m miktos.auth list-keys

# Revoke API key
python -m miktos.auth revoke-key --key "your-api-key"
```

#### Using API Keys

**Python SDK:**

```python
agent = MiktosAgent(api_key="your-api-key")
```

**REST API:**

```bash
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"command": "create cube"}' \
     http://localhost:8000/api/v1/execute
```

### OAuth 2.0 Integration

```python
from miktos.auth import OAuthProvider

# Configure OAuth
oauth = OAuthProvider(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8080/callback"
)

# Generate authorization URL
auth_url = oauth.get_authorization_url()
print(f"Authorize at: {auth_url}")

# Exchange code for token
token = oauth.exchange_code(authorization_code)
agent = MiktosAgent(oauth_token=token)
```

### JWT Token Authentication

```python
from miktos.auth import JWTAuth

# Create JWT token
jwt_auth = JWTAuth(secret_key="your-secret-key")
token = jwt_auth.create_token(
    user_id="user_123",
    permissions=["execute", "read"],
    expires_in=3600
)

# Use JWT token
agent = MiktosAgent(jwt_token=token)
```

---

## ⚠️ Error Handling

### Error Types

```python
from miktos.exceptions import (
    MiktosError,
    CommandParsingError,
    SkillExecutionError,
    BlenderIntegrationError,
    PerformanceError,
    AuthenticationError
)

try:
    result = agent.execute("invalid command syntax")
except CommandParsingError as e:
    print(f"Command parsing failed: {e.message}")
    print(f"Suggestion: {e.suggestion}")
except SkillExecutionError as e:
    print(f"Skill execution failed: {e.skill_name}")
    print(f"Error: {e.error_details}")
except BlenderIntegrationError as e:
    print(f"Blender integration error: {e.blender_error}")
except MiktosError as e:
    print(f"General Miktos error: {e}")
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "type": "CommandParsingError",
    "code": "INVALID_SYNTAX",
    "message": "Unable to parse command: 'invalid command syntax'",
    "details": {
      "command": "invalid command syntax",
      "error_position": 8,
      "suggestion": "Try: 'create cube' or 'add material metallic'"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123"
  }
}
```

### Retry Logic

```python
from miktos.utils import retry_with_backoff

@retry_with_backoff(max_retries=3, backoff_factor=1.5)
def execute_with_retry(agent, command):
    return agent.execute(command)

# Usage
try:
    result = execute_with_retry(agent, "create complex scene")
except Exception as e:
    print(f"Command failed after retries: {e}")
```

---

## 🚦 Rate Limiting

### Rate Limiting Configuration

```yaml
# config.yaml
rate_limiting:
  enabled: true
  requests_per_minute: 100
  burst_size: 10
  per_user_limit: 50
  
  # Different limits for different endpoints
  endpoints:
    "/api/v1/execute":
      requests_per_minute: 60
      burst_size: 5
    "/api/v1/workflow/generate":
      requests_per_minute: 20
      burst_size: 2
```

### Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643097600
X-RateLimit-Retry-After: 60
```

### Handling Rate Limits

```python
import time
from miktos.exceptions import RateLimitError

def execute_with_rate_limit_handling(agent, command):
    try:
        return agent.execute(command)
    except RateLimitError as e:
        print(f"Rate limited. Waiting {e.retry_after} seconds...")
        time.sleep(e.retry_after)
        return agent.execute(command)  # Retry after wait
```

---

## 📊 Performance Monitoring

### Metrics Collection

```python
from miktos.monitoring import MetricsCollector

metrics = MetricsCollector()

# Collect execution metrics
with metrics.measure_execution("create_cube"):
    result = agent.execute("create cube")

# Get collected metrics
stats = metrics.get_stats()
print(f"Average execution time: {stats.avg_execution_time}s")
print(f"Success rate: {stats.success_rate}%")
```

### Custom Metrics

```python
# Register custom metric
metrics.register_counter("custom_operations")
metrics.register_histogram("workflow_complexity")

# Record metrics
metrics.increment("custom_operations")
metrics.record("workflow_complexity", complexity_score)
```

---

## 🧪 Testing

### Unit Tests

```python
import unittest
from miktos.testing import MiktosTestCase

class TestCustomSkill(MiktosTestCase):
    def setUp(self):
        self.agent = self.create_test_agent()
        self.skill_manager = self.agent.skill_manager
    
    def test_create_cube(self):
        result = self.agent.execute("create cube")
        self.assertTrue(result.success)
        self.assertIn("cube", result.object_name.lower())
    
    def test_skill_execution(self):
        result = self.skill_manager.execute_skill("create_cube", {
            "size": [2, 2, 2]
        })
        self.assertTrue(result.success)
        self.assertEqual(result.data["size"], [2, 2, 2])
```

### Integration Tests

```python
from miktos.testing import IntegrationTestSuite

class WorkflowIntegrationTest(IntegrationTestSuite):
    def test_complete_workflow(self):
        workflow = self.agent.generate_workflow("create product scene")
        result = workflow.execute()
        
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.objects_created, 3)
        self.assertLessEqual(result.execution_time, 60.0)
```

---

## 📝 Examples

### Complete Workflow Example

```python
from miktos import MiktosAgent
import json

# Initialize agent
agent = MiktosAgent(config_path="config.yaml")

# Create complex scene
commands = [
    "create plane with size 10x10 as background",
    "create sphere with radius 2 at position 0,0,2",
    "add metallic material to sphere",
    "create three-point lighting setup",
    "add camera for product photography",
    "render scene with high quality"
]

results = []
for command in commands:
    result = agent.execute(command)
    results.append({
        "command": command,
        "success": result.success,
        "execution_time": result.execution_time,
        "message": result.message
    })

# Save results
with open("workflow_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ Workflow completed successfully!")
```

### Custom Skill Development

```python
from miktos.skills import BaseSkill, SkillResult

class TerrainGeneratorSkill(BaseSkill):
    name = "generate_terrain"
    category = "procedural"
    description = "Generate procedural terrain"
    
    def execute(self, params):
        size = params.get("size", [10, 10])
        detail = params.get("detail_level", 5)
        noise_scale = params.get("noise_scale", 1.0)
        
        # Generate terrain using Blender API
        terrain_name = self.create_terrain_mesh(size, detail, noise_scale)
        
        return SkillResult(
            success=True,
            message=f"Generated terrain with {detail} detail levels",
            data={
                "terrain_name": terrain_name,
                "size": size,
                "detail_level": detail
            }
        )

# Register and use
agent.skill_manager.register_skill(TerrainGeneratorSkill())
result = agent.execute("generate terrain with high detail")
```

---

## 🔗 External Integrations

### Blender Add-on Integration

```python
# Blender add-on integration
import bpy
from miktos.blender import BlenderMiktosAddon

class MiktosBlenderPanel(bpy.types.Panel):
    bl_label = "Miktos AI"
    bl_idname = "VIEW3D_PT_miktos"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Miktos"
    
    def draw(self, context):
        layout = self.layout
        
        # Command input
        layout.prop(context.scene, "miktos_command")
        layout.operator("miktos.execute_command", text="Execute")
        
        # Status display
        if hasattr(context.scene, "miktos_last_result"):
            layout.label(text=f"Result: {context.scene.miktos_last_result}")

def register():
    bpy.utils.register_class(MiktosBlenderPanel)
    bpy.types.Scene.miktos_command = bpy.props.StringProperty(name="Command")

def unregister():
    bpy.utils.unregister_class(MiktosBlenderPanel)
    del bpy.types.Scene.miktos_command
```

### Web Integration

```javascript
// React component example
import React, { useState, useEffect } from 'react';
import { MiktosClient } from 'miktos-web-client';

function MiktosInterface() {
    const [client] = useState(new MiktosClient('http://localhost:8000'));
    const [command, setCommand] = useState('');
    const [result, setResult] = useState(null);
    const [sceneInfo, setSceneInfo] = useState(null);
    
    useEffect(() => {
        // Subscribe to scene updates
        client.subscribe('scene_update', (data) => {
            setSceneInfo(data);
        });
    }, [client]);
    
    const executeCommand = async () => {
        try {
            const result = await client.execute(command);
            setResult(result);
            setCommand('');
        } catch (error) {
            setResult({ success: false, error: error.message });
        }
    };
    
    return (
        <div className="miktos-interface">
            <div className="command-input">
                <input
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="Enter Miktos command..."
                    onKeyPress={(e) => e.key === 'Enter' && executeCommand()}
                />
                <button onClick={executeCommand}>Execute</button>
            </div>
            
            {result && (
                <div className={`result ${result.success ? 'success' : 'error'}`}>
                    {result.message || result.error}
                </div>
            )}
            
            {sceneInfo && (
                <div className="scene-info">
                    <h3>Scene Information</h3>
                    <p>Objects: {sceneInfo.object_count}</p>
                    <p>Materials: {sceneInfo.material_count}</p>
                    <p>Memory: {sceneInfo.memory_usage}MB</p>
                </div>
            )}
        </div>
    );
}

export default MiktosInterface;
```

---

This comprehensive API reference provides complete documentation for integrating with and extending the Miktos AI Bridge Platform. For additional examples and advanced usage patterns, visit the [complete documentation](https://docs.miktos.ai).

**Miktos AI Bridge Platform** - *Transforming 3D creation through AI-powered automation*
