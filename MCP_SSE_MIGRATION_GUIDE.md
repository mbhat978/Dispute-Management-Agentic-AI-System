# MCP SSE Migration Guide

## Overview

The MCP (Model Context Protocol) client has been migrated from a stdio-based architecture to a persistent Server-Sent Events (SSE) architecture. This change eliminates the overhead of spawning and killing the core banking server on every tool call, resulting in better performance and resource utilization.

## Architecture Changes

### Before (stdio_client)
- **Connection Model**: Spawned a new Python process for each tool call
- **Lifecycle**: Server started → tool executed → server killed
- **Overhead**: High (process creation/destruction on every call)
- **Resource Usage**: Multiple short-lived processes

### After (sse_client)
- **Connection Model**: Persistent HTTP/SSE connection to a running server
- **Lifecycle**: Server runs continuously, client connects as needed
- **Overhead**: Low (reuses existing connection)
- **Resource Usage**: Single long-running server process

## Files Modified

### 1. `backend/mcp_servers/core_banking_server.py`
**Changes:**
- Updated `mcp.run()` to use SSE transport on port 8001
- Server now runs as: `mcp.run(transport='sse', port=8001)`

### 2. `backend/mcp_client.py`
**Changes:**
- Removed `stdio_client` and `StdioServerParameters` imports
- Added `sse_client` import from `mcp.client.sse`
- Removed httpx client dependency (not needed for basic SSE)
- Updated `_call_mcp_tool_async()` to connect to `http://localhost:8001/sse`
- Simplified connection logic - each call creates a fresh SSE connection
- Removed complex connection pooling (SSE handles this efficiently)

### 3. `run_mcp_server.bat` (New File)
**Purpose:**
- Standalone script to start the MCP server independently
- Runs the server in SSE mode on port 8001
- Must be running before the application starts

## How to Use

### Step 1: Start the MCP Server

Before starting your application, you must start the MCP server:

```bash
# Windows
run_mcp_server.bat

# Or manually
cd backend\mcp_servers
python core_banking_server.py
```

The server will start and display:
```
Server running on port 8001
```

**Important:** Keep this terminal window open. The server must remain running for the application to work.

### Step 2: Start Your Application

In a separate terminal, start your FastAPI application as usual:

```bash
# Windows
run_app.bat

# Or manually
cd backend
uvicorn main:app --reload
```

### Step 3: Use the Application

The application will now connect to the persistent MCP server via SSE. All tool calls will be routed through the running server at `http://localhost:8001/sse`.

## Testing

A test script is provided to verify the SSE connection:

```bash
python test_mcp_sse.py
```

This will test:
1. Connection to the SSE server
2. Tool availability
3. Sample tool calls (get_transaction_details, get_customer_history, check_atm_logs)

## Benefits

1. **Performance**: No process spawning overhead on each tool call
2. **Resource Efficiency**: Single server process instead of multiple short-lived processes
3. **Scalability**: Better handling of concurrent requests
4. **Reliability**: Persistent connection reduces connection failures
5. **Debugging**: Easier to monitor and debug a single running server

## Connection Behavior

The current implementation creates a new SSE connection for each tool call but reuses the persistent server. This is efficient because:

- The server remains running (no startup cost)
- SSE connections are lightweight HTTP connections
- The MCP protocol handles connection management
- No need for complex connection pooling logic

## Troubleshooting

### Error: "Connection refused" or "Cannot connect to server"

**Solution:** Make sure the MCP server is running:
```bash
run_mcp_server.bat
```

### Error: "Port 8001 already in use"

**Solution:** Another process is using port 8001. Either:
1. Stop the other process
2. Change the port in both `core_banking_server.py` and `mcp_client.py`

### Server crashes or stops responding

**Solution:** Restart the MCP server:
1. Stop the server (Ctrl+C in the terminal)
2. Run `run_mcp_server.bat` again

### Tools return errors

**Solution:** Check the server logs in the terminal where `run_mcp_server.bat` is running. The server will display detailed error messages.

## Production Considerations

For production deployment, consider:

1. **Process Management**: Use a process manager (e.g., systemd, supervisord, PM2) to keep the MCP server running
2. **Health Checks**: Implement health check endpoints to monitor server status
3. **Auto-Restart**: Configure automatic restart on failure
4. **Logging**: Implement proper logging for the MCP server
5. **Monitoring**: Add metrics and monitoring for server performance
6. **Load Balancing**: For high-traffic scenarios, run multiple server instances behind a load balancer

## Future Enhancements

Potential improvements for the future:

1. **Connection Pooling**: Implement true connection pooling with session reuse
2. **Reconnection Logic**: Add automatic reconnection on connection loss
3. **Circuit Breaker**: Implement circuit breaker pattern for fault tolerance
4. **Health Monitoring**: Add health check endpoints
5. **Graceful Shutdown**: Implement proper cleanup on application shutdown

## Migration Checklist

- [x] Update core_banking_server.py to use SSE transport
- [x] Create run_mcp_server.bat script
- [x] Update mcp_client.py to use sse_client
- [x] Remove stdio_client dependencies
- [x] Test basic connectivity
- [ ] Update deployment documentation
- [ ] Update CI/CD pipelines (if applicable)
- [ ] Train team on new startup procedure

## Support

If you encounter issues with the SSE migration:

1. Check this guide's troubleshooting section
2. Review server logs for detailed error messages
3. Verify the server is running and accessible
4. Test with `test_mcp_sse.py` to isolate issues

---

**Made with Bob**