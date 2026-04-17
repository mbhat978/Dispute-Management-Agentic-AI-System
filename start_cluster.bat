@echo off
echo Starting Enterprise AI Banking Cluster...

echo Launching Core Banking MCP Server (Port 8001)...
start "Core Banking MCP" cmd /k "call venv\Scripts\activate && python backend/mcp_servers/core_banking_server.py"

echo Launching Compliance MCP Server (Port 8002)...
start "Compliance MCP" cmd /k "call venv\Scripts\activate && python backend/mcp_servers/compliance_server.py"

echo Waiting for MCP servers to initialize...
timeout /t 3 /nobreak

echo Launching FastAPI AI Orchestrator (Port 8000)...
start "FastAPI Backend" cmd /k "call venv\Scripts\activate && uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo Cluster launched successfully!

echo Starting Frontend (Next.js on port 3000)...
start "Frontend" cmd /k "cd frontend && npm run dev"

@REM Made with Bob
