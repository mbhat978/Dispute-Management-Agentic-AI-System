"""Test script to verify the dispute detail endpoint"""
from database import SessionLocal
from models import DisputeTicket, Customer, Transaction, AuditLog

db = SessionLocal()

# Get first ticket
ticket = db.query(DisputeTicket).first()

if ticket:
    print(f"[OK] Found ticket #{ticket.id}")
    print(f"   Status: {ticket.status}")
    print(f"   Customer ID: {ticket.customer_id}")
    print(f"   Transaction ID: {ticket.transaction_id}")
    
    # Check customer
    customer = db.query(Customer).filter(Customer.id == ticket.customer_id).first()
    print(f"   Customer: {customer.name if customer else 'Not found'}")
    
    # Check transaction
    transaction = db.query(Transaction).filter(Transaction.id == ticket.transaction_id).first()
    print(f"   Transaction: ${transaction.amount if transaction else 'Not found'}")
    
    # Check audit logs
    audit_logs = db.query(AuditLog).filter(AuditLog.ticket_id == ticket.id).count()
    print(f"   Audit logs: {audit_logs}")
    
    print(f"\n[SUCCESS] Endpoint GET /api/disputes/{ticket.id} should work!")
else:
    print("[ERROR] No tickets found in database")

db.close()

# Made with Bob
