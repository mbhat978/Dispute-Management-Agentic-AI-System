# Banking Dispute Management System

A multi-agent AI dispute resolution platform for banking workflows built with FastAPI, LangGraph, SQLite, Next.js, and MCP-based tool servers.

## 🎯 Team Members
- **Name**: Manisha Bhattacharjee
- **IBM Email ID**: Manisha.Bhattacharjee@ibm.com

## Overview

This project processes banking dispute tickets through an agentic workflow that:
- classifies the dispute
- gathers evidence through MCP tools
- makes an automated decision when confidence is sufficient
- pauses for human review when required
- resumes from checkpointed workflow state

The system includes:
- **FastAPI backend** for APIs, orchestration, and streaming
- **LangGraph multi-agent workflow** for triage, investigation, and decisioning
- **SQLite database** for customers, transactions, disputes, audit logs, and seeded demo data
- **Three MCP servers** for core banking tools, compliance lookup, and enhanced dispute tooling
- **Next.js frontend** for customer and employee workflows
- **SSE streams** for real-time processing and log updates

## High-Level Architecture

```text
Frontend (Next.js, port 3000)
        |
        v
Backend API (FastAPI, port 8000)
        |
        +--> LangGraph workflow
        |     - Triage Agent
        |     - Investigation Agent
        |     - Decision Agent
        |
        +--> SSE streams
        |     - /api/disputes/stream
        |     - /api/logs/stream
        |
        +--> MCP client
              - Core Banking MCP Server      (8001)
              - Compliance MCP Server        (8002)
              - Enhanced Banking MCP Server  (8003)

Shared SQLite DB: backend/dispute_management.db
Workflow checkpoints: backend/checkpoints.db
```

## Project Structure

```text
Dispute-Management-Agentic-AI-System/
├── INSTALLATION_GUIDE.md
├── PROJECT_DOCUMENTATION.md
├── README.md
├── .env.example
├── requirements.txt
├── run_app.bat
├── start_cluster.bat
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── seed_data.py
│   ├── requirements.txt
│   ├── mcp_client.py
│   ├── checkpoints.db
│   ├── dispute_management.db
│   ├── agents/
│   └── mcp_servers/
└── frontend/
    ├── package.json
    ├── app/
    └── components/
```

## Core Backend Models

### Customer
- `id`
- `name`
- `account_tier`
- `current_account_balance`
- `card_number`
- `card_status`
- `inactive_cards`

### Transaction
- `id`
- `customer_id`
- `amount`
- `merchant_name`
- `transaction_date`
- `status`
- `is_international`
- `refunded_amount`
- `transaction_type`

### ATM_Log
- `id`
- `transaction_id`
- `atm_id`
- `status_code`

### LoanAccount
- `id`
- `customer_id`
- `monthly_emi_amount`
- `total_outstanding`

### DisputeTicket
- `id`
- `transaction_id`
- `customer_id`
- `dispute_reason`
- `dispute_category`
- `status`
- `final_decision`
- `decision_reasoning`
- `resolution_notes`
- `created_at`
- `updated_at`

### AuditLog
- `id`
- `ticket_id`
- `agent_name`
- `action_type`
- `description`
- `timestamp`

## MCP Servers and Tools

The backend connects to MCP servers over SSE using these endpoints:
- `http://localhost:8001/sse`
- `http://localhost:8002/sse`
- `http://localhost:8003/sse`

### Core Banking MCP Server - Port 8001
Exposes core dispute and banking tools such as:
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

### Compliance MCP Server - Port 8002
- `query_compliance_policy`

### Enhanced Banking MCP Server - Port 8003
- `get_delivery_tracking_status`
- `check_merchant_reputation_score`
- `get_merchant_dispute_history`
- `check_subscription_status`
- `verify_subscription_cancellation`
- `get_refund_timeline`

## API Endpoints

### Health and Counts
- `GET /`
- `GET /health`
- `GET /customers/count`
- `GET /transactions/count`
- `GET /disputes/count`

### Customer APIs
- `GET /api/customers`
- `GET /api/customers/{customer_id}/transactions`
- `GET /api/customers/{customer_id}/disputes`

### Dispute APIs
- `GET /api/disputes`
- `GET /api/disputes/{ticket_id}`
- `POST /api/disputes/process`
- `POST /api/disputes/{ticket_id}/approve`
- `POST /api/disputes/{ticket_id}/reject`
- `POST /api/disputes/{ticket_id}/resolve`
- `POST /api/disputes/{ticket_id}/resume`

### Streaming APIs
- `GET /api/disputes/stream`
- `GET /api/logs/stream`

### Analytics
- `GET /api/analytics`

## Setup

