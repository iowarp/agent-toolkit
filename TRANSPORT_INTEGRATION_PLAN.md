# HDF5 MCP Transport Integration Plan

## Vision

Make HDF5 MCP the **exemplary multi-transport implementation** for all iowarp MCPs, supporting:
- **stdio** (default) - subprocess mode for Claude Code, Cursor, etc.
- **SSE/HTTP** (advanced) - for streaming large datasets, remote servers, multiple clients

This becomes the template for upgrading all iowarp MCPs.

## Current State Analysis

### What We Have ✅

**server.py** (lines 1-427):
- Uses MCP SDK's `stdio_server()`
- Registers tools, resources, prompts
- Full HDF5Tools implementation with 25+ tools
- Working stdio implementation

**main.py** + **transports/**:
- Custom transport abstraction (BaseTransport)
- stdio_transport.py - Enhanced stdio with batching
- sse_transport.py - HTTP/SSE for remote access
- TransportManager - Multi-transport orchestration
- Mode switching: "stdio" vs "enhanced"

### The Integration Gap

**Problem**: Two parallel implementations
1. `server.py` - uses MCP SDK directly
2. `main.py` - tries to wrap everything in custom transport layer

**Current main.py approach**:
```python
if args.mode == "stdio":
    await run_stdio_mode()  # Calls server.py's run_server()
else:
    await run_enhanced_mode()  # Uses custom transport layer
```

This creates **redundancy** and **confusion**.

## MCP Protocol Compliance Check

### stdio Transport ✅
**Protocol Requirements**:
- Newline-delimited JSON-RPC over stdin/stdout
- No embedded newlines in messages
- stderr for logging only

**Our Implementation** (server.py):
```python
from mcp.server.stdio import stdio_server
async with stdio_server() as (read_stream, write_stream):
```
✅ Uses MCP SDK's built-in stdio → **Protocol compliant**

### Streamable HTTP Transport ✅
**Protocol Requirements** (2025-06-18):
- Single MCP endpoint supporting POST and GET
- POST for client→server messages
- GET for optional SSE stream (server→client)
- `Mcp-Session-Id` header for session management
- Support for resumable streams

**Our Implementation** (sse_transport.py):
- Has HTTP POST/GET handling
- SSE stream support
- Session management
- Message batching

Need to **verify** full compliance with 2025-06-18 spec.

## Integration Strategy

### Option 1: Unified Entry Point (RECOMMENDED)

**Concept**: Single main.py that:
1. Default mode: stdio (uses MCP SDK)
2. Advanced mode: SSE/HTTP (uses custom transport)
3. Configuration-driven transport selection
4. Seamless fallback

**Entry Point** (main.py):
```python
def main():
    # Parse args
    if args.transport == "stdio" or not args.transport:
        # Default: Use MCP SDK's stdio_server
        asyncio.run(run_stdio_mode(args.data_dir))
    elif args.transport == "sse":
        # Advanced: Use custom SSE transport
        asyncio.run(run_sse_mode(args.data_dir, args.host, args.port))
```

**Benefits**:
- Simple default (stdio works out of box)
- Advanced features available when needed
- Clear separation of concerns
- Easy to test each mode

### Option 2: Unified Server Architecture

**Concept**: Single HDF5Server class that:
- Supports multiple transports internally
- Transport-agnostic tool registration
- Dynamic transport switching

**Structure**:
```python
class HDF5Server:
    def __init__(self):
        self.mcp_server = Server("hdf5-mcp")
        self.transports = TransportManager()

    async def start(self, transports=["stdio"]):
        # Register tools once
        self._register_tools()

        # Start requested transports
        for transport_type in transports:
            await self.transports.start(transport_type)
```

**Benefits**:
- Single codebase
- Tools registered once, work on all transports
- More complex architecture

## Recommended Approach: Option 1 (Phased)

### Phase 1: Validate stdio Mode ✅
**Goal**: Ensure default stdio mode works perfectly with iowarp

**Tasks**:
1. ✅ server.py already works with stdio_server()
2. ✅ main.py calls server.py in stdio mode
3. Test: `uvx iowarp-mcps hdf5` works
4. Test: All 25+ tools functional via stdio
5. Test: Large dataset handling via stdio

**Status**: Should already work, needs testing

### Phase 2: Validate SSE Mode 🔧
**Goal**: Ensure SSE transport is protocol-compliant and functional

**Tasks**:
1. Review sse_transport.py against MCP 2025-06-18 spec
2. Check HTTP endpoint implementation
3. Verify session management
4. Test streaming for large datasets
5. Document SSE mode usage

**Verification Checklist**:
- [ ] Single MCP endpoint (POST + GET)
- [ ] `Mcp-Session-Id` header support
- [ ] Resumable SSE streams with `Last-Event-Id`
- [ ] Proper Content-Type headers
- [ ] Origin validation for security
- [ ] Local binding (localhost only by default)

### Phase 3: Integration & Documentation 📝
**Goal**: Make both modes seamlessly usable

**Tasks**:
1. Clean up main.py entry point
2. Add environment variable config
3. Document transport selection
4. Create usage examples
5. Write migration guide for other MCPs

### Phase 4: Testing & Validation ✅
**Goal**: Comprehensive testing

**Tasks**:
1. Copy tests from hdf5-mcp-server
2. Add transport-specific tests
3. Integration tests for both modes
4. Performance benchmarks
5. Security validation (SSE mode)

## Configuration Design

### Environment Variables
```bash
# Data directory
HDF5_DATA_DIR=/path/to/data

# Transport selection
HDF5_TRANSPORT=stdio              # stdio (default) or sse
HDF5_SSE_HOST=localhost           # SSE mode only
HDF5_SSE_PORT=8765                # SSE mode only

# Performance
HDF5_CACHE_SIZE=1000
HDF5_NUM_WORKERS=4
HDF5_ENABLE_BATCHING=true         # Message batching
```

### CLI Arguments
```bash
# Default (stdio)
uvx iowarp-mcps hdf5

# With data directory
uvx iowarp-mcps hdf5 --data-dir /path/to/data

# SSE mode
uvx iowarp-mcps hdf5 --transport sse --host localhost --port 8765

# Debug mode
uvx iowarp-mcps hdf5 --log-level DEBUG
```

## Implementation Steps

### Step 1: Review & Audit (Now)
- [x] Understand current transport implementation
- [ ] Check MCP protocol compliance
- [ ] Identify integration points
- [ ] Document current behavior

### Step 2: Verify stdio Default
- [ ] Test server.py standalone
- [ ] Test main.py stdio mode
- [ ] Verify iowarp launcher compatibility
- [ ] Benchmark performance

### Step 3: Validate SSE Implementation
- [ ] Review sse_transport.py line-by-line
- [ ] Check against MCP 2025-06-18 spec
- [ ] Add missing protocol features if any
- [ ] Security audit (Origin, localhost binding)

### Step 4: Clean Integration
- [ ] Simplify main.py if needed
- [ ] Remove redundant code
- [ ] Ensure both modes use same tool registry
- [ ] Add mode switching logic

### Step 5: Documentation
- [ ] README: Usage for both modes
- [ ] ARCHITECTURE.md: Transport design
- [ ] EXAMPLES.md: Streaming use cases
- [ ] docs/TRANSPORTS.md: Protocol compliance

### Step 6: Testing
- [ ] Copy test suite from hdf5-mcp-server
- [ ] Add stdio transport tests
- [ ] Add SSE transport tests
- [ ] Integration tests
- [ ] Performance benchmarks

## Success Criteria

### Functional
- ✅ stdio mode: `uvx iowarp-mcps hdf5` works
- ✅ All 25+ tools work in stdio mode
- ✅ SSE mode: Server starts on HTTP endpoint
- ✅ SSE mode: Can handle multiple clients
- ✅ Both modes: Same tool functionality

### Performance
- ✅ stdio: Handles MB-sized responses
- ✅ SSE: Streams GB-sized datasets
- ✅ Batching reduces round-trips
- ✅ Caching works in both modes

### Protocol Compliance
- ✅ stdio: Newline-delimited JSON-RPC
- ✅ SSE: 2025-06-18 spec compliant
- ✅ Session management works
- ✅ Resumable streams work

### Security
- ✅ SSE: Origin validation
- ✅ SSE: Localhost-only default
- ✅ No credential leaks in logs
- ✅ Proper error handling

## Next Actions

1. **Audit sse_transport.py** against MCP 2025-06-18 spec
2. **Test stdio mode** with iowarp launcher
3. **Review main.py** integration logic
4. **Document** transport architecture
5. **Copy tests** from hdf5-mcp-server
6. **Validate** both modes work

This makes HDF5 MCP the gold standard for iowarp MCPs with multi-transport support.
