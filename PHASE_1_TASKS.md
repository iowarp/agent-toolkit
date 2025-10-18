# Phase 1: Transport Integration & Testing

## Task 1: Protocol Compliance Audit ✅

###

 SSE Transport Issues Found

**Critical (Security)**:
- ❌ Line 265: `Access-Control-Allow-Origin: *` → Must validate Origin header
- ❌ No localhost binding enforcement → Should bind to 127.0.0.1 by default
- ❌ No authentication → Should implement for all connections

**Missing Features (MCP 2025-06-18)**:
- ❌ No `Mcp-Session-Id` header support
- ❌ No `Last-Event-ID` resumable streams
- ❌ No `MCP-Protocol-Version` header validation
- ❌ POST doesn't return proper responses based on message type

**Working Features** ✅:
- ✅ Single '/mcp' endpoint
- ✅ POST and GET support
- ✅ SSE stream implementation
- ✅ Message batching
- ✅ Client connection management
- ✅ Health/stats endpoints

### stdio Transport Status ✅
- ✅ Uses MCP SDK's stdio_server()
- ✅ Protocol compliant (newline-delimited JSON-RPC)
- ✅ Ready to use

## Task 2: Fix SSE Protocol Compliance

### 2.1 Add Origin Validation
```python
# sse_transport.py line ~250
async def _validate_origin(self, request: Request) -> bool:
    """Validate Origin header to prevent DNS rebinding."""
    origin = request.headers.get('Origin')
    if not origin:
        return True  # No origin header

    # Allow localhost origins only
    allowed = ['http://localhost', 'http://127.0.0.1',
               'https://localhost', 'https://127.0.0.1']
    return any(origin.startswith(allowed_origin) for allowed_origin in allowed)
```

### 2.2 Add Session Management
```python
# Add to SSETransport class
class SSETransport(BaseTransport):
    def __init__(self, config):
        super().__init__(config)
        self.sessions: Dict[str, SessionInfo] = {}

    def _create_session(self) -> str:
        """Create new session ID (UUID or JWT)."""
        import uuid
        return str(uuid.uuid4())

    async def _handle_post(self, request):
        # Check for Mcp-Session-Id header
        session_id = request.headers.get('Mcp-Session-Id')

        # On InitializeRequest, create session and return header
        if is_initialize_request(data):
            session_id = self._create_session()
            response.headers['Mcp-Session-Id'] = session_id
```

### 2.3 Add Resumable Streams
```python
# Add event IDs to SSE events
async def _send_sse_event(self, client, event_type, data):
    event_id = self._generate_event_id(client)
    event = f"id: {event_id}\nevent: {event_type}\ndata: {data}\n\n"

# Support Last-Event-ID header
async def _handle_sse(self, request):
    last_event_id = request.headers.get('Last-Event-ID')
    if last_event_id:
        # Resume from this event ID
        await self._replay_events_after(client, last_event_id)
```

### 2.4 Add Protocol Version Validation
```python
async def _handle_post(self, request):
    # Validate protocol version
    protocol_version = request.headers.get('MCP-Protocol-Version', '2025-03-26')
    if protocol_version not in SUPPORTED_VERSIONS:
        return web.Response(status=400, text="Unsupported protocol version")
```

### 2.5 Fix localhost Binding
```python
# In config.py or SSETransport.__init__
if config.host is None or config.host == '0.0.0.0':
    # Default to localhost for security
    config.host = '127.0.0.1'
```

## Task 3: Test stdio Mode with iowarp

```bash
# From iowarp-mcps root
cd /home/akougkas/projects/iowarp-mcps

# Test 1: Verify it starts
uvx --from . iowarp-mcps hdf5

# Test 2: Check it uses stdio
# Should print "HDF5 MCP Server started" to stderr
# Should wait for stdin

# Test 3: Send test message
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uvx --from . iowarp-mcps hdf5

# Test 4: Integration with client
# (Would need MCP client to fully test)
```

## Task 4: Copy & Adapt Tests

```bash
# Copy test suite
cd /home/akougkas/projects/iowarp-mcps/mcps/HDF5
cp -r /home/akougkas/projects/hdf5-mcp-server/tests/* tests/

# Update imports in tests
find tests -name "*.py" -exec sed -i 's/from hdf5_mcp_server/from src/g' {} \;

# Run tests
uv run pytest tests/ -v
```

## Task 5: Documentation

### Create docs/TRANSPORTS.md
```markdown
# Transport Support

HDF5 MCP supports two transports:

## stdio (Default)
For subprocess-launched servers (Cursor, Claude Code, etc.)

Usage: `uvx iowarp-mcps hdf5`

## SSE/HTTP (Advanced)
For remote servers, multiple clients, streaming

Usage: `uvx iowarp-mcps hdf5 --transport sse --host localhost --port 8765`

### Security
- Origin validation enabled
- localhost-only binding by default
- Session management required
```

### Update README.md
Add transport section showing both modes.

## Task 6: Integration Testing

### Test Matrix

| Mode | Test | Expected Result |
|------|------|----------------|
| stdio | Start server | Starts, waits for stdin |
| stdio | Send tools/list | Returns tool list JSON |
| stdio | Large response (1MB) | Handles newline-delimited |
| stdio | 25+ tool calls | All tools work |
| SSE | Start server | HTTP server on localhost:8765 |
| SSE | GET /mcp | Opens SSE stream |
| SSE | POST /mcp | Returns 202 or SSE stream |
| SSE | Session management | Mcp-Session-Id header works |
| SSE | Multiple clients | Each gets own session |
| SSE | Stream large dataset | GB-sized response streams |
| SSE | Origin validation | Rejects bad origins |

## Timeline

### Week 1: Protocol Fixes
- Day 1-2: Fix SSE security issues (Origin, localhost)
- Day 3-4: Add session management
- Day 5: Add resumable streams, protocol version

### Week 2: Testing
- Day 1-2: Copy and adapt test suite
- Day 3: stdio mode testing
- Day 4: SSE mode testing
- Day 5: Integration testing

### Week 3: Documentation & Finalization
- Day 1-2: Write docs (TRANSPORTS.md, ARCHITECTURE.md, EXAMPLES.md)
- Day 3-4: Performance benchmarking
- Day 5: Final validation, prepare for merge

## Success Criteria

### Functional ✅
- [ ] stdio mode: `uvx iowarp-mcps hdf5` works
- [ ] All 25+ tools work via stdio
- [ ] SSE mode: Server starts on localhost
- [ ] SSE mode: Session management works
- [ ] SSE mode: Resumable streams work

### Security ✅
- [ ] Origin validation implemented
- [ ] localhost-only binding by default
- [ ] No authentication bypass vulnerabilities
- [ ] Session IDs are cryptographically secure

### Protocol Compliance ✅
- [ ] stdio: MCP 2025-06-18 compliant
- [ ] SSE: MCP 2025-06-18 compliant
- [ ] Protocol version header supported
- [ ] All required headers present

### Documentation ✅
- [ ] TRANSPORTS.md complete
- [ ] ARCHITECTURE.md describes transport layer
- [ ] EXAMPLES.md shows both modes
- [ ] README.md updated

### Testing ✅
- [ ] All existing tests pass
- [ ] Transport-specific tests added
- [ ] Integration tests pass
- [ ] Performance benchmarks done

## Next Steps (Now)

1. ✅ Create this plan
2. Start with security fixes to SSE transport
3. Test stdio mode works with iowarp
4. Copy test suite
5. Run comprehensive tests
6. Document everything
7. Merge to main

This makes HDF5 MCP the exemplary multi-transport implementation for iowarp.
