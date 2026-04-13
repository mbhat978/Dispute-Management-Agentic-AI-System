from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
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
                "created_at": dispute.created_at.isoformat() if dispute.created_at else None
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
        
        # Get customer_id from the ticket
        customer_id = ticket.customer_id
        
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