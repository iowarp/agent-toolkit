#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp>=1.4.0",
#   "aiohttp>=3.9.0",
#   "pydantic>=2.4.2,<3.0.0"
# ]
# requires-python = ">=3.10"
# ///

"""
Server-Sent Events (SSE) transport for streaming large datasets.
Implements the Streamable HTTP transport from MCP 2025-06-18 spec.
"""
import asyncio
import json
import logging
import uuid
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from weakref import WeakSet

from aiohttp import web, WSMsgType
from aiohttp.web_request import Request
from aiohttp.web_response import Response, StreamResponse

from mcp.types import (
    JSONRPCMessage,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification
)

from .base import BaseTransport, TransportConfig, TransportType

logger = logging.getLogger(__name__)

# Supported MCP protocol versions
SUPPORTED_VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05']

@dataclass
class SessionInfo:
    """Session management information."""
    session_id: str
    created_at: float
    last_accessed: float
    client_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SSEClient:
    """Represents an SSE client connection."""
    client_id: str
    request: Request
    response: StreamResponse
    queue: asyncio.Queue
    last_ping: float
    session_id: Optional[str] = None
    event_counter: int = 0

class SSETransport(BaseTransport):
    """Server-Sent Events transport with JSON-RPC batching."""

    def __init__(self, config: TransportConfig = None):
        if config is None:
            config = TransportConfig(
                transport_type=TransportType.SSE,
                host="127.0.0.1",  # Localhost-only by default for security
                port=8765,
                max_connections=100,
                enable_batching=True,
                batch_timeout=0.1,
                max_batch_size=50
            )
        super().__init__(config)

        # Enforce localhost binding for security
        if config.host in ['0.0.0.0', None]:
            config.host = '127.0.0.1'
            logger.warning("Enforcing localhost-only binding for security")

        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.clients: Dict[str, SSEClient] = {}
        self.sessions: Dict[str, SessionInfo] = {}
        self.event_history: Dict[str, List[tuple]] = {}  # client_id -> [(event_id, data)]
        self.client_counter = 0
        self._ping_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the SSE HTTP server."""
        try:
            # Create aiohttp application
            self.app = web.Application()
            
            # Add routes
            self.app.router.add_post('/mcp', self._handle_post)
            self.app.router.add_get('/mcp', self._handle_sse)
            self.app.router.add_get('/health', self._handle_health)
            self.app.router.add_get('/stats', self._handle_stats)
            
            # Start server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner,
                self.config.host,
                self.config.port
            )
            await self.site.start()
            
            self.running = True
            
            # Start ping task to keep connections alive
            self._ping_task = asyncio.create_task(self._ping_clients())
            
            logger.info(f"SSE transport started on {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to start SSE transport: {e}")
            raise
            
    async def stop(self) -> None:
        """Stop the SSE transport."""
        self.running = False
        
        # Cancel ping task
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
                
        # Close all client connections
        for client in list(self.clients.values()):
            await self._close_client(client)
            
        # Stop server
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
            
        logger.info("SSE transport stopped")

    def _validate_origin(self, request: Request) -> bool:
        """Validate Origin header to prevent DNS rebinding attacks."""
        origin = request.headers.get('Origin')
        if not origin:
            return True  # No origin header - allow (for non-browser clients)

        # Allow localhost/127.0.0.1 origins only
        allowed_prefixes = [
            'http://localhost', 'http://127.0.0.1',
            'https://localhost', 'https://127.0.0.1'
        ]

        for prefix in allowed_prefixes:
            if origin.startswith(prefix):
                return True

        logger.warning(f"Rejected request from origin: {origin}")
        return False

    def _create_session(self) -> str:
        """Create new session ID (cryptographically secure UUID)."""
        session_id = str(uuid.uuid4())
        current_time = asyncio.get_event_loop().time()

        self.sessions[session_id] = SessionInfo(
            session_id=session_id,
            created_at=current_time,
            last_accessed=current_time
        )

        logger.info(f"Created session: {session_id}")
        return session_id

    def _validate_session(self, session_id: Optional[str]) -> bool:
        """Validate session ID exists and is active."""
        if not session_id:
            return False
        if session_id not in self.sessions:
            return False

        # Update last accessed time
        self.sessions[session_id].last_accessed = asyncio.get_event_loop().time()
        return True

    def _terminate_session(self, session_id: str) -> None:
        """Terminate a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Terminated session: {session_id}")

    def _validate_protocol_version(self, request: Request) -> tuple:
        """Validate MCP protocol version header."""
        protocol_version = request.headers.get('MCP-Protocol-Version', '2025-03-26')
        if protocol_version not in SUPPORTED_VERSIONS:
            return False, f"Unsupported protocol version: {protocol_version}"
        return True, protocol_version

    def _generate_event_id(self, client: SSEClient) -> str:
        """Generate unique event ID for resumable streams."""
        client.event_counter += 1
        return f"{client.client_id}_{client.event_counter}"

    def _store_event(self, client_id: str, event_id: str, data: Any) -> None:
        """Store event for resumable streams."""
        if client_id not in self.event_history:
            self.event_history[client_id] = []
        self.event_history[client_id].append((event_id, data))
        # Keep only last 100 events per client
        if len(self.event_history[client_id]) > 100:
            self.event_history[client_id] = self.event_history[client_id][-100:]

    async def _replay_events(self, client: SSEClient, last_event_id: str) -> None:
        """Replay events after last_event_id for resumable streams."""
        if client.client_id not in self.event_history:
            return

        replay = False
        for event_id, data in self.event_history[client.client_id]:
            if event_id == last_event_id:
                replay = True
                continue
            if replay:
                await self._send_sse_event(client, 'message', data, event_id=event_id)

    async def send_message(self, message: JSONRPCMessage) -> None:
        """Send message to all connected clients."""
        if not self.clients:
            return
            
        # Serialize message
        try:
            if hasattr(message, 'model_dump'):
                data = message.model_dump()
            elif hasattr(message, 'dict'):
                data = message.dict()
            else:
                data = message
                
            json_str = json.dumps(data, separators=(',', ':'))
            
            # Send to all clients
            for client in list(self.clients.values()):
                try:
                    await client.queue.put(('message', json_str))
                except Exception as e:
                    logger.error(f"Failed to queue message for client {client.client_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to serialize message: {e}")
            self.stats['errors'] += 1
            
    async def send_batch(self, messages: List[JSONRPCMessage]) -> None:
        """Send batch of messages to all connected clients."""
        if not messages or not self.clients:
            return
            
        try:
            # Serialize batch
            batch_data = []
            for message in messages:
                if hasattr(message, 'model_dump'):
                    data = message.model_dump()
                elif hasattr(message, 'dict'):
                    data = message.dict()
                else:
                    data = message
                batch_data.append(data)
                
            json_str = json.dumps(batch_data, separators=(',', ':'))
            
            # Send to all clients
            for client in list(self.clients.values()):
                try:
                    await client.queue.put(('batch', json_str))
                except Exception as e:
                    logger.error(f"Failed to queue batch for client {client.client_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to serialize batch: {e}")
            self.stats['errors'] += 1
            
    async def receive_message(self) -> Optional[JSONRPCMessage]:
        """Not implemented for SSE (receive via POST)."""
        return None
        
    async def receive_batch(self) -> List[JSONRPCMessage]:
        """Not implemented for SSE (receive via POST)."""
        return []
        
    async def _handle_post(self, request: Request) -> Response:
        """Handle HTTP POST requests with JSON-RPC messages (MCP 2025-06-18 compliant)."""
        try:
            # Security: Validate Origin header
            if not self._validate_origin(request):
                return web.Response(status=403, text="Forbidden: Invalid origin")

            # Validate MCP protocol version
            valid, version_or_error = self._validate_protocol_version(request)
            if not valid:
                return web.Response(status=400, text=version_or_error)

            protocol_version = version_or_error

            # Check content type
            content_type = request.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                return web.Response(
                    status=400,
                    text="Content-Type must be application/json"
                )

            # Parse request body
            try:
                data = await request.json()
            except Exception as e:
                return web.Response(
                    status=400,
                    text=f"Invalid JSON: {e}"
                )
                
            # Session management
            session_id = request.headers.get('Mcp-Session-Id')
            is_initialize = isinstance(data, dict) and data.get('method') == 'initialize'

            # Validate session (except for initialize requests)
            if not is_initialize and session_id:
                if not self._validate_session(session_id):
                    return web.Response(status=404, text="Session not found or expired")

            # Process message(s)
            messages = []
            if isinstance(data, list):
                # Batch request
                for item in data:
                    message = self._parse_message(item)
                    if message:
                        messages.append(message)
                self.stats['batches_received'] += 1
            else:
                # Single request
                message = self._parse_message(data)
                if message:
                    messages.append(message)

            self.stats['messages_received'] += len(messages)

            # Determine message type for proper response
            is_request = any(isinstance(m, JSONRPCRequest) for m in messages)
            is_notification = all(isinstance(m, JSONRPCNotification) for m in messages)
            is_response = all(isinstance(m, JSONRPCResponse) for m in messages)

            # Handle responses and notifications (MCP spec: return 202 Accepted)
            if is_response or is_notification:
                return web.Response(status=202, text="Accepted")

            # Handle requests
            accept = request.headers.get('Accept', '')

            if 'text/event-stream' in accept:
                # Client wants SSE stream
                response = await self._initiate_sse(request, messages, session_id, is_initialize)
                return response
            else:
                # Client wants JSON response (single response)
                # Return 202 for now - actual processing happens elsewhere
                headers = {}
                if is_initialize and not session_id:
                    # Create session for initialize request
                    new_session_id = self._create_session()
                    headers['Mcp-Session-Id'] = new_session_id

                return web.json_response(
                    {'status': 'received', 'message_count': len(messages)},
                    headers=headers
                )
                
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.stats['errors'] += 1
            return web.Response(status=500, text=str(e))
            
    async def _handle_sse(self, request: Request) -> StreamResponse:
        """Handle SSE connection requests (GET /mcp)."""
        try:
            # Security: Validate Origin
            if not self._validate_origin(request):
                return web.Response(status=403, text="Forbidden: Invalid origin")

            # Validate protocol version
            valid, _ = self._validate_protocol_version(request)
            if not valid:
                return web.Response(status=400, text="Unsupported protocol version")

            # Validate session
            session_id = request.headers.get('Mcp-Session-Id')
            if session_id and not self._validate_session(session_id):
                return web.Response(status=404, text="Session not found")

            return await self._initiate_sse(request, [], session_id, False)
        except Exception as e:
            logger.error(f"Error handling SSE request: {e}")
            return web.Response(status=500, text=str(e))

    async def _initiate_sse(
        self,
        request: Request,
        initial_messages: List[JSONRPCMessage],
        session_id: Optional[str] = None,
        is_initialize: bool = False
    ) -> StreamResponse:
        """Initiate SSE connection with session and resumability support."""
        # Validate origin (double-check)
        if not self._validate_origin(request):
            return web.Response(status=403, text="Forbidden: Invalid origin")

        # Create session if this is an initialize request
        if is_initialize and not session_id:
            session_id = self._create_session()

        # Create SSE response with security headers
        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Content-Type-Options': 'nosniff',
            }
        )

        # Add session ID header if we have a session
        if session_id:
            response.headers['Mcp-Session-Id'] = session_id
        
        await response.prepare(request)
        
        # Create client
        self.client_counter += 1
        client_id = f"client_{self.client_counter}"

        client = SSEClient(
            client_id=client_id,
            request=request,
            response=response,
            queue=asyncio.Queue(),
            last_ping=asyncio.get_event_loop().time(),
            session_id=session_id,
            event_counter=0
        )

        self.clients[client_id] = client

        try:
            # Check for Last-Event-ID header for resumable streams
            last_event_id = request.headers.get('Last-Event-ID')
            if last_event_id:
                logger.info(f"Resuming stream from event ID: {last_event_id}")
                await self._replay_events(client, last_event_id)

            # Send initial messages if any
            for message in initial_messages:
                await self.send_message(message)

            # Send welcome message
            await self._send_sse_event(client, 'connected', {'client_id': client_id})
            
            # Process client queue
            while self.running and not response.transport.is_closing():
                try:
                    # Wait for message with timeout
                    event_type, data = await asyncio.wait_for(
                        client.queue.get(), timeout=30.0
                    )
                    
                    if event_type == 'ping':
                        await self._send_sse_event(client, 'ping', {'timestamp': data})
                        client.last_ping = asyncio.get_event_loop().time()
                    elif event_type in ('message', 'batch'):
                        await self._send_sse_event(client, event_type, data)
                    elif event_type == 'close':
                        break
                        
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await client.queue.put(('ping', asyncio.get_event_loop().time()))
                    
        except Exception as e:
            logger.error(f"Error in SSE connection for {client_id}: {e}")
        finally:
            await self._close_client(client)
            
        return response
        
    async def _send_sse_event(
        self,
        client: SSEClient,
        event_type: str,
        data: Any,
        event_id: Optional[str] = None
    ) -> None:
        """Send SSE event to client with event ID for resumability."""
        try:
            # Generate event ID if not provided
            if event_id is None:
                event_id = self._generate_event_id(client)

            # Store event for resumability
            self._store_event(client.client_id, event_id, data)

            # Serialize data
            if isinstance(data, str):
                data_str = data
            else:
                data_str = json.dumps(data, separators=(',', ':'))

            # Build SSE event with ID
            event = f"id: {event_id}\nevent: {event_type}\ndata: {data_str}\n\n"
            await client.response.write(event.encode('utf-8'))
            await client.response.drain()

        except Exception as e:
            logger.error(f"Failed to send SSE event to {client.client_id}: {e}")
            raise
            
    async def _close_client(self, client: SSEClient) -> None:
        """Close a client connection."""
        try:
            if client.client_id in self.clients:
                del self.clients[client.client_id]
                
            if not client.response.transport.is_closing():
                await client.response.write_eof()
                
        except Exception as e:
            logger.error(f"Error closing client {client.client_id}: {e}")
            
    async def _ping_clients(self) -> None:
        """Periodically ping clients to keep connections alive."""
        while self.running:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                
                current_time = asyncio.get_event_loop().time()
                stale_clients = []
                
                for client in self.clients.values():
                    if current_time - client.last_ping > 60:  # 60 second timeout
                        stale_clients.append(client)
                    else:
                        await client.queue.put(('ping', current_time))
                        
                # Close stale clients
                for client in stale_clients:
                    logger.info(f"Closing stale client: {client.client_id}")
                    await self._close_client(client)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping task: {e}")
                
    async def _handle_health(self, request: Request) -> Response:
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'transport': 'sse',
            'running': self.running,
            'clients': len(self.clients)
        })
        
    async def _handle_stats(self, request: Request) -> Response:
        """Statistics endpoint."""
        stats = self.get_stats()
        stats['clients'] = {
            client_id: {
                'last_ping': client.last_ping,
                'queue_size': client.queue.qsize()
            }
            for client_id, client in self.clients.items()
        }
        return web.json_response(stats)
        
    def _parse_message(self, data: dict) -> Optional[JSONRPCMessage]:
        """Parse message data into appropriate MCP type."""
        try:
            # Determine message type
            if 'method' in data:
                if 'id' in data:
                    # Request
                    return JSONRPCRequest(**data)
                else:
                    # Notification
                    return JSONRPCNotification(**data)
            elif 'result' in data or 'error' in data:
                # Response
                return JSONRPCResponse(**data)
            else:
                logger.warning(f"Unknown message format: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            self.stats['errors'] += 1
            return None