# Banking Dispute Management System

A multi-agent AI system for banking dispute management built with FastAPI, SQLAlchemy, and SQLite.

## Project Structure

```
Dispute-Management-Agentic-AI-System/
├── main.py              # FastAPI application entry point
├── database.py          # Database connection and session management
├── models.py            # SQLAlchemy ORM models
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Database Models

### Customer
- **id**: Primary key
- **name**: Customer name
- **account_tier**: Account tier (Basic, Premium, Gold, etc.)
- **average_monthly_balance**: Average monthly balance

### Transaction
- **id**: Primary key
- **customer_id**: Foreign key to Customer
- **amount**: Transaction amount
- **merchant_name**: Name of merchant
- **transaction_date**: Date and time of transaction
- **status**: Transaction status (success, failed, pending)
- **is_international**: Boolean indicating if transaction is international

### ATM_Log
- **id**: Primary key
- **transaction_id**: Foreign key to Transaction
- **atm_id**: ATM machine identifier
- **status_code**: Status code (e.g., '200_DISPENSED', '500_HARDWARE_FAULT')

### DisputeTicket
- **id**: Primary key
- **transaction_id**: Foreign key to Transaction
- **customer_id**: Foreign key to Customer
- **dispute_reason**: Reason for the dispute
- **status**: Dispute status (open, under_investigation, auto_approved, auto_rejected, human_review_required)
- **resolution_notes**: Notes about the resolution
- **created_at**: Timestamp when ticket was created
- **updated_at**: Timestamp when ticket was last updated

### AuditLog
- **id**: Primary key
- **ticket_id**: Foreign key to DisputeTicket
- **agent_name**: Name of the AI agent
- **action_type**: Type of action (thought, tool_call, observation, decision)
- **description**: Description of the action
- **timestamp**: Timestamp of the action

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

The API will be available at: `http://localhost:8000`

### 3. Access API Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

### Statistics
- `GET /customers/count` - Get total customer count
- `GET /transactions/count` - Get total transaction count
- `GET /disputes/count` - Get total dispute ticket count

## Database

The application uses SQLite for the prototype. The database file `dispute_management.db` will be automatically created in the project directory when you first run the application.

All database tables are created automatically on startup using SQLAlchemy's `create_all()` method.

## Next Steps

1. Add CRUD endpoints for each model (Create, Read, Update, Delete)
2. Implement Pydantic schemas for request/response validation
3. Add AI agent integration for dispute resolution
4. Implement authentication and authorization
5. Add business logic for automatic dispute resolution
6. Create agent orchestration system
7. Add logging and monitoring

## Development

To add new models or modify existing ones:
1. Update the models in `models.py`
2. The tables will be automatically created/updated on next startup
3. For production, consider using Alembic for database migrations

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **SQLite**: Lightweight database for prototyping
- **Uvicorn**: ASGI server for running FastAPI
- **Pydantic**: Data validation using Python type annotations