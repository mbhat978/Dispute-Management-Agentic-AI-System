# 🚀 Dispute Management Agentic AI System - Installation Guide

Complete step-by-step guide to install and run the Banking Dispute Management System with multi-agent AI capabilities and MCP (Model Context Protocol) servers.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Project Overview](#project-overview)
4. [Installation Steps](#installation-steps)
   - [Backend Setup](#backend-setup)
   - [Frontend Setup](#frontend-setup)
   - [MCP Servers Setup](#mcp-servers-setup)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Running the Application](#running-the-application)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## 🖥️ System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.9 or higher (3.11+ recommended)
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 500MB free space

---

## 📦 Prerequisites

Before starting, ensure you have the following installed:

### 1. Python
Check if Python is installed:
```bash
python --version
# or
python3 --version
```

If not installed, download from [python.org](https://www.python.org/downloads/)

### 2. Node.js and npm
Check if Node.js and npm are installed:
```bash
node --version
npm --version
```

If not installed, download from [nodejs.org](https://nodejs.org/)

**Note:** This project uses:
- Next.js 16.2.3
- React 19.2.4
- These are newer versions that require Node.js 18+ for optimal compatibility

### 3. Git (Optional but recommended)
```bash
git --version
```

Download from [git-scm.com](https://git-scm.com/)

### 4. OpenAI API Key
You'll need an OpenAI API key for the AI agents to function.
- Sign up at [platform.openai.com](https://platform.openai.com/)
- Generate an API key from your account dashboard

---

## 🏗️ Project Overview

This system consists of four main components:

### Backend (FastAPI + Python)
- **Location**: `backend/` directory
- **Framework**: FastAPI
- **Database**: SQLite
- **AI Framework**: LangChain + LangGraph
- **Port**: 8000

### Frontend (Next.js + React)
- **Location**: `frontend/` directory
- **Framework**: Next.js 16.x with React 19.x
- **UI Library**: Shadcn/ui + Tailwind CSS
- **Port**: 3000

### MCP Servers (Model Context Protocol)
- **Core Banking Server**: Port 8001 - Core banking operations
- **Compliance Server**: Port 8002 - Policy and compliance queries
- **Enhanced Banking Tools Server**: Port 8003 - Extended banking services & Vision AI
- **Framework**: FastMCP (SSE transport)

### Multi-Agent System
- **Triage Agent**: Classifies disputes using ReAct methodology
- **Investigator Agent**: Gathers evidence via MCP tools
- **Decision Agent**: Makes final decisions with business rules
- **Orchestrator**: LangGraph-based workflow coordination

---

## 🔧 Installation Steps

### Backend Setup

#### Step 1: Navigate to Backend Directory
```bash
cd backend
```

#### Step 2: Create Python Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt.

#### Step 3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages installed:**
- fastapi - Web framework
- uvicorn[standard] - ASGI server
- sqlalchemy - ORM
- pydantic - Data validation
- langgraph - Agent orchestration
- langchain - LLM framework
- langchain-openai - OpenAI integration
- openai - OpenAI API client
- python-dotenv - Environment variables
- mcp - Model Context Protocol
- loguru - Logging
- aiosqlite - LangGraph SQLite checkpoint support
- slowapi / tenacity / structlog - runtime utilities
- And other dependencies

**Validated source of truth:** use `backend/requirements.txt` for backend dependency versions. The root `requirements.txt` is older and does not fully reflect the backend runtime.

**Installation time**: 2-5 minutes depending on internet speed.

#### Step 4: Verify Backend Installation
```bash
python -c "import fastapi; import sqlalchemy; import langchain; print('✅ All backend packages installed successfully!')"
```

---

### Frontend Setup

#### Step 1: Navigate to Frontend Directory
Open a **new terminal window** (keep backend terminal open) and navigate:
```bash
cd frontend
```

#### Step 2: Install Node.js Dependencies
```bash
npm install
```

**Expected packages installed:**
- next@16.2.3
- react@19.2.4
- react-dom@19.2.4
- tailwindcss@4
- shadcn components
- And other dependencies

**Installation time**: 3-7 minutes depending on internet speed.

#### Step 3: Verify Frontend Installation
```bash
npm list next react
```

Should show installed versions without errors.

---

### MCP Servers Setup

The system uses three MCP (Model Context Protocol) servers for tool execution:

#### Step 1: Verify MCP Server Files

Check that MCP server files exist:
```bash
cd backend/mcp_servers
ls -la  # macOS/Linux
dir     # Windows
```

You should see:
- `core_banking_server.py` - Core banking MCP server
- `compliance_server.py` - Compliance MCP server
- `enhanced_banking_tools.py` - Enhanced banking tools MCP server
- `banking_tools.py` - Shared banking tool implementations used by MCP servers

#### Step 2: Understanding MCP Architecture

MCP servers run as separate processes and communicate via SSE (Server-Sent Events):

```
┌─────────────────────────────────────────────┐
│         FastAPI Backend (Port 8000)         │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │   MCP Client (mcp_client.py)        │   │
│  │   Connects to all MCP servers       │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
              │         │         │
              ▼         ▼         ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Core      │ │ Compliance  │ │ Enhanced    │
    │  Banking    │ │  Server     │ │ Banking     │
    │  (8001)     │ │  (8002)     │ │ Tools (8003)│
    └─────────────┘ └─────────────┘ └─────────────┘
```

#### Step 3: Available Banking Tools

The MCP servers provide 15+ specialized tools:

**Core Banking Server (Port 8001):**
- `get_transaction_details`
- `get_customer_history`
- `check_atm_logs`
- `check_duplicate_transactions`
- `block_card`
- `issue_replacement_card`
- `initiate_refund`
- `route_to_human`
- `get_loan_details`
- `check_merchant_refund_status`
- `verify_receipt_amount`
- `initiate_chargeback`
- `analyze_receipt_evidence`
- `calculate_timeline_from_evidence`

**Compliance Server (Port 8002):**
- `query_compliance_policy`

**Enhanced Banking Tools Server (Port 8003):**
- `get_delivery_tracking_status`
- `check_merchant_reputation_score`
- `get_merchant_dispute_history`
- `check_subscription_status`
- `verify_subscription_cancellation`
- `get_refund_timeline`

**Important:** the FastAPI backend connects to these servers through SSE endpoints configured in `backend/mcp_client.py`:
- `http://localhost:8001/sse`
- `http://localhost:8002/sse`
- `http://localhost:8003/sse`

---

## ⚙️ Configuration

### Step 1: Create Environment File

Navigate to the **project root directory** (parent of `backend/` and `frontend/`):

```bash
cd ..  # If you're in frontend/ or backend/
```

Create `.env` file from the example:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

### Step 2: Configure OpenAI API Key

Edit the `.env` file with your favorite text editor:

```bash
# Windows
notepad .env

# macOS
open -e .env

# Linux
nano .env
```

Replace the placeholder with your actual OpenAI API key:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# Optional: Specify which model to use
OPENAI_MODEL=gpt-4-turbo-preview

# Optional: Set temperature for LLM responses (0.0 to 1.0)
OPENAI_TEMPERATURE=0.0

# LangSmith Configuration (Optional - for Enterprise Observability)
# Sign up at https://smith.langchain.com/ to get API key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
LANGCHAIN_PROJECT="dispute-management-agents"
```

**About LangSmith (Optional):**
- LangSmith provides observability and debugging for LangChain applications
- It's **completely optional** - the system works without it
- If you want to use it:
  1. Sign up at [smith.langchain.com](https://smith.langchain.com/)
  2. Get your API key from the dashboard
  3. Add it to your `.env` file
- If you don't want to use it, simply leave the default values or remove these lines

**⚠️ Important**: 
- Never commit `.env` file to version control
- Keep your API key secure
- The `.env.example` file is safe to commit (no actual keys)

### Step 3: Verify Environment Configuration

```bash
# Windows (PowerShell)
Get-Content .env

# macOS/Linux
cat .env
```

Ensure your API key is properly set.

---

## 🗄️ Database Setup

The system uses SQLite database which will be automatically created. However, you need to seed it with test data.

### Step 1: Navigate to Backend Directory
```bash
cd backend
```

### Step 2: Activate Virtual Environment (if not already active)
```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

### Step 3: Run Database Seed Script
```bash
python seed_data.py
```

**Expected output (abridged):**
```
Clearing existing data...
✓ Database cleared.

📋 Creating 6 customers...
💰 Creating loan accounts...
✅ Creating common successful transactions...
🎯 Creating test scenario transactions...
📊 Creating High-Risk Merchant History: ShopXYZ Online

DATABASE SEEDING SUMMARY
...
✅ Database seeding completed successfully!
```

**Validated notes from the actual seed script:**
- Creates **6 customers**
- Creates **1 loan account**
- Creates common transactions plus scenario-specific transactions for all 10 scenarios
- Creates ATM logs for ATM scenarios
- Creates **15 historical ShopXYZ disputes** for risk-pattern testing
- Uses the shared SQLite database at `backend/dispute_management.db`

### Step 4: Verify Database Creation
Check that `dispute_management.db` file exists:

```bash
# Windows (PowerShell)
Test-Path dispute_management.db

# macOS/Linux
ls -lh dispute_management.db
```

**Database file location**: `backend/dispute_management.db`

### What Data Was Created?

The seed script creates comprehensive test scenarios for all 10 dispute types:

1. **6 Customers** with different profiles:
   - Priya Sharma (Premium) - Fraud scenarios
   - Rahul Verma (Gold) - Merchant disputes
   - Ananya Patel (Basic) - ATM failures
   - Vikram Singh (Premium) - Duplicate charges and EMI disputes
   - Meera Reddy (Gold) - Subscription and refund disputes
   - Karthik Menon (Basic) - Incorrect amount and quality/service disputes

2. **25+ Transactions** covering:
   - International fraud patterns
   - Merchant disputes (Amazon, high-risk merchants)
   - ATM withdrawals with hardware faults
   - Duplicate charges within 5 minutes
   - Overcharged amounts
   - Subscription charges
   - Loan EMI payments
   - Refund scenarios
   - Quality/service disputes
   - Chargeback scenarios

3. **ATM Logs** with realistic fault codes:
   - `DISPENSE_FAULT`
   - `200_DISPENSED`

4. **15 Historic Disputes** for one customer:
   - Establishes high-risk merchant patterns
   - Tests fraud detection algorithms

5. **Loan Accounts** for EMI dispute testing
6. **Transaction IDs for quick testing** are printed by the seed script summary

For detailed scenario information, see `AGENT_TESTING_GUIDE.md`.

---

## 🚀 Running the Application

### Quick Start (Recommended)

Use the provided batch file to start all servers at once:

**Windows:**
```bash
start_cluster.bat
```

This will automatically start:
1. Core Banking MCP Server (Port 8001)
2. Compliance MCP Server (Port 8002)
3. Enhanced Banking Tools MCP Server (Port 8003)
4. FastAPI Backend (Port 8000)
5. Next.js Frontend (Port 3000)

**Validated behavior from `start_cluster.bat`:**
- Assumes a Python virtual environment already exists at the project root as `venv`
- Launches MCP servers first, waits 5 seconds, then starts backend and frontend
- Starts frontend with `npm run dev`
- Starts backend with `uvicorn main:app --host 0.0.0.0 --port 8000`

**Important:** `run_app.bat` is a simpler launcher that creates `backend/venv` if needed, installs dependencies, and starts only backend + frontend. It does **not** start MCP servers, so use `start_cluster.bat` for full agent workflows.

### Manual Start (Alternative)

If you prefer to start servers individually, you'll need **five terminal windows**.

#### Terminal 1: Core Banking MCP Server
```bash
cd backend
python mcp_servers/core_banking_server.py
```

#### Terminal 2: Compliance MCP Server
```bash
cd backend
python mcp_servers/compliance_server.py
```

#### Terminal 3: Enhanced Banking Tools MCP Server
```bash
cd backend
python mcp_servers/enhanced_banking_tools.py
```

#### Terminal 4: FastAPI Backend

#### Step 1: Navigate to Backend and Activate Environment
```bash
cd backend
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

#### Step 2: Start FastAPI Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Note:** `python main.py` is not the documented startup path in this repository. Use `uvicorn main:app ...` as used by the batch launchers.

**Expected output:**
```
Creating database tables...
Database tables created successfully!
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ **Backend is now running on**: `http://localhost:8000`

**Keep this terminal window open!**

---

#### Terminal 5: Next.js Frontend

#### Step 1: Open New Terminal and Navigate to Frontend
```bash
cd frontend
```

#### Step 2: Start Next.js Development Server
```bash
npm run dev
```

**Expected output:**
```
  ▲ Next.js 16.2.3
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Starting...
 ✓ Ready in 2.5s
```

✅ **Frontend is now running on**: `http://localhost:3000`

**Keep this terminal window open!**

---

## ✅ Verification

### 1. Verify Backend API

Open your browser and visit:

**API Documentation (Swagger UI):**
```
http://localhost:8000/docs
```

You should see interactive API documentation with all available endpoints.

**Alternative Documentation (ReDoc):**
```
http://localhost:8000/redoc
```

**Health Check:**
```
http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy"
}
```

**Test API Endpoints:**

Using curl or browser:
```bash
# Get customer count
curl http://localhost:8000/customers/count

# Get transaction count
curl http://localhost:8000/transactions/count

# Get dispute count
curl http://localhost:8000/disputes/count
```

### 2. Verify Frontend Application

Open your browser and visit:
```
http://localhost:3000
```

You should see the Banking Dispute Management System homepage.

**Available Pages:**
- **Home**: `http://localhost:3000/`
- **Customer Portal**: `http://localhost:3000/customer`
- **Employee Dashboard**: `http://localhost:3000/employee`
- **Ticket Details**: `http://localhost:3000/ticket/[id]` (e.g., `/ticket/1`)

### 3. Test End-to-End Functionality

1. **Navigate to Customer Portal**: `http://localhost:3000/customer`
2. **Submit a test dispute** (if form is available)
3. **Check Employee Dashboard**: `http://localhost:3000/employee`
4. **View dispute tickets and their AI agent processing**

### 4. Verify MCP Servers

Check that all MCP servers are running:

```bash
# Check ports
netstat -an | findstr "8001 8002 8003"  # Windows
lsof -i :8001,8002,8003                  # macOS/Linux
```

Expected: All three ports should show LISTENING status.

### 5. Verify Dispute and Analytics APIs

Useful endpoints confirmed from `backend/main.py`:

```bash
curl http://localhost:8000/api/disputes
curl http://localhost:8000/api/disputes/1
curl http://localhost:8000/api/analytics
```

### 6. Verify Streaming Endpoints

The backend also exposes SSE streams for live UI updates:

```bash
http://localhost:8000/api/disputes/stream
http://localhost:8000/api/logs/stream
```

### 7. Test Complete Dispute Processing

Submit a test dispute through the UI or API:

```bash
curl -X POST http://localhost:8000/api/disputes/process \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 15,
    "customer_id": 3,
    "customer_query": "ATM did not dispense cash but my account was debited"
  }'
```

Expected response with full agent workflow:
```json
{
  "status": "success",
  "ticket_id": 1,
  "dispute_category": "atm_failure",
  "final_decision": "auto_approved",
  "triage_confidence": 0.95,
  "investigation_confidence": 0.92,
  "decision_confidence": 0.95,
  "audit_trail": [...]
}
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: MCP Servers Not Starting

**Error**: `Address already in use` for ports 8001, 8002, or 8003

**Solution**:
```bash
# Windows - Kill processes on MCP ports
netstat -ano | findstr "8001 8002 8003"
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8001,8002,8003 | xargs kill -9
```

Then restart using `start_cluster.bat` or manually.

#### Issue 2: MCP Connection Errors

**Error**: `Failed to connect to MCP server` or `Connection refused`

**Solution**:
1. Verify MCP servers are running:
   ```bash
   netstat -an | findstr "8001 8002 8003"
   ```
2. Check MCP server logs for errors
3. Ensure no firewall blocking localhost connections
4. Restart MCP servers individually to identify the failing one

#### Issue 3: Port Already in Use (Backend/Frontend)

**Error**: `Address already in use` or `Port 8000/3000 is already in use`

**Solution**:

**For Backend (Port 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

**For Frontend (Port 3000):**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:3000 | xargs kill -9
```

Or use different ports:
```bash
# Backend
uvicorn main:app --reload --port 8001

# Frontend
npm run dev -- -p 3001
```

---

#### Issue 2: Module Not Found Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'` or similar

**Solution**:
1. Ensure virtual environment is activated (you should see `(venv)` in prompt)
2. Reinstall dependencies:
```bash
cd backend
pip install -r requirements.txt
```

---

#### Issue 3: OpenAI API Key Not Found

**Error**: `OpenAI API key not found` or authentication errors

**Solution**:
1. Verify `.env` file exists in project root
2. Check API key format: `OPENAI_API_KEY=sk-proj-...`
3. Ensure no extra spaces or quotes around the key
4. Restart backend server after updating `.env`

---

#### Issue 4: Database Connection Errors

**Error**: `Could not connect to database` or `Table doesn't exist`

**Solution**:
1. Delete existing database:
```bash
cd backend
rm dispute_management.db  # macOS/Linux
del dispute_management.db  # Windows
```

2. Re-run seed script:
```bash
python seed_data.py
```

---

#### Issue 5: Frontend Build Errors

**Error**: `Module not found` or `Cannot find module` in frontend

**Solution**:
1. Delete node_modules and reinstall:
```bash
cd frontend
rm -rf node_modules package-lock.json  # macOS/Linux
# Windows: manually delete node_modules folder
npm install
```

2. Clear Next.js cache:
```bash
rm -rf .next  # macOS/Linux
# Windows: manually delete .next folder
npm run dev
```

---

#### Issue 6: CORS Errors

**Error**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**:
The backend is configured to allow `http://localhost:3000`. If using different port:

Edit `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Add your port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

#### Issue 7: Python Virtual Environment Issues

**Error**: Cannot activate virtual environment

**Solution**:

**Windows PowerShell Execution Policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Recreate virtual environment:**
```bash
cd backend
rm -rf venv  # or manually delete venv folder
python -m venv venv
# Activate and reinstall
pip install -r requirements.txt
```

---

## 📚 Next Steps

### 1. Explore the System

- **API Documentation**: `http://localhost:8000/docs`
- **Agent Testing Guide**: See `AGENT_TESTING_GUIDE.md`
- **Project Documentation**: See `PROJECT_DOCUMENTATION.md`
- **MCP Architecture**: See MCP server files in `backend/mcp_servers/`

### 2. Test All 10 Dispute Scenarios

Follow the comprehensive testing guide:
```bash
# Open the testing guide
cat AGENT_TESTING_GUIDE.md
```

Test scenarios include:
1. Fraudulent Transaction (Auto-Decision)
2. Merchant Dispute - Item Not Delivered (Human-in-Loop)
3. ATM Dispute - Cash Not Dispensed
4. Duplicate Transaction
5. Incorrect Amount - Overcharged
6. Subscription Dispute
7. Loan/EMI Dispute
8. Refund Not Received
9. Quality/Service Dispute
10. Chargeback Scenario

### 3. Understand the Multi-Agent System

The system uses a sophisticated ReAct (Reasoning + Acting) architecture:

**Triage Agent** (GPT-3.5-turbo):
- Classifies disputes into categories
- Confidence scoring
- Clarification handling

**Investigator Agent** (GPT-4):
- Dynamic tool selection via MCP
- Evidence gathering and validation
- Iterative re-investigation

**Decision Agent** (GPT-4):
- Business rule validation
- Risk assessment
- Final decision with justification

**Orchestrator** (LangGraph):
- Workflow coordination
- Dynamic routing
- State management

### 4. Test MCP Tools Individually

Test specific banking tools:
```bash
cd backend
python -c "
from mcp_client import call_tool
result = call_tool('get_transaction_details', transaction_id=1)
print(result)
"
```

### 3. Development Workflow

**Backend Development:**
```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1
# Make changes to Python files
# Server auto-reloads with --reload flag
```

**Frontend Development:**
```bash
cd frontend
# Make changes to React/Next.js files
# Browser auto-refreshes
```

### 4. Add New Features

**Add New API Endpoint:**
1. Edit `backend/main.py`
2. Add new route function
3. Test at `http://localhost:8000/docs`

**Add New Frontend Page:**
1. Create file in `frontend/app/your-page/page.tsx`
2. Access at `http://localhost:3000/your-page`

### 5. Production Deployment

For production deployment, consider:
- Use PostgreSQL instead of SQLite
- Set up proper environment variables
- Configure HTTPS
- Use production-grade ASGI server (Gunicorn + Uvicorn)
- Build frontend: `npm run build` and `npm start`
- Set up monitoring and logging
- Implement rate limiting
- Add authentication/authorization

---

## 📖 Additional Resources

### Documentation Files
- `README.md` - Project overview and quick start
- `PROJECT_DOCUMENTATION.md` - Complete system documentation
- `AGENT_TESTING_GUIDE.md` - Comprehensive testing scenarios
- `INSTALLATION_GUIDE.md` - This file
- `IMPLEMENTATION_GAP_ANALYSIS.md` - Feature implementation status

### API Endpoints Reference

**Health & Info:**
- `GET /` - Root endpoint, API status
- `GET /health` - Health check

**Customers:**
- `GET /api/customers` - List all customers
- `GET /api/customers/{id}/transactions` - Get customer transaction history

**Disputes (Core Endpoints):**
- `GET /api/disputes` - List all disputes with filters
- `GET /api/disputes/{id}` - Get dispute details with full audit trail
- `POST /api/disputes/process` - **Process new dispute through AI workflow** (SSE streaming)
- `POST /api/disputes/{id}/resolve` - Human resolution of dispute
- `POST /api/disputes/{id}/approve` - Approve a dispute
- `POST /api/disputes/{id}/reject` - Reject a dispute

**Analytics:**
- `GET /api/analytics` - Executive dashboard metrics (auto-resolution rate, fraud prevention, etc.)

**Key Endpoint Details:**

**POST /api/disputes/process** - Main AI Processing Endpoint
```json
Request:
{
  "transaction_id": 5,
  "customer_id": 1,
  "customer_query": "ATM did not dispense cash but my account was debited"
}

Response (SSE Stream):
- Real-time updates as agents process the dispute
- Final response includes ticket_id, decision, confidence scores, audit trail
```

**GET /api/analytics** - Dashboard Metrics
```json
Response:
{
  "total_tickets": 150,
  "auto_resolved_count": 120,
  "human_review_count": 30,
  "auto_resolution_rate": 80.0,
  "total_fraud_prevented": 45000.00,
  "fraud_tickets_prevented": 15
}
```

For complete API documentation, visit: http://localhost:8000/docs (when backend is running)

### Technology Stack

**Backend:**
- FastAPI - Web framework
- SQLAlchemy - ORM
- SQLite - Database
- LangChain - LLM framework
- LangGraph - Agent orchestration
- OpenAI - LLM provider
- Pydantic - Data validation

**Frontend:**
- Next.js 16 - React framework
- React 19 - UI library
- Tailwind CSS - Styling
- Shadcn/ui - Component library
- TypeScript - Type safety

---

## 🆘 Getting Help

If you encounter issues not covered in this guide:

1. **Check logs**: Look at terminal output for error messages
2. **Review documentation**: Check the docs mentioned above
3. **Verify prerequisites**: Ensure all required software is installed
4. **Check API status**: Visit `http://localhost:8000/health`
5. **Restart services**: Stop and restart both backend and frontend

---

## ✅ Installation Checklist

Use this checklist to track your installation progress:

- [ ] Python 3.9+ installed
- [ ] Node.js 18+ and npm installed
- [ ] OpenAI API key obtained
- [ ] Project downloaded/cloned
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] MCP server dependencies verified
- [ ] `.env` file created and configured
- [ ] Database seeded successfully (6 customers, 25+ transactions)
- [ ] MCP Banking Tools Server running on port 8001
- [ ] MCP Compliance Server running on port 8002
- [ ] MCP Core Banking Server running on port 8003
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 3000
- [ ] API documentation accessible
- [ ] Frontend homepage loads
- [ ] All MCP tools operational
- [ ] Test dispute processed successfully

---

## 🎉 Success!

If you've completed all steps, you now have a fully functional Banking Dispute Management System with AI agents running locally!

**Access Points:**
- 🌐 Frontend: `http://localhost:3000`
- 🔌 Backend API: `http://localhost:8000`
- 📚 API Docs: `http://localhost:8000/docs`

**Happy coding! 🚀**

---

*Last Updated: April 29, 2026*
*Version: 2.0.0 - MCP Enhanced*