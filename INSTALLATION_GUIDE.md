# 🚀 Dispute Management Agentic AI System - Installation Guide

Complete step-by-step guide to install and run the Banking Dispute Management System with multi-agent AI capabilities.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Project Overview](#project-overview)
4. [Installation Steps](#installation-steps)
   - [Backend Setup](#backend-setup)
   - [Frontend Setup](#frontend-setup)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Running the Application](#running-the-application)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## 🖥️ System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.9 or higher
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

This system consists of two main components:

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
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- sqlalchemy==2.0.25
- pydantic==2.5.3
- langgraph==0.0.26
- langchain==0.1.10
- langchain-openai==0.0.8
- openai==1.12.0
- python-dotenv==1.0.1
- And other dependencies

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
```

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

**Expected output:**
```
Clearing existing data...
Database cleared.

Creating customers...
✅ Created 5 customers

Creating transactions...
✅ Created 7 transactions

Creating ATM logs...
✅ Created 2 ATM logs

Creating dispute tickets...
✅ Created 5 dispute tickets

Creating audit logs...
✅ Created 5 audit logs

========================================
DATABASE SEEDING COMPLETED SUCCESSFULLY!
========================================

Summary:
- 5 Customers created
- 7 Transactions created
- 2 ATM Logs created
- 5 Dispute Tickets created
- 5 Audit Logs created
```

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

The seed script creates realistic test scenarios:

1. **5 Customers** with different account tiers (Basic, Premium, Gold)
2. **7 Transactions** including:
   - High-value international transactions
   - Failed transactions
   - Duplicate charges
   - ATM withdrawals
3. **5 Dispute Tickets** covering:
   - Fraud detection scenarios
   - ATM hardware faults
   - Duplicate charge disputes
   - Merchant disputes
4. **ATM Logs** with hardware fault records
5. **Audit Logs** simulating AI agent actions

For detailed information, see `DATABASE_SEED_SUMMARY.md`.

---

## 🚀 Running the Application

You'll need **TWO terminal windows** - one for backend, one for frontend.

### Terminal 1: Start Backend Server

#### Step 1: Navigate to Backend and Activate Environment
```bash
cd backend
# Activate venv if not already active
# Windows: .\venv\Scripts\Activate.ps1
# macOS/Linux: source venv/bin/activate
```

#### Step 2: Start FastAPI Server
```bash
python main.py
```

**Alternative method using uvicorn directly:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

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

### Terminal 2: Start Frontend Server

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
  "status": "healthy",
  "database": "connected"
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

### 4. Verify AI Agent Functionality

Test the banking tools:
```bash
cd backend
python test_banking_tools.py
```

Expected output showing all 7 tools tested successfully:
```
Testing Banking Tools...
✅ get_transaction_details - PASSED
✅ get_customer_history - PASSED
✅ check_atm_logs - PASSED
✅ check_duplicate_transactions - PASSED
✅ block_card - PASSED
✅ initiate_refund - PASSED
✅ route_to_human - PASSED

All tests passed! ✅
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Port Already in Use

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
- **Banking Tools Documentation**: See `BANKING_TOOLS_DOCUMENTATION.md`
- **Database Schema**: See `DATABASE_SEED_SUMMARY.md`
- **Agent Architecture**: See `frontend/AGENTS.md`

### 2. Test AI Agents

The system includes multiple AI agents:
- **Triage Agent**: Routes disputes to appropriate handlers
- **Investigator Agent**: Gathers evidence using banking tools
- **Decision Agent**: Makes resolution decisions
- **Orchestrator Agent**: Coordinates multi-agent workflow

Test dispute resolution:
```bash
cd backend
python simulate_disputes.py  # If available
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
- `README.md` - Project overview
- `BANKING_TOOLS_DOCUMENTATION.md` - Complete banking tools reference
- `DATABASE_SEED_SUMMARY.md` - Database schema and test data
- `frontend/AGENTS.md` - AI agent architecture
- `frontend/CLAUDE.md` - Development notes

### API Endpoints Reference

**Health & Info:**
- `GET /` - Root endpoint
- `GET /health` - Health check

**Statistics:**
- `GET /customers/count` - Total customers
- `GET /transactions/count` - Total transactions
- `GET /disputes/count` - Total disputes

**Customers:**
- `GET /customers` - List all customers
- `GET /customers/{id}` - Get customer details

**Transactions:**
- `GET /transactions` - List all transactions
- `GET /transactions/{id}` - Get transaction details

**Disputes:**
- `GET /disputes` - List all disputes
- `GET /disputes/{id}` - Get dispute details
- `POST /disputes` - Create new dispute
- `PUT /disputes/{id}` - Update dispute

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
- [ ] `.env` file created and configured
- [ ] Database seeded successfully
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 3000
- [ ] API documentation accessible
- [ ] Frontend homepage loads
- [ ] Banking tools tests pass

---

## 🎉 Success!

If you've completed all steps, you now have a fully functional Banking Dispute Management System with AI agents running locally!

**Access Points:**
- 🌐 Frontend: `http://localhost:3000`
- 🔌 Backend API: `http://localhost:8000`
- 📚 API Docs: `http://localhost:8000/docs`

**Happy coding! 🚀**

---

*Last Updated: April 2026*
*Version: 1.0.0*