"""
Utility script to clear testing data (disputes and audit logs) 
without destroying the seeded banking data (customers, transactions, etc.)
"""

from database import SessionLocal
from models import DisputeTicket, AuditLog


def clear_disputes():
    """Clear all dispute tickets and audit logs from the database"""
    db = SessionLocal()
    try:
        # Delete AuditLog first to prevent foreign key constraint issues
        audit_count = db.query(AuditLog).delete()
        
        # Delete DisputeTicket records
        dispute_count = db.query(DisputeTicket).delete()
        
        # Commit the changes
        db.commit()
        
        print(f"Cleared {audit_count} audit log(s) and {dispute_count} dispute ticket(s).")
        print("Disputes and Audit logs cleared successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error clearing disputes: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_disputes()

# Made with Bob