## Prerequisites
- Python 3.11+ recommended
- Node.js and npm
- OpenAI API key
- Optional: LangSmith API key for tracing

## 1. Configure environment variables

Create `.env` in the project root from `.env.example`.

### Windows PowerShell
```powershell
Copy-Item .env.example .env
```

### macOS/Linux
```bash
cp .env.example .env
```

Update `.env` with at least:

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.0
```

Optional LangSmith values are also supported:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
LANGCHAIN_PROJECT="dispute-management-agents"
```

## 2. Backend setup

Use `backend/requirements.txt` as the source of truth for backend dependencies.

```bash
cd backend
python -m venv venv
```

### Activate virtual environment

#### Windows PowerShell
```powershell
.\venv\Scripts\Activate.ps1
```

#### Windows Command Prompt
```cmd
venv\Scripts\activate.bat
```

#### macOS/Linux
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Seed the database

From the `backend/` directory:

```bash
python seed_data.py
```

This creates:
- 6 customers
- 1 loan account
- common baseline transactions
- scenario-specific transactions for 10 dispute scenarios
- ATM logs
- 15 historical ShopXYZ disputes for merchant-risk testing

Primary database path:
- `backend/dispute_management.db`

## 4. Frontend setup

In a separate terminal:

```bash
cd frontend
npm install
```

## Running the Application

## Option A: Full cluster startup
Use this for end-to-end agent workflows with MCP servers.

```bash
start_cluster.bat
```

This starts:
1. Core Banking MCP Server on port 8001
2. Compliance MCP Server on port 8002
3. Enhanced Banking MCP Server on port 8003
4. FastAPI backend on port 8000
5. Next.js frontend on port 3000

Notes:
- `start_cluster.bat` expects a root-level virtual environment at `venv`
- it launches MCP servers before backend and frontend
- backend is started with `uvicorn main:app --host 0.0.0.0 --port 8000`

## Option B: Backend + frontend launcher
```bash
run_app.bat
```

Notes:
- creates `backend/venv` if needed
- installs backend/frontend dependencies if missing
- starts backend and frontend only
- does **not** start MCP servers

## Option C: Manual startup

### Terminal 1
```bash
cd backend
python mcp_servers/core_banking_server.py
```

### Terminal 2
```bash
cd backend
python mcp_servers/compliance_server.py
```

### Terminal 3
```bash
cd backend
python mcp_servers/enhanced_banking_tools.py
```

### Terminal 4
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 5
```bash
cd frontend
npm run dev
```

## Access URLs
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Verification

### Basic health checks
```bash
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/customers/count
curl http://localhost:8000/transactions/count
curl http://localhost:8000/disputes/count
```

Expected health response:
```json
{
  "status": "healthy"
}
```

### Useful API checks
```bash
curl http://localhost:8000/api/customers
curl http://localhost:8000/api/disputes
curl http://localhost:8000/api/analytics
```

### Test dispute processing
```bash
curl -X POST http://localhost:8000/api/disputes/process \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 15,
    "customer_id": 3,
    "customer_query": "ATM did not dispense cash but my account was debited"
  }'
```

### Test human-in-the-loop resume
```bash
curl -X POST http://localhost:8000/api/disputes/1/resume \
  -H "Content-Type: application/json" \
  -d '{
    "override_decision": "approved",
    "human_notes": "Confirmed by reviewer"
  }'
```

## Seeded Test Coverage

The seed script supports testing for:
1. Fraudulent international transaction
2. Merchant dispute - item not delivered
3. ATM dispute - cash not dispensed
4. Duplicate transaction
5. Incorrect amount - overcharged
6. Subscription dispute
7. Loan/EMI dispute
8. Refund not received
9. Quality/service dispute
10. Chargeback scenario

Reference material:
- `AGENT_TESTING_GUIDE.md`
- `INSTALLATION_GUIDE.md`
- `PROJECT_DOCUMENTATION.md`

## Technology Stack
- FastAPI
- SQLAlchemy
- SQLite
- LangGraph
- LangChain
- OpenAI
- MCP
- Loguru
- Next.js
- React
- TypeScript

## Notes
- The backend creates tables at startup using SQLAlchemy metadata.
- Workflow checkpoints are stored in SQLite for human-in-the-loop resume support.
- Tickets can move through states such as `under_investigation`, `pending_review`, `auto_approved`, and `auto_rejected`.
- Investigation evidence can be read back from checkpointed workflow state for in-progress tickets.

## Documentation
- `INSTALLATION_GUIDE.md` - installation and run instructions
- `PROJECT_DOCUMENTATION.md` - architecture and detailed technical documentation
- `AGENT_TESTING_GUIDE.md` - testing scenarios and flows