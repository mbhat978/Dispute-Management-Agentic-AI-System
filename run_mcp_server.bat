@echo off
echo Starting MCP Core Banking Server on port 8001...
echo.
echo The server will run as an SSE server at http://localhost:8001/sse
echo Press Ctrl+C to stop the server
echo.

cd backend\mcp_servers
python core_banking_server.py

pause

@REM Made with Bob
