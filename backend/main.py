from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import cast, Any, Optional
from dotenv import load_dotenv
import os
import logging
import traceback

# Load environment variables from .env file
load_dotenv()

from database import engine, get_db, Base
import models
from agents.state import DisputeState, initialize_dispute_state
from agents.orchestrator import dispute_resolution_workflow

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("dispute_management")

# Create all tables in the database
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Banking Dispute Management System",
    description="Multi-agent AI system for banking dispute management",
    version="1.0.0"
)

# Configure CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


def build_error_response(
    message: str,
    *,
    code: str,
    details: Optional[Any] = None,
    ticket_id: Optional[int] = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    if details is not None:
        response["error"]["details"] = details
    if ticket_id is not None:
        response["ticket_id"] = ticket_id
    return response


def raise_api_error(
    status_code: int,
    message: str,
    *,
    code: str,
    details: Optional[Any] = None,
    ticket_id: Optional[int] = None,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail=build_error_response(
            message,
            code=code,
            details=details,
            ticket_id=ticket_id,
        ),
    )


@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs on application startup.
    Creates database tables if they don't exist.
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    return {
        "message": "Banking Dispute Management System API",
        "status": "active",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and detail.get("status") == "error":
        logger.warning(
            "HTTPException | path=%s | status=%s | code=%s | message=%s",
            request.url.path,
            exc.status_code,
            detail.get("error", {}).get("code"),
            detail.get("error", {}).get("message"),
        )
        return JSONResponse(status_code=exc.status_code, content=detail)

    message = detail if isinstance(detail, str) else "Request failed"
    error_payload = build_error_response(
        message,
        code="HTTP_ERROR",
        details={"path": request.url.path},
    )
    logger.warning(
        "HTTPException | path=%s | status=%s | message=%s",
        request.url.path,
        exc.status_code,
        message,
    )
    return JSONResponse(status_code=exc.status_code, content=error_payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception | path=%s | error=%s\n%s",
        request.url.path,
        str(exc),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content=build_error_response(
            "An unexpected server error occurred. Please try again or contact support.",
            code="INTERNAL_SERVER_ERROR",
            details={"path": request.url.path},
        ),
    )


# Example endpoint to test database connection
@app.get("/customers/count")
async def get_customer_count(db: Session = Depends(get_db)):
    """
    Get the total count of customers in the database.
    """
    count = db.query(models.Customer).count()
    return {"customer_count": count}


@app.get("/transactions/count")
async def get_transaction_count(db: Session = Depends(get_db)):
    """
    Get the total count of transactions in the database.
    """
    count = db.query(models.Transaction).count()
    return {"transaction_count": count}


@app.get("/disputes/count")
async def get_dispute_count(db: Session = Depends(get_db)):
    """
    Get the total count of dispute tickets in the database.
    """
    count = db.query(models.DisputeTicket).count()
    return {"dispute_count": count}


@app.get("/api/customers")
async def get_customers(db: Session = Depends(get_db)):
    """
    Return all mock customers for the customer dispute intake form.
    """
    try:
        customers = db.query(models.Customer).order_by(models.Customer.name.asc()).all()

        return {
            "status": "success",
            "count": len(customers),
            "customers": [
                {
                    "id": customer.id,
                    "name": customer.name,
                    "account_tier": customer.account_tier,
                    "average_monthly_balance": customer.average_monthly_balance,
                }
                for customer in customers
            ],
        }
    except Exception as e:
        logger.error("Error fetching customers: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to load customers.",
            code="CUSTOMERS_FETCH_FAILED",
            details={"reason": str(e)},
        )


@app.get("/api/customers/{customer_id}/transactions")
async def get_customer_transactions(customer_id: int, db: Session = Depends(get_db)):
    """
    Return recent transactions for a specific customer.
    """
    try:
        customer = db.query(models.Customer).filter(
            models.Customer.id == customer_id
        ).first()

        if not customer:
            raise_api_error(
                404,
                f"Customer with ID {customer_id} not found.",
                code="CUSTOMER_NOT_FOUND",
                details={"customer_id": customer_id},
            )
        customer = cast(models.Customer, customer)

        transactions = db.query(models.Transaction).filter(
            models.Transaction.customer_id == customer_id
        ).order_by(models.Transaction.transaction_date.desc()).limit(10).all()

        return {
            "status": "success",
            "customer": {
                "id": customer.id,
                "name": customer.name,
            },
            "count": len(transactions),
            "transactions": [
                {
                    "id": transaction.id,
                    "customer_id": transaction.customer_id,
                    "amount": transaction.amount,
                    "merchant_name": transaction.merchant_name,
                    "transaction_date": transaction.transaction_date.isoformat(),
                    "status": transaction.status,
                    "is_international": transaction.is_international,
                }
                for transaction in transactions
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching customer transactions: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to load customer transactions.",
            code="CUSTOMER_TRANSACTIONS_FETCH_FAILED",
            details={"customer_id": customer_id, "reason": str(e)},
        )


@app.get("/api/disputes")
async def get_all_disputes(db: Session = Depends(get_db)):
    """
    Get all dispute tickets with customer information.
    Returns a list of disputes with customer names for the dashboard.
    """
    try:
        # Query all dispute tickets with joined customer and transaction data
        disputes = db.query(models.DisputeTicket).join(
            models.Customer,
            models.DisputeTicket.customer_id == models.Customer.id
        ).join(
            models.Transaction,
            models.DisputeTicket.transaction_id == models.Transaction.id
        ).all()
        
        # Format the response
        result = []
        for dispute in disputes:
            result.append({
                "id": dispute.id,
                "customer_name": dispute.customer.name,
                "customer_id": dispute.customer.id,
                "dispute_reason": dispute.dispute_reason,
                "status": dispute.status,
                "amount": dispute.transaction.amount,
                "created_at": dispute.created_at.isoformat()
            })
        
        return {
            "status": "success",
            "count": len(result),
            "disputes": result
        }
        
    except Exception as e:
        logger.error("Error fetching disputes: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to load disputes.",
            code="DISPUTES_FETCH_FAILED",
            details={"reason": str(e)},
        )


@app.get("/api/disputes/{ticket_id}")
async def get_dispute_by_id(ticket_id: int, db: Session = Depends(get_db)):
    """
    Get a single dispute ticket with full details including:
    - Dispute ticket information
    - Customer details
    - Transaction details
    - Complete audit log ordered by timestamp
    
    This endpoint is crucial for AI governance and explainability,
    providing a complete view of the AI decision-making process.
    
    Args:
        ticket_id: The dispute ticket ID
        db: Database session
        
    Returns:
        Dict containing:
        - dispute: DisputeTicket details
        - customer: Customer information
        - transaction: Transaction details
        - audit_logs: Complete audit trail ordered by timestamp
        
    Raises:
        HTTPException: If ticket not found
    """
    try:
        # Query the dispute ticket with all relationships
        dispute = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not dispute:
            raise_api_error(
                404,
                f"Dispute ticket with ID {ticket_id} not found.",
                code="DISPUTE_NOT_FOUND",
                details={"ticket_id": ticket_id},
                ticket_id=ticket_id,
            )
        dispute = cast(models.DisputeTicket, dispute)
        
        # Get customer details
        customer = db.query(models.Customer).filter(
            models.Customer.id == dispute.customer_id
        ).first()
        
        if not customer:
            raise_api_error(
                404,
                f"Customer not found for dispute ticket {ticket_id}.",
                code="DISPUTE_CUSTOMER_NOT_FOUND",
                details={"ticket_id": ticket_id},
                ticket_id=ticket_id,
            )
        customer = cast(models.Customer, customer)
        
        # Get transaction details
        transaction = db.query(models.Transaction).filter(
            models.Transaction.id == dispute.transaction_id
        ).first()
        
        if not transaction:
            raise_api_error(
                404,
                f"Transaction not found for dispute ticket {ticket_id}.",
                code="DISPUTE_TRANSACTION_NOT_FOUND",
                details={"ticket_id": ticket_id},
                ticket_id=ticket_id,
            )
        transaction = cast(models.Transaction, transaction)
        
        # Get audit logs ordered by timestamp
        audit_logs = db.query(models.AuditLog).filter(
            models.AuditLog.ticket_id == ticket_id
        ).order_by(models.AuditLog.timestamp.asc()).all()
        
        # Format the response
        return {
            "dispute": {
                "id": dispute.id,
                "dispute_reason": dispute.dispute_reason,
                "status": dispute.status,
                "resolution_notes": dispute.resolution_notes,
                "created_at": dispute.created_at.isoformat(),
                "updated_at": dispute.updated_at.isoformat()
            },
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "account_tier": customer.account_tier,
                "average_monthly_balance": customer.average_monthly_balance
            },
            "transaction": {
                "id": transaction.id,
                "amount": transaction.amount,
                "merchant_name": transaction.merchant_name,
                "transaction_date": transaction.transaction_date.isoformat(),
                "status": transaction.status,
                "is_international": transaction.is_international
            },
            "audit_logs": [
                {
                    "id": log.id,
                    "agent_name": log.agent_name,
                    "action_type": log.action_type,
                    "description": log.description,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in audit_logs
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching dispute details: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to load dispute details.",
            code="DISPUTE_DETAILS_FETCH_FAILED",
            details={"ticket_id": ticket_id, "reason": str(e)},
            ticket_id=ticket_id,
        )


@app.post("/api/disputes/{ticket_id}/approve")
async def approve_dispute(ticket_id: int, db: Session = Depends(get_db)):
    """
    Approve a dispute ticket that requires human review.
    Updates the ticket status to 'auto_approved' and adds resolution notes.
    
    Args:
        ticket_id: The dispute ticket ID
        db: Database session
        
    Returns:
        Dict with success message and updated ticket info
        
    Raises:
        HTTPException: If ticket not found or not in human_review_required status
    """
    try:
        # Get the dispute ticket
        dispute = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not dispute:
            raise HTTPException(
                status_code=404,
                detail=f"Dispute ticket with ID {ticket_id} not found"
            )
        
        # Update the ticket status using setattr to avoid type checking issues
        setattr(dispute, 'status', 'auto_approved')
        setattr(dispute, 'resolution_notes', 'Approved by human agent after AI review')
        setattr(dispute, 'updated_at', datetime.utcnow())
        
        # Add audit log entry
        audit_entry = models.AuditLog(
            ticket_id=ticket_id,
            agent_name="Human Agent",
            action_type="decision",
            description="Human agent approved the dispute after reviewing AI analysis and audit trail.",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        
        db.commit()
        db.refresh(dispute)
        
        return {
            "status": "success",
            "message": f"Dispute ticket #{ticket_id} has been approved",
            "ticket_id": ticket_id,
            "new_status": dispute.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error approving dispute: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to approve dispute.",
            code="DISPUTE_APPROVE_FAILED",
            details={"ticket_id": ticket_id, "reason": str(e)},
            ticket_id=ticket_id,
        )


@app.post("/api/disputes/{ticket_id}/reject")
async def reject_dispute(ticket_id: int, db: Session = Depends(get_db)):
    """
    Reject a dispute ticket that requires human review.
    Updates the ticket status to 'auto_rejected' and adds resolution notes.
    
    Args:
        ticket_id: The dispute ticket ID
        db: Database session
        
    Returns:
        Dict with success message and updated ticket info
        
    Raises:
        HTTPException: If ticket not found or not in human_review_required status
    """
    try:
        # Get the dispute ticket
        dispute = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not dispute:
            raise HTTPException(
                status_code=404,
                detail=f"Dispute ticket with ID {ticket_id} not found"
            )
        
        # Update the ticket status using setattr to avoid type checking issues
        setattr(dispute, 'status', 'auto_rejected')
        setattr(dispute, 'resolution_notes', 'Rejected by human agent after AI review')
        setattr(dispute, 'updated_at', datetime.utcnow())
        
        # Add audit log entry
        audit_entry = models.AuditLog(
            ticket_id=ticket_id,
            agent_name="Human Agent",
            action_type="decision",
            description="Human agent rejected the dispute after reviewing AI analysis and audit trail.",
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        
        db.commit()
        db.refresh(dispute)
        
        return {
            "status": "success",
            "message": f"Dispute ticket #{ticket_id} has been rejected",
            "ticket_id": ticket_id,
            "new_status": dispute.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error rejecting dispute: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to reject dispute.",
            code="DISPUTE_REJECT_FAILED",
            details={"ticket_id": ticket_id, "reason": str(e)},
            ticket_id=ticket_id,
        )


# ============================================================================
# HUMAN RESOLUTION ENDPOINT
# ============================================================================

class DisputeResolveRequest(BaseModel):
    """
    Request model for human resolution of a dispute.
    """
    resolution_status: str  # 'resolved_approved' or 'resolved_rejected'
    human_notes: str

    class Config:
        json_schema_extra = {
            "example": {
                "resolution_status": "resolved_approved",
                "human_notes": "After reviewing the complete audit trail and evidence, I approve this dispute. The ATM logs confirm hardware fault."
            }
        }


@app.post("/api/disputes/{ticket_id}/resolve")
async def resolve_dispute(
    ticket_id: int,
    request: DisputeResolveRequest,
    db: Session = Depends(get_db)
):
    """
    Human resolution endpoint for dispute tickets.
    
    This endpoint allows human agents to make final decisions on disputes,
    particularly those requiring human review. It updates the ticket status
    and adds a comprehensive audit log entry documenting the human decision.
    
    Args:
        ticket_id: The dispute ticket ID
        request: DisputeResolveRequest with resolution_status and human_notes
        db: Database session
        
    Returns:
        Dict with success message and updated ticket info
        
    Raises:
        HTTPException: If ticket not found or resolution fails
    """
    try:
        # Validate resolution status
        valid_statuses = ['resolved_approved', 'resolved_rejected']
        if request.resolution_status not in valid_statuses:
            raise_api_error(
                400,
                f"Invalid resolution_status. Must be one of: {valid_statuses}",
                code="INVALID_RESOLUTION_STATUS",
                details={"allowed_values": valid_statuses},
                ticket_id=ticket_id,
            )
        
        # Get the dispute ticket
        dispute = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not dispute:
            raise_api_error(
                404,
                f"Dispute ticket with ID {ticket_id} not found.",
                code="DISPUTE_NOT_FOUND",
                details={"ticket_id": ticket_id},
                ticket_id=ticket_id,
            )
        dispute = cast(models.DisputeTicket, dispute)
        
        logger.info("=" * 80)
        logger.info("[HUMAN RESOLUTION] - TICKET #%s", ticket_id)
        logger.info("=" * 80)
        logger.info("Resolution Status: %s", request.resolution_status)
        logger.info("Human Notes: %s...", request.human_notes[:100])
        logger.info("=" * 80)
        
        # Update the ticket status
        old_status = dispute.status
        setattr(dispute, 'status', request.resolution_status)
        setattr(dispute, 'resolution_notes', request.human_notes)
        setattr(dispute, 'updated_at', datetime.utcnow())
        
        # Create comprehensive audit log entry
        action_description = f"""Human Agent Final Resolution:

Previous Status: {old_status}
New Status: {request.resolution_status}

Human Agent Notes:
{request.human_notes}

Resolution Timestamp: {datetime.utcnow().isoformat()}

This represents the final human decision after reviewing the complete AI audit trail,
gathered evidence, and all relevant transaction data. The human agent has exercised
their judgment to override or confirm the AI recommendation."""
        
        audit_entry = models.AuditLog(
            ticket_id=ticket_id,
            agent_name="Human Agent",
            action_type="decision",
            description=action_description,
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        
        # Commit changes
        db.commit()
        db.refresh(dispute)
        
        logger.info("[SUCCESS] RESOLUTION COMPLETE")
        logger.info("Ticket #%s status updated to: %s", ticket_id, request.resolution_status)
        logger.info("Audit log entry created")
        logger.info("%s", "=" * 80)
        
        return {
            "status": "success",
            "message": f"Dispute ticket #{ticket_id} has been {request.resolution_status.replace('resolved_', '')}",
            "ticket_id": ticket_id,
            "previous_status": old_status,
            "new_status": dispute.status,
            "resolution_notes": dispute.resolution_notes,
            "updated_at": dispute.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error resolving dispute: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to resolve dispute.",
            code="DISPUTE_RESOLVE_FAILED",
            details={"ticket_id": ticket_id, "reason": str(e)},
            ticket_id=ticket_id,
        )


# ============================================================================
# DISPUTE RESOLUTION ENDPOINT
# ============================================================================

class DisputeProcessRequest(BaseModel):
    """
    Request model for processing a dispute.
    """
    transaction_id: int
    customer_id: int
    customer_query: str

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": 5,
                "customer_id": 1,
                "customer_query": "ATM did not dispense cash but my account was debited. ATM showed error message."
            }
        }


@app.post("/api/disputes/process")
async def process_dispute(request: DisputeProcessRequest, db: Session = Depends(get_db)):
    """
    Process a dispute ticket using the multi-agent AI system.
    
    This endpoint:
    1. Creates a new dispute ticket in the database
    2. Initializes the DisputeState with the provided information
    3. Invokes the LangGraph workflow with dynamic ReAct routing
    4. Returns the final state with the decision and full audit trail
    
    Args:
        request: DisputeProcessRequest containing transaction_id, customer_id, and customer_query
        db: Database session
        
    Returns:
        Dict containing the complete DisputeState including:
        - ticket_id: The dispute ticket ID
        - customer_id: The customer ID
        - customer_query: The original query
        - dispute_category: Categorized dispute type
        - gathered_data: All evidence collected by agents
        - audit_trail: Complete reasoning trail (thoughts, actions, observations)
        - final_decision: auto_approved, auto_rejected, or human_review_required
        
    Raises:
        HTTPException: If processing fails
    """
    new_ticket: Optional[models.DisputeTicket] = None

    try:
        # Create a new dispute ticket
        new_ticket = models.DisputeTicket(
            transaction_id=request.transaction_id,
            customer_id=request.customer_id,
            dispute_reason=request.customer_query,
            status='under_investigation'
        )
        
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        
        logger.info("%s", "=" * 80)
        logger.info("[PROCESSING] DISPUTE TICKET #%s", new_ticket.id)
        logger.info("%s", "=" * 80)
        logger.info("Customer ID: %s", request.customer_id)
        logger.info("Transaction ID: %s", request.transaction_id)
        logger.info("Query: %s", request.customer_query)
        logger.info("%s", "=" * 80)
        
        # Initialize the dispute state
        initial_state = initialize_dispute_state(
            ticket_id=cast(int, new_ticket.id),
            customer_id=request.customer_id,
            customer_query=request.customer_query,
            dispute_category="unknown"
        )
        
        # Execute the LangGraph workflow so agents can route dynamically
        final_state: DisputeState = cast(
            DisputeState,
            dispute_resolution_workflow.invoke(initial_state)
        )
        
        logger.info("%s", "=" * 80)
        logger.info("[SUCCESS] DISPUTE PROCESSING COMPLETE")
        logger.info("%s", "=" * 80)
        logger.info("Final Decision: %s", final_state["final_decision"].upper())
        logger.info("Category: %s", final_state["dispute_category"])
        logger.info("Audit Trail Entries: %s", len(final_state["audit_trail"]))
        logger.info("%s", "=" * 80)
        
        # Return the final state
        return {
            "status": "success",
            "ticket_id": final_state["ticket_id"],
            "customer_id": final_state["customer_id"],
            "customer_query": final_state["customer_query"],
            "dispute_category": final_state["dispute_category"],
            "final_decision": final_state["final_decision"],
            "gathered_data": final_state["gathered_data"],
            "audit_trail": final_state["audit_trail"],
            "triage_confidence": final_state.get("triage_confidence", 0.0),
            "investigation_confidence": final_state.get("investigation_confidence", 0.0),
            "decision_confidence": final_state.get("decision_confidence", 0.0),
            "investigation_summary": final_state.get("investigation_summary", ""),
            "decision_reasoning": final_state.get("decision_reasoning", {}),
            "working_memory": final_state.get("working_memory", {}),
            "message": f"Dispute processed successfully. Decision: {final_state['final_decision']}"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Error processing dispute: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to process dispute.",
            code="DISPUTE_PROCESS_FAILED",
            details={
                "customer_id": request.customer_id,
                "transaction_id": request.transaction_id,
                "reason": str(e),
            },
            ticket_id=getattr(new_ticket, "id", None),
        )


# ============================================================================
# ANALYTICS ENDPOINT - Phase 8: Executive Analytics Dashboard
# ============================================================================

@app.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """
    Executive Analytics Dashboard endpoint.
    
    Calculates and returns key business metrics to prove the value of the agentic system:
    - Total dispute tickets processed
    - Auto-resolved tickets (auto_approved + auto_rejected)
    - Human review tickets (human_review_required + resolved_approved + resolved_rejected)
    - Auto-resolution rate (percentage)
    - Total fraud prevented (sum of amounts for fraud-related auto-approved tickets)
    
    Returns:
        Dict containing all analytics metrics in a clean JSON structure
        
    Raises:
        HTTPException: If analytics calculation fails
    """
    try:
        logger.info("%s", "=" * 80)
        logger.info("[ANALYTICS] Calculating Executive Dashboard Metrics")
        logger.info("%s", "=" * 80)
        
        # 1. Total tickets
        total_tickets = db.query(models.DisputeTicket).count()
        logger.info("Total Tickets: %s", total_tickets)
        
        # 2. Auto-resolved count (auto_approved + auto_rejected)
        auto_resolved_count = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.status.in_(['auto_approved', 'auto_rejected'])
        ).count()
        logger.info("Auto-Resolved Count: %s", auto_resolved_count)
        
        # 3. Human review count (human_review_required + resolved_approved + resolved_rejected)
        human_review_count = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.status.in_([
                'human_review_required',
                'resolved_approved',
                'resolved_rejected'
            ])
        ).count()
        logger.info("Human Review Count: %s", human_review_count)
        
        # 4. Auto-resolution rate
        auto_resolution_rate = 0.0
        if total_tickets > 0:
            auto_resolution_rate = round((auto_resolved_count / total_tickets) * 100, 2)
        logger.info("Auto-Resolution Rate: %s%%", auto_resolution_rate)
        
        # 5. Total fraud prevented
        # Get all auto-approved tickets where dispute_reason contains fraud-related keywords
        fraud_keywords = ['fraud', 'fraudulent', 'unauthorized', 'stolen', 'scam', 'phishing']
        
        # Query for fraud-related auto-approved tickets with their transaction amounts
        fraud_tickets = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.status == 'auto_approved'
        ).all()
        
        total_fraud_prevented: float = 0.0
        fraud_ticket_count = 0
        
        for ticket in fraud_tickets:
            # Check if dispute reason contains fraud-related keywords
            dispute_reason_lower = ticket.dispute_reason.lower()
            is_fraud_related = any(keyword in dispute_reason_lower for keyword in fraud_keywords)
            
            if is_fraud_related:
                # Get the transaction amount
                transaction = db.query(models.Transaction).filter(
                    models.Transaction.id == ticket.transaction_id
                ).first()
                
                if transaction is not None:
                    # Access the actual value from the SQLAlchemy model instance
                    amount_value = cast(float, transaction.amount)
                    total_fraud_prevented += amount_value
                    fraud_ticket_count += 1
        
        total_fraud_prevented = round(total_fraud_prevented, 2)
        logger.info("Total Fraud Prevented: $%s (%s tickets)", total_fraud_prevented, fraud_ticket_count)
        logger.info("%s", "=" * 80)
        
        # Return analytics in clean JSON structure
        return {
            "status": "success",
            "analytics": {
                "total_tickets": total_tickets,
                "auto_resolved_count": auto_resolved_count,
                "human_review_count": human_review_count,
                "auto_resolution_rate": auto_resolution_rate,
                "total_fraud_prevented": total_fraud_prevented,
                "fraud_tickets_prevented": fraud_ticket_count
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "description": "Executive Analytics Dashboard - Proving Business Value of Agentic AI System"
            }
        }
        
    except Exception as e:
        logger.error("Error calculating analytics: %s", str(e), exc_info=True)
        raise_api_error(
            500,
            "Unable to calculate analytics.",
            code="ANALYTICS_CALCULATION_FAILED",
            details={"reason": str(e)},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)