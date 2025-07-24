"""
Real-time Manager for Miktos AI Platform
Priority 3: Real-time Features & Optimization

Provides real-time collaboration, live synchronization, and
multi-user workflow coordination with WebSocket communication.
"""

import asyncio
import logging
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import weakref
from enum import Enum

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Real-time message types"""
    # User management
    USER_CONNECTED = "user_connected"
    USER_DISCONNECTED = "user_disconnected"
    USER_LIST = "user_list"
    
    # Workflow collaboration
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_ERROR = "workflow_error"
    
    # Scene synchronization
    SCENE_UPDATE = "scene_update"
    OBJECT_ADDED = "object_added"
    OBJECT_MODIFIED = "object_modified"
    OBJECT_DELETED = "object_deleted"
    
    # Command coordination
    COMMAND_RECEIVED = "command_received"
    COMMAND_EXECUTING = "command_executing"
    COMMAND_RESULT = "command_result"
    
    # System notifications
    PERFORMANCE_UPDATE = "performance_update"
    SYSTEM_STATUS = "system_status"
    ERROR_NOTIFICATION = "error_notification"
    
    # Chat and collaboration
    CHAT_MESSAGE = "chat_message"
    CURSOR_POSITION = "cursor_position"
    SELECTION_CHANGED = "selection_changed"


@dataclass
class ConnectedUser:
    """Connected user information"""
    user_id: str
    username: str
    connection_id: str
    websocket: Any  # WebSocket connection
    connected_at: datetime
    last_activity: datetime
    permissions: Set[str]
    current_workflow: Optional[str] = None
    cursor_position: Optional[Dict[str, float]] = None
    selected_objects: Optional[Set[str]] = None
    
    def __post_init__(self):
        if self.selected_objects is None:
            self.selected_objects = set()


@dataclass
class RealtimeMessage:
    """Real-time message structure"""
    message_id: str
    type: MessageType
    sender_id: str
    data: Dict[str, Any]
    timestamp: datetime
    target_users: Optional[List[str]] = None  # None means broadcast to all


@dataclass
class WorkflowSession:
    """Collaborative workflow session"""
    session_id: str
    workflow_id: str
    owner_id: str
    participants: Set[str]
    started_at: datetime
    current_step: int
    total_steps: int
    progress: float
    status: str  # "pending", "running", "completed", "error"
    shared_state: Dict[str, Any]


class CollaborationManager:
    """Manages collaborative workflow sessions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, WorkflowSession] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)
        self.session_locks: Dict[str, asyncio.Lock] = {}
    
    async def create_session(self, workflow_id: str, owner_id: str) -> str:
        """Create a new collaborative workflow session"""
        session_id = str(uuid.uuid4())
        
        session = WorkflowSession(
            session_id=session_id,
            workflow_id=workflow_id,
            owner_id=owner_id,
            participants={owner_id},
            started_at=datetime.now(),
            current_step=0,
            total_steps=1,
            progress=0.0,
            status="pending",
            shared_state={}
        )
        
        self.active_sessions[session_id] = session
        self.user_sessions[owner_id].add(session_id)
        self.session_locks[session_id] = asyncio.Lock()
        
        logger.info(f"Created collaborative session {session_id} for workflow {workflow_id}")
        return session_id
    
    async def join_session(self, session_id: str, user_id: str) -> bool:
        """Add user to collaborative session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.participants.add(user_id)
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"User {user_id} joined session {session_id}")
        return True
    
    async def leave_session(self, session_id: str, user_id: str):
        """Remove user from collaborative session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.participants.discard(user_id)
            
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
            
            # Clean up empty sessions
            if not session.participants:
                await self._cleanup_session(session_id)
    
    async def update_session_progress(self, session_id: str, current_step: int, 
                                    total_steps: int, progress: float, status: str):
        """Update session progress"""
        if session_id not in self.active_sessions:
            return
        
        async with self.session_locks[session_id]:
            session = self.active_sessions[session_id]
            session.current_step = current_step
            session.total_steps = total_steps
            session.progress = progress
            session.status = status
    
    async def update_shared_state(self, session_id: str, key: str, value: Any):
        """Update shared state for session"""
        if session_id not in self.active_sessions:
            return
        
        async with self.session_locks[session_id]:
            session = self.active_sessions[session_id]
            session.shared_state[key] = value
    
    async def _cleanup_session(self, session_id: str):
        """Clean up completed or empty session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        if session_id in self.session_locks:
            del self.session_locks[session_id]
        
        logger.info(f"Cleaned up session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[WorkflowSession]:
        """Get session information"""
        return self.active_sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[WorkflowSession]:
        """Get all sessions for a user"""
        session_ids = self.user_sessions.get(user_id, set())
        return [self.active_sessions[sid] for sid in session_ids if sid in self.active_sessions]


class SceneSync:
    """Manages real-time scene synchronization"""
    
    def __init__(self):
        self.scene_state = {}
        self.object_locks = {}
        self.pending_updates = defaultdict(list)
        self.sync_interval = 0.1  # 100ms sync interval
        self.last_sync = time.time()
    
    async def update_object(self, object_id: str, properties: Dict[str, Any], 
                          user_id: str) -> Dict[str, Any]:
        """Update object properties with conflict resolution"""
        current_time = time.time()
        
        # Check for object lock
        if object_id in self.object_locks:
            lock_info = self.object_locks[object_id]
            if lock_info['user_id'] != user_id and current_time - lock_info['timestamp'] < 30:
                # Object is locked by another user
                return {
                    'success': False,
                    'reason': 'object_locked',
                    'locked_by': lock_info['user_id']
                }
        
        # Apply update
        if object_id not in self.scene_state:
            self.scene_state[object_id] = {}
        
        # Merge properties
        self.scene_state[object_id].update(properties)
        self.scene_state[object_id]['last_modified'] = current_time
        self.scene_state[object_id]['modified_by'] = user_id
        
        # Add to pending updates
        update = {
            'object_id': object_id,
            'properties': properties,
            'user_id': user_id,
            'timestamp': current_time
        }
        self.pending_updates[object_id].append(update)
        
        return {'success': True, 'state': self.scene_state[object_id]}
    
    async def lock_object(self, object_id: str, user_id: str) -> bool:
        """Lock object for exclusive editing"""
        if object_id in self.object_locks:
            lock_info = self.object_locks[object_id]
            if lock_info['user_id'] != user_id:
                return False  # Already locked by another user
        
        self.object_locks[object_id] = {
            'user_id': user_id,
            'timestamp': time.time()
        }
        return True
    
    async def unlock_object(self, object_id: str, user_id: str) -> bool:
        """Unlock object"""
        if object_id in self.object_locks:
            lock_info = self.object_locks[object_id]
            if lock_info['user_id'] == user_id:
                del self.object_locks[object_id]
                return True
        return False
    
    async def get_pending_updates(self, since_timestamp: float) -> List[Dict[str, Any]]:
        """Get all pending updates since timestamp"""
        updates = []
        
        for object_id, object_updates in self.pending_updates.items():
            for update in object_updates:
                if update['timestamp'] > since_timestamp:
                    updates.append(update)
        
        return sorted(updates, key=lambda x: x['timestamp'])
    
    async def cleanup_old_updates(self, max_age_seconds: int = 300):
        """Clean up old pending updates"""
        cutoff_time = time.time() - max_age_seconds
        
        for object_id in list(self.pending_updates.keys()):
            self.pending_updates[object_id] = [
                update for update in self.pending_updates[object_id]
                if update['timestamp'] > cutoff_time
            ]
            
            if not self.pending_updates[object_id]:
                del self.pending_updates[object_id]


class RealtimeManager:
    """Main real-time collaboration and synchronization manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('realtime', {})
        self.websocket_config = config.get('websocket', {})
        
        # Connection management
        self.connected_users: Dict[str, ConnectedUser] = {}
        self.user_connections: Dict[str, List[ConnectedUser]] = defaultdict(list)
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        
        # Collaboration components
        self.collaboration_manager = CollaborationManager()
        self.scene_sync = SceneSync()
        
        # Performance settings
        self.max_concurrent_users = self.config.get('max_concurrent_users', 10)
        self.sync_interval = self.config.get('sync_interval_ms', 100) / 1000
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        
        # Message queue and rate limiting
        self.message_queue = asyncio.Queue()
        self.rate_limits = defaultdict(lambda: {'count': 0, 'reset_time': time.time() + 60})
        
        # Performance monitoring integration
        self.performance_monitor = None
        
        # WebSocket server
        self.websocket_server = None
        self.is_running = False
    
    def set_performance_monitor(self, monitor):
        """Set performance monitor for integration"""
        self.performance_monitor = monitor
    
    async def start_server(self, host: str = "localhost", port: int = 8083):
        """Start WebSocket server for real-time communication"""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("WebSockets not available - install websockets package")
            return False
        
        if self.is_running:
            return True
        
        try:
            self.websocket_server = await websockets.serve(
                self._handle_websocket_connection,
                host,
                port,
                max_size=1024*1024,  # 1MB max message size
                ping_interval=self.heartbeat_interval,
                ping_timeout=self.heartbeat_interval * 2
            )
            
            self.is_running = True
            logger.info(f"Real-time WebSocket server started on {host}:{port}")
            
            # Start background tasks
            asyncio.create_task(self._message_processor())
            asyncio.create_task(self._sync_coordinator())
            asyncio.create_task(self._cleanup_task())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def stop_server(self):
        """Stop WebSocket server"""
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
            self.is_running = False
            logger.info("Real-time WebSocket server stopped")
    
    async def _handle_websocket_connection(self, websocket):
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        user_id = None
        
        try:
            # Wait for authentication message
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=30)
            auth_data = json.loads(auth_message)
            
            if auth_data.get('type') != 'authenticate':
                await websocket.close(code=4001, reason="Authentication required")
                return
            
            # Validate user
            user_id = auth_data.get('user_id')
            username = auth_data.get('username', f"User-{user_id[:8]}")
            
            if not user_id:
                await websocket.close(code=4002, reason="Invalid user_id")
                return
            
            # Check concurrent user limit
            if len(self.connected_users) >= self.max_concurrent_users:
                await websocket.close(code=4003, reason="Server full")
                return
            
            # Create user connection
            user = ConnectedUser(
                user_id=user_id,
                username=username,
                connection_id=connection_id,
                websocket=websocket,
                connected_at=datetime.now(),
                last_activity=datetime.now(),
                permissions=set(auth_data.get('permissions', []))
            )
            
            self.connected_users[connection_id] = user
            self.user_connections[user_id].append(user)
            
            # Send successful authentication
            await self._send_to_user(connection_id, RealtimeMessage(
                message_id=str(uuid.uuid4()),
                type=MessageType.USER_CONNECTED,
                sender_id="system",
                data={
                    'connection_id': connection_id,
                    'user_count': len(self.connected_users)
                },
                timestamp=datetime.now()
            ))
            
            # Broadcast user list update
            await self._broadcast_user_list()
            
            # Record connection in performance monitor
            if self.performance_monitor:
                self.performance_monitor.record_websocket_activity(
                    "user_connected", len(self.connected_users)
                )
            
            logger.info(f"User {username} ({user_id}) connected with connection {connection_id}")
            
            # Handle messages
            async for message in websocket:
                try:
                    await self._handle_message(connection_id, message)
                except Exception as e:
                    logger.error(f"Error handling message from {connection_id}: {e}")
                    await self._send_error(connection_id, str(e))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection {connection_id} closed")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            await self._cleanup_connection(connection_id, user_id)
    
    async def _handle_message(self, connection_id: str, raw_message: str):
        """Handle incoming message from WebSocket"""
        user = self.connected_users.get(connection_id)
        if not user:
            return
        
        # Update last activity
        user.last_activity = datetime.now()
        
        # Parse message
        try:
            message_data = json.loads(raw_message)
        except json.JSONDecodeError:
            await self._send_error(connection_id, "Invalid JSON message")
            return
        
        # Rate limiting
        if not self._check_rate_limit(user.user_id):
            await self._send_error(connection_id, "Rate limit exceeded")
            return
        
        # Create message object
        message = RealtimeMessage(
            message_id=message_data.get('message_id', str(uuid.uuid4())),
            type=MessageType(message_data.get('type')),
            sender_id=user.user_id,
            data=message_data.get('data', {}),
            timestamp=datetime.now(),
            target_users=message_data.get('target_users')
        )
        
        # Queue message for processing
        await self.message_queue.put((connection_id, message))
    
    async def _message_processor(self):
        """Process queued messages"""
        while self.is_running:
            try:
                connection_id, message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=1.0
                )
                
                await self._process_message(connection_id, message)
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Message processor error: {e}")
    
    async def _process_message(self, connection_id: str, message: RealtimeMessage):
        """Process individual message"""
        user = self.connected_users.get(connection_id)
        if not user:
            return
        
        # Handle different message types
        if message.type == MessageType.WORKFLOW_STARTED:
            await self._handle_workflow_started(user, message)
        
        elif message.type == MessageType.SCENE_UPDATE:
            await self._handle_scene_update(user, message)
        
        elif message.type == MessageType.OBJECT_MODIFIED:
            await self._handle_object_modified(user, message)
        
        elif message.type == MessageType.COMMAND_RECEIVED:
            await self._handle_command_received(user, message)
        
        elif message.type == MessageType.CHAT_MESSAGE:
            await self._handle_chat_message(user, message)
        
        elif message.type == MessageType.CURSOR_POSITION:
            await self._handle_cursor_position(user, message)
        
        # Call registered handlers
        for handler in self.message_handlers[message.type]:
            try:
                await handler(user, message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
    
    async def _handle_workflow_started(self, user: ConnectedUser, message: RealtimeMessage):
        """Handle workflow started message"""
        workflow_id = message.data.get('workflow_id')
        if not workflow_id:
            return
        
        # Create collaborative session
        session_id = await self.collaboration_manager.create_session(workflow_id, user.user_id)
        user.current_workflow = session_id
        
        # Broadcast to other users
        await self._broadcast_message(RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.WORKFLOW_STARTED,
            sender_id=user.user_id,
            data={
                'workflow_id': workflow_id,
                'session_id': session_id,
                'username': user.username
            },
            timestamp=datetime.now()
        ), exclude_user=user.user_id)
    
    async def _handle_scene_update(self, user: ConnectedUser, message: RealtimeMessage):
        """Handle scene update message"""
        object_id = message.data.get('object_id')
        properties = message.data.get('properties', {})
        
        if not object_id:
            return
        
        # Update scene state
        result = await self.scene_sync.update_object(object_id, properties, user.user_id)
        
        if result['success']:
            # Broadcast update to other users
            await self._broadcast_message(RealtimeMessage(
                message_id=str(uuid.uuid4()),
                type=MessageType.SCENE_UPDATE,
                sender_id=user.user_id,
                data={
                    'object_id': object_id,
                    'properties': properties,
                    'state': result['state']
                },
                timestamp=datetime.now()
            ), exclude_user=user.user_id)
        else:
            # Send error back to user
            await self._send_to_user(user.connection_id, RealtimeMessage(
                message_id=str(uuid.uuid4()),
                type=MessageType.ERROR_NOTIFICATION,
                sender_id="system",
                data=result,
                timestamp=datetime.now()
            ))
    
    async def _handle_object_modified(self, user: ConnectedUser, message: RealtimeMessage):
        """Handle object modification message"""
        # Similar to scene update but for specific object modifications
        await self._handle_scene_update(user, message)
    
    async def _handle_command_received(self, user: ConnectedUser, message: RealtimeMessage):
        """Handle command received message"""
        command = message.data.get('command')
        if not command:
            return
        
        # Broadcast command to other users for awareness
        await self._broadcast_message(RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.COMMAND_RECEIVED,
            sender_id=user.user_id,
            data={
                'command': command,
                'username': user.username
            },
            timestamp=datetime.now()
        ), exclude_user=user.user_id)
    
    async def _handle_chat_message(self, user: ConnectedUser, message: RealtimeMessage):
        """Handle chat message"""
        chat_text = message.data.get('text')
        if not chat_text:
            return
        
        # Broadcast chat message
        await self._broadcast_message(RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.CHAT_MESSAGE,
            sender_id=user.user_id,
            data={
                'text': chat_text,
                'username': user.username
            },
            timestamp=datetime.now()
        ))
    
    async def _handle_cursor_position(self, user: ConnectedUser, message: RealtimeMessage):
        """Handle cursor position update"""
        position = message.data.get('position')
        if not position:
            return
        
        user.cursor_position = position
        
        # Broadcast cursor position to other users
        await self._broadcast_message(RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.CURSOR_POSITION,
            sender_id=user.user_id,
            data={
                'position': position,
                'username': user.username
            },
            timestamp=datetime.now()
        ), exclude_user=user.user_id)
    
    async def _sync_coordinator(self):
        """Coordinate periodic synchronization"""
        while self.is_running:
            try:
                # Send performance updates to connected users
                if self.performance_monitor:
                    metrics = self.performance_monitor.get_current_metrics()
                    await self._broadcast_message(RealtimeMessage(
                        message_id=str(uuid.uuid4()),
                        type=MessageType.PERFORMANCE_UPDATE,
                        sender_id="system",
                        data={'metrics': metrics},
                        timestamp=datetime.now()
                    ))
                
                # Sync scene updates
                current_time = time.time()
                updates = await self.scene_sync.get_pending_updates(
                    current_time - self.sync_interval
                )
                
                if updates:
                    await self._broadcast_message(RealtimeMessage(
                        message_id=str(uuid.uuid4()),
                        type=MessageType.SCENE_UPDATE,
                        sender_id="system",
                        data={'updates': updates},
                        timestamp=datetime.now()
                    ))
                
                await asyncio.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Sync coordinator error: {e}")
                await asyncio.sleep(1.0)
    
    async def _cleanup_task(self):
        """Background cleanup task"""
        while self.is_running:
            try:
                # Clean up old scene updates
                await self.scene_sync.cleanup_old_updates()
                
                # Clean up inactive users
                current_time = datetime.now()
                inactive_threshold = timedelta(minutes=30)
                
                inactive_connections = []
                for connection_id, user in self.connected_users.items():
                    if current_time - user.last_activity > inactive_threshold:
                        inactive_connections.append(connection_id)
                
                for connection_id in inactive_connections:
                    user = self.connected_users.get(connection_id)
                    if user:
                        await self._cleanup_connection(connection_id, user.user_id)
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(60)
    
    async def _send_to_user(self, connection_id: str, message: RealtimeMessage):
        """Send message to specific user"""
        user = self.connected_users.get(connection_id)
        if not user:
            return
        
        try:
            message_json = json.dumps({
                'message_id': message.message_id,
                'type': message.type.value,
                'sender_id': message.sender_id,
                'data': message.data,
                'timestamp': message.timestamp.isoformat()
            })
            
            await user.websocket.send(message_json)
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            await self._cleanup_connection(connection_id, user.user_id)
    
    async def _broadcast_message(self, message: RealtimeMessage, exclude_user: Optional[str] = None):
        """Broadcast message to all connected users"""
        tasks = []
        
        for connection_id, user in self.connected_users.items():
            if exclude_user and user.user_id == exclude_user:
                continue
            
            if message.target_users and user.user_id not in message.target_users:
                continue
            
            tasks.append(self._send_to_user(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _broadcast_user_list(self):
        """Broadcast current user list to all connected users"""
        user_list = [
            {
                'user_id': user.user_id,
                'username': user.username,
                'connected_at': user.connected_at.isoformat(),
                'current_workflow': user.current_workflow
            }
            for user in self.connected_users.values()
        ]
        
        await self._broadcast_message(RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.USER_LIST,
            sender_id="system",
            data={'users': user_list},
            timestamp=datetime.now()
        ))
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send error message to user"""
        await self._send_to_user(connection_id, RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.ERROR_NOTIFICATION,
            sender_id="system",
            data={'error': error_message},
            timestamp=datetime.now()
        ))
    
    async def _cleanup_connection(self, connection_id: str, user_id: Optional[str]):
        """Clean up disconnected user"""
        if connection_id in self.connected_users:
            user = self.connected_users[connection_id]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id] = [
                    u for u in self.user_connections[user_id] 
                    if u.connection_id != connection_id
                ]
                
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Leave any collaborative sessions
            user_sessions = self.collaboration_manager.get_user_sessions(user.user_id)
            for session in user_sessions:
                await self.collaboration_manager.leave_session(session.session_id, user.user_id)
            
            # Remove from connected users
            del self.connected_users[connection_id]
            
            # Record disconnection
            if self.performance_monitor:
                self.performance_monitor.record_websocket_activity(
                    "user_disconnected", len(self.connected_users)
                )
            
            # Broadcast user list update
            await self._broadcast_user_list()
            
            logger.info(f"Cleaned up connection {connection_id} for user {user_id}")
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        rate_info = self.rate_limits[user_id]
        
        if current_time > rate_info['reset_time']:
            # Reset rate limit window
            rate_info['count'] = 0
            rate_info['reset_time'] = current_time + 60
        
        if rate_info['count'] >= 60:  # 60 messages per minute
            return False
        
        rate_info['count'] += 1
        return True
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register handler for specific message type"""
        self.message_handlers[message_type].append(handler)
    
    def get_connected_users(self) -> List[Dict[str, Any]]:
        """Get list of connected users"""
        return [
            {
                'user_id': user.user_id,
                'username': user.username,
                'connected_at': user.connected_at.isoformat(),
                'last_activity': user.last_activity.isoformat(),
                'current_workflow': user.current_workflow,
                'cursor_position': user.cursor_position
            }
            for user in self.connected_users.values()
        ]
    
    async def broadcast_workflow_progress(self, workflow_id: str, progress: float, 
                                        current_step: int, total_steps: int):
        """Broadcast workflow progress to all users"""
        await self._broadcast_message(RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.WORKFLOW_PROGRESS,
            sender_id="system",
            data={
                'workflow_id': workflow_id,
                'progress': progress,
                'current_step': current_step,
                'total_steps': total_steps
            },
            timestamp=datetime.now()
        ))
    
    async def broadcast_system_status(self, status: Dict[str, Any]):
        """Broadcast system status to all users"""
        await self._broadcast_message(RealtimeMessage(
            message_id=str(uuid.uuid4()),
            type=MessageType.SYSTEM_STATUS,
            sender_id="system",
            data=status,
            timestamp=datetime.now()
        ))
