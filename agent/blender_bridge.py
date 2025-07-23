"""
Blender Bridge for Miktos Agent

Handles communication with Blender Python API and executes 3D operations.
Includes safety validation and real-time feedback.
"""

import asyncio
import subprocess
import json
import socket
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import tempfile
import time

from .scene_manager import SceneManager  # type: ignore
from .operation_validator import OperationValidator  # type: ignore
from .result_analyzer import ResultAnalyzer  # type: ignore


@dataclass
class BlenderOperation:
    """Represents a single Blender operation"""
    operation_type: str  # create, modify, delete, etc.
    target: str  # object, material, light, etc.
    parameters: Dict[str, Any]
    safety_level: str = "normal"  # low, normal, high
    timeout: float = 30.0


@dataclass
class ExecutionPlan:
    """Represents a complete execution plan"""
    operations: List[BlenderOperation]
    dependencies: Dict[str, List[str]]  # operation dependencies
    rollback_plan: List[BlenderOperation]
    skills_used: List[str]
    estimated_time: float


@dataclass
class BlenderResult:
    """Result of Blender operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    scene_state: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0


class BlenderBridge:
    """
    Bridge between Miktos Agent and Blender Python API
    Handles safe execution of 3D operations with real-time feedback
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.blender_path = config.get('path', '/Applications/Blender.app')
        self.python_path = config.get('python_path')
        
        # Connection settings
        self.socket_port = config.get('socket_port', 8089)
        self.socket = None
        self._is_connected = False
        
        # Initialize components
        self.scene_manager = SceneManager(config.get('scene', {}))
        self.operation_validator = OperationValidator(config.get('validation', {}))
        self.result_analyzer = ResultAnalyzer(config.get('analysis', {}))
        
        # Setup logging
        self.logger = logging.getLogger('BlenderBridge')
        
        # State tracking
        self.current_scene_state = None
        self.operation_history = []
        
        # Blender process
        self.blender_process = None
        self.bridge_script_path = None
        
    async def connect(self) -> bool:
        """Establish connection to Blender"""
        try:
            # Create bridge script
            await self._create_bridge_script()
            
            # Start Blender with bridge script
            await self._start_blender_bridge()
            
            # Wait for connection
            success = await self._wait_for_connection()
            
            if success:
                self._is_connected = True
                self.logger.info("Successfully connected to Blender")
                
                # Initialize scene state
                await self._initialize_scene_state()
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Blender: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Blender"""
        if self.socket:
            try:
                await self._send_command({"action": "shutdown"})
                self.socket.close()
            except:
                pass
        
        if self.blender_process:
            self.blender_process.terminate()
            await asyncio.sleep(1)
            if self.blender_process.poll() is None:
                self.blender_process.kill()
        
        self._is_connected = False
        self.logger.info("Disconnected from Blender")
    
    async def execute_plan(self, plan: ExecutionPlan) -> BlenderResult:
        """Execute a complete operation plan"""
        start_time = time.time()
        
        if not await self.is_connected():
            return BlenderResult(
                success=False,
                message="Not connected to Blender",
                errors=["Blender bridge not connected"]
            )
        
        try:
            # Create checkpoint for rollback
            checkpoint = await self._create_checkpoint()
            
            # Validate entire plan
            validation_result = await self.operation_validator.validate_plan(plan)
            if not validation_result.is_valid:
                return BlenderResult(
                    success=False,
                    message=f"Plan validation failed: {validation_result.reason}",
                    errors=[validation_result.reason]
                )
            
            # Execute operations in sequence
            results = []
            for i, operation in enumerate(plan.operations):
                self.logger.info(f"Executing operation {i+1}/{len(plan.operations)}: {operation.operation_type}")
                
                result = await self._execute_single_operation(operation)
                results.append(result)
                
                if not result.success:
                    # Rollback on failure
                    await self._rollback_to_checkpoint(checkpoint)
                    return BlenderResult(
                        success=False,
                        message=f"Operation {i+1} failed: {result.message}",
                        errors=result.errors
                    )
            
            # Analyze overall result
            execution_time = time.time() - start_time
            final_result = await self._analyze_plan_result(plan, results)
            final_result.execution_time = execution_time
            
            # Update scene state
            await self._update_scene_state()
            
            return final_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Plan execution failed: {e}")
            
            return BlenderResult(
                success=False,
                message=f"Execution error: {str(e)}",
                errors=[str(e)],
                execution_time=execution_time
            )
    
    async def _execute_single_operation(self, operation: BlenderOperation) -> BlenderResult:
        """Execute a single Blender operation"""
        try:
            # Prepare command
            command = {
                "action": "execute_operation",
                "operation": {
                    "type": operation.operation_type,
                    "target": operation.target,
                    "parameters": operation.parameters
                },
                "timeout": operation.timeout
            }
            
            # Send to Blender
            response = await self._send_command(command)
            
            if response.get('success'):
                return BlenderResult(
                    success=True,
                    message=response.get('message', 'Operation completed'),
                    data=response.get('data'),
                    scene_state=response.get('scene_state')
                )
            else:
                return BlenderResult(
                    success=False,
                    message=response.get('message', 'Operation failed'),
                    errors=response.get('errors', [])
                )
                
        except Exception as e:
            return BlenderResult(
                success=False,
                message=f"Communication error: {str(e)}",
                errors=[str(e)]
            )
    
    async def _create_bridge_script(self):
        """Create the Python script that runs inside Blender"""
        bridge_script = '''
import bpy
import bmesh
import socket
import json
import threading
import time
from mathutils import Vector, Euler

class BlenderBridge:
    def __init__(self, port=8089):
        self.port = port
        self.socket = None
        self.running = False
        
    def start_server(self):
        """Start the socket server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('localhost', self.port))
        self.socket.listen(1)
        self.running = True
        
        print(f"Blender bridge listening on port {self.port}")
        
        while self.running:
            try:
                client, addr = self.socket.accept()
                print(f"Connection from {addr}")
                
                # Handle client in separate thread
                threading.Thread(target=self.handle_client, args=(client,)).start()
                
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
                break
    
    def handle_client(self, client):
        """Handle client connection"""
        try:
            while True:
                data = client.recv(4096)
                if not data:
                    break
                
                try:
                    command = json.loads(data.decode())
                    response = self.process_command(command)
                    client.send(json.dumps(response).encode())
                    
                except json.JSONDecodeError:
                    error_response = {"success": False, "message": "Invalid JSON"}
                    client.send(json.dumps(error_response).encode())
                    
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            client.close()
    
    def process_command(self, command):
        """Process incoming command"""
        action = command.get('action')
        
        if action == 'ping':
            return {"success": True, "message": "pong"}
        
        elif action == 'execute_operation':
            return self.execute_operation(command.get('operation'))
        
        elif action == 'get_scene_state':
            return self.get_scene_state()
        
        elif action == 'shutdown':
            self.running = False
            return {"success": True, "message": "Shutting down"}
        
        else:
            return {"success": False, "message": f"Unknown action: {action}"}
    
    def execute_operation(self, operation):
        """Execute a 3D operation"""
        try:
            op_type = operation.get('type')
            target = operation.get('target')
            params = operation.get('parameters', {})
            
            if op_type == 'create':
                return self.create_object(target, params)
            elif op_type == 'modify':
                return self.modify_object(target, params)
            elif op_type == 'delete':
                return self.delete_object(target, params)
            else:
                return {"success": False, "message": f"Unknown operation type: {op_type}"}
                
        except Exception as e:
            return {"success": False, "message": str(e), "errors": [str(e)]}
    
    def create_object(self, obj_type, params):
        """Create a new object"""
        try:
            if obj_type == 'cube':
                bpy.ops.mesh.primitive_cube_add(
                    size=params.get('size', 2.0),
                    location=params.get('location', (0, 0, 0))
                )
            elif obj_type == 'sphere':
                bpy.ops.mesh.primitive_uv_sphere_add(
                    radius=params.get('radius', 1.0),
                    location=params.get('location', (0, 0, 0))
                )
            elif obj_type == 'cylinder':
                bpy.ops.mesh.primitive_cylinder_add(
                    radius=params.get('radius', 1.0),
                    depth=params.get('depth', 2.0),
                    location=params.get('location', (0, 0, 0))
                )
            elif obj_type == 'plane':
                bpy.ops.mesh.primitive_plane_add(
                    size=params.get('size', 2.0),
                    location=params.get('location', (0, 0, 0))
                )
            else:
                return {"success": False, "message": f"Unknown object type: {obj_type}"}
            
            # Get the created object
            obj = bpy.context.active_object
            
            # Apply any additional modifications
            if 'subdivisions' in params:
                self.subdivide_object(obj, params['subdivisions'])
            
            return {
                "success": True,
                "message": f"Created {obj_type}",
                "data": {"object_name": obj.name}
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def modify_object(self, target, params):
        """Modify an existing object"""
        try:
            # Get target object
            if target == 'selected':
                obj = bpy.context.active_object
            else:
                obj = bpy.data.objects.get(target)
            
            if not obj:
                return {"success": False, "message": f"Object not found: {target}"}
            
            # Select and make active
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Apply modifications
            if 'scale' in params:
                scale_factor = params['scale']
                if isinstance(scale_factor, (int, float)):
                    obj.scale = (scale_factor, scale_factor, scale_factor)
                elif isinstance(scale_factor, (list, tuple)) and len(scale_factor) == 3:
                    obj.scale = scale_factor
            
            if 'rotation' in params:
                rotation = params['rotation']
                if isinstance(rotation, (list, tuple)) and len(rotation) == 3:
                    obj.rotation_euler = Euler(rotation, 'XYZ')
            
            if 'location' in params:
                location = params['location']
                if isinstance(location, (list, tuple)) and len(location) == 3:
                    obj.location = location
            
            if 'subdivisions' in params:
                self.subdivide_object(obj, params['subdivisions'])
            
            return {
                "success": True,
                "message": f"Modified {obj.name}",
                "data": {"object_name": obj.name}
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def subdivide_object(self, obj, levels):
        """Subdivide a mesh object"""
        try:
            # Enter edit mode
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Select all
            bpy.ops.mesh.select_all(action='SELECT')
            
            # Apply subdivision
            for _ in range(levels):
                bpy.ops.mesh.subdivide()
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
        except Exception as e:
            # Ensure we're back in object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            raise e
    
    def delete_object(self, target, params):
        """Delete an object"""
        try:
            if target == 'selected':
                bpy.ops.object.delete()
                return {"success": True, "message": "Deleted selected object"}
            else:
                obj = bpy.data.objects.get(target)
                if obj:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    return {"success": True, "message": f"Deleted {target}"}
                else:
                    return {"success": False, "message": f"Object not found: {target}"}
                    
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_scene_state(self):
        """Get current scene state"""
        try:
            objects = []
            for obj in bpy.data.objects:
                objects.append({
                    "name": obj.name,
                    "type": obj.type,
                    "location": list(obj.location),
                    "scale": list(obj.scale),
                    "rotation": list(obj.rotation_euler)
                })
            
            return {
                "success": True,
                "data": {
                    "objects": objects,
                    "active_object": bpy.context.active_object.name if bpy.context.active_object else None
                }
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}

# Start the bridge
if __name__ == "__main__":
    bridge = BlenderBridge()
    bridge.start_server()
'''
        
        # Save script to temporary file
        self.bridge_script_path = Path(tempfile.gettempdir()) / "miktos_bridge.py"
        with open(self.bridge_script_path, 'w') as f:
            f.write(bridge_script)
        
        self.logger.info(f"Bridge script created at {self.bridge_script_path}")
    
    async def _start_blender_bridge(self):
        """Start Blender with the bridge script"""
        command = [
            str(Path(self.blender_path) / "Contents/MacOS/Blender"),
            "--background",
            "--python", str(self.bridge_script_path)
        ]
        
        self.logger.info(f"Starting Blender: {' '.join(command)}")
        
        self.blender_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    async def _wait_for_connection(self, timeout: float = 30.0) -> bool:
        """Wait for Blender to start and accept connections"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(('localhost', self.socket_port))
                
                # Test connection
                response = await self._send_command({"action": "ping"})
                if response.get('message') == 'pong':
                    self.logger.info("Connection established")
                    return True
                    
            except (ConnectionRefusedError, OSError):
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Connection test failed: {e}")
                await asyncio.sleep(1)
        
        return False
    
    async def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to Blender and get response"""
        try:
            if not self.socket:
                self.logger.error("Socket not connected")
                return {"error": "Socket not connected"}
            
            message = json.dumps(command).encode()
            self.socket.send(message)
            
            response_data = self.socket.recv(4096)
            response = json.loads(response_data.decode())
            
            return response
            
        except Exception as e:
            self.logger.error(f"Communication error: {e}")
            raise
    
    async def _initialize_scene_state(self):
        """Initialize scene state tracking"""
        response = await self._send_command({"action": "get_scene_state"})
        if response.get('success'):
            self.current_scene_state = response.get('data')
    
    async def _update_scene_state(self):
        """Update current scene state"""
        response = await self._send_command({"action": "get_scene_state"})
        if response.get('success'):
            self.current_scene_state = response.get('data')
    
    async def _create_checkpoint(self) -> Dict[str, Any]:
        """Create a checkpoint for rollback"""
        response = await self._send_command({"action": "get_scene_state"})
        return response.get('data', {})
    
    async def _rollback_to_checkpoint(self, checkpoint: Dict[str, Any]):
        """Rollback to a previous checkpoint"""
        # Simple implementation - would need more sophisticated rollback logic
        self.logger.warning("Rollback requested - not fully implemented")
    
    async def _analyze_plan_result(self, plan: ExecutionPlan, results: List[BlenderResult]) -> BlenderResult:
        """Analyze the overall result of plan execution"""
        all_successful = all(result.success for result in results)
        
        if all_successful:
            return BlenderResult(
                success=True,
                message=f"Successfully executed {len(results)} operations",
                data={"operations_completed": len(results)}
            )
        else:
            failed_count = sum(1 for result in results if not result.success)
            return BlenderResult(
                success=False,
                message=f"{failed_count} operations failed",
                errors=[result.message for result in results if not result.success]
            )
    
    async def is_connected(self) -> bool:
        """Check if connected to Blender"""
        return self._is_connected
    
    async def get_scene_info(self) -> Dict[str, Any]:
        """Get current scene information"""
        if not await self.is_connected():
            return {}
        
        response = await self._send_command({"action": "get_scene_state"})
        return response.get('data', {})


# Utility functions
def create_simple_operation(op_type: str, target: str, **kwargs) -> BlenderOperation:
    """Create a simple Blender operation"""
    return BlenderOperation(
        operation_type=op_type,
        target=target,
        parameters=kwargs
    )


if __name__ == "__main__":
    # Test the Blender bridge
    async def test_bridge():
        config = {
            'path': '/Applications/Blender.app',
            'socket_port': 8089
        }
        
        bridge = BlenderBridge(config)
        
        # Connect
        success = await bridge.connect()
        if not success:
            print("Failed to connect to Blender")
            return
        
        # Create test operations
        operations = [
            create_simple_operation('create', 'cube', size=2.0),
            create_simple_operation('modify', 'selected', subdivisions=2),
            create_simple_operation('modify', 'selected', scale=1.5),
        ]
        
        plan = ExecutionPlan(
            operations=operations,
            dependencies={},
            rollback_plan=[],
            skills_used=['create_cube', 'subdivide_mesh', 'scale_object'],
            estimated_time=5.0
        )
        
        # Execute plan
        result = await bridge.execute_plan(plan)
        print(f"Execution result: {result.message}")
        print(f"Success: {result.success}")
        
        # Disconnect
        await bridge.disconnect()
    
    asyncio.run(test_bridge())
