#!/usr/bin/env python3
# Script to add the GET /api/disputes/{ticket_id} endpoint

# Read the file
with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# The endpoint code to insert (after line 129, which is after the get_all_disputes function)
new_endpoint = '''
@app.get("/api/disputes/{ticket_id}")
async def get_dispute_by_id(ticket_id: int, db: Session = Depends(get_db)):
    """
    Get a specific dispute ticket with full details including:
    - Dispute ticket information
    - Associated customer details
    - Associated transaction details
    - Full audit log ordered by timestamp
    
    This endpoint is crucial for AI governance requirements, providing
    complete explainability and traceability for each dispute resolution.
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
        
        # Get the customer details
        customer = dispute.customer
        
        # Get the transaction details
        transaction = dispute.transaction
        
        # Get all audit logs ordered by timestamp
        audit_logs = db.query(models.AuditLog).filter(
            models.AuditLog.ticket_id == ticket_id
        ).order_by(models.AuditLog.timestamp.asc()).all()
        
        # Format the response
        return {
            "status": "success",
            "dispute": {
                "id": dispute.id,
                "dispute_reason": dispute.dispute_reason,
                "status": dispute.status,
                "resolution_notes": dispute.resolution_notes,
                "created_at": dispute.created_at.isoformat() if dispute.created_at else None,
                "updated_at": dispute.updated_at.isoformat() if dispute.updated_at else None
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
                "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                "status": transaction.status,
                "is_international": transaction.is_international
            },
            "audit_logs": [
                {
                    "id": log.id,
                    "agent_name": log.agent_name,
                    "action_type": log.action_type,
                    "description": log.description,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None
                }
                for log in audit_logs
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\\n❌ Error fetching dispute details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dispute details: {str(e)}"
        )


'''

# Insert the new endpoint after line 129 (index 129)
lines.insert(129, new_endpoint)

# Write back to the file
with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Endpoint successfully added to main.py at line 130")
print("✅ The GET /api/disputes/{ticket_id} endpoint is now available")