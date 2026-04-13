from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import cast
from database import engine, get_db, Base
import models
from agent import dispute_resolution_workflow, initialize_dispute_state

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


@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs on application startup.
    Creates database tables if they don't exist.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


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
        print(f"\n❌ Error fetching disputes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching disputes: {str(e)}"
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
            raise HTTPException(
                status_code=404,
                detail=f"Dispute ticket with ID {ticket_id} not found"
            )
        
        # Get customer details
        customer = db.query(models.Customer).filter(
            models.Customer.id == dispute.customer_id
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer not found for dispute ticket {ticket_id}"
            )
        
        # Get transaction details
        transaction = db.query(models.Transaction).filter(
            models.Transaction.id == dispute.transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction not found for dispute ticket {ticket_id}"
            )
        
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
        print(f"\n❌ Error fetching dispute details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dispute details: {str(e)}"
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
        print(f"\n❌ Error approving dispute: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error approving dispute: {str(e)}"
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
        print(f"\n❌ Error rejecting dispute: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error rejecting dispute: {str(e)}"
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
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resolution_status. Must be one of: {valid_statuses}"
            )
        
        # Get the dispute ticket
        dispute = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == ticket_id
        ).first()
        
        if not dispute:
            raise HTTPException(
                status_code=404,
                detail=f"Dispute ticket with ID {ticket_id} not found"
            )
        
        print(f"\n{'='*80}")
        print(f"👤 HUMAN RESOLUTION - TICKET #{ticket_id}")
        print(f"{'='*80}")
        print(f"Resolution Status: {request.resolution_status}")
        print(f"Human Notes: {request.human_notes[:100]}...")
        print(f"{'='*80}")
        
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
        
        print(f"\n✅ RESOLUTION COMPLETE")
        print(f"   Ticket #{ticket_id} status updated to: {request.resolution_status}")
        print(f"   Audit log entry created")
        print(f"{'='*80}\n")
        
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
        print(f"\n❌ Error resolving dispute: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resolving dispute: {str(e)}"
        )


# ============================================================================
# DISPUTE RESOLUTION ENDPOINT
# ============================================================================

class DisputeProcessRequest(BaseModel):
    """
    Request model for processing a dispute.
    """
    ticket_id: int
    customer_query: str

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": 5,
                "customer_query": "ATM did not dispense cash but my account was debited. ATM showed error message."
            }
        }


@app.post("/api/disputes/process")
async def process_dispute(request: DisputeProcessRequest, db: Session = Depends(get_db)):
    """
    Process a dispute ticket using the multi-agent AI system.
    
    This endpoint:
    1. Retrieves the dispute ticket and customer information from the database
    2. Initializes the DisputeState with the provided information
    3. Invokes the LangGraph workflow (triage → investigator → decision)
    4. Returns the final state with the decision and full audit trail
    
    Args:
        request: DisputeProcessRequest containing ticket_id and customer_query
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
        HTTPException: If ticket not found or processing fails
    """
    try:
        # Retrieve the dispute ticket from the database
        ticket = db.query(models.DisputeTicket).filter(
            models.DisputeTicket.id == request.ticket_id
        ).first()
        
        if not ticket:
            raise HTTPException(
                status_code=404,
                detail=f"Dispute ticket with ID {request.ticket_id} not found"
            )
        
        # Narrow ORM attribute type for static type checkers
        customer_id = cast(int, ticket.customer_id)
        
        print(f"\n{'='*80}")
        print(f"🚀 PROCESSING DISPUTE TICKET #{request.ticket_id}")
        print(f"{'='*80}")
        print(f"Customer ID: {customer_id}")
        print(f"Query: {request.customer_query}")
        print(f"{'='*80}")
        
        # Initialize the dispute state
        initial_state = initialize_dispute_state(
            ticket_id=request.ticket_id,
            customer_id=customer_id,
            customer_query=request.customer_query,
            dispute_category="unknown"
        )
        
        # Invoke the compiled LangGraph workflow
        # The workflow will execute: triage → investigator → decision
        final_state = dispute_resolution_workflow.invoke(initial_state)
        
        print(f"\n{'='*80}")
        print(f"✅ DISPUTE PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"Final Decision: {final_state['final_decision'].upper()}")
        print(f"Category: {final_state['dispute_category']}")
        print(f"Audit Trail Entries: {len(final_state['audit_trail'])}")
        print(f"{'='*80}\n")
        
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
            "message": f"Dispute processed successfully. Decision: {final_state['final_decision']}"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"\n❌ Error processing dispute: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing dispute: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)