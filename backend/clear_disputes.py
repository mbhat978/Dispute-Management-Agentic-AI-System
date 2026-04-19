"""
Utility script to clear testing data (disputes and audit logs)
without destroying the seeded banking data (customers, transactions, etc.)
Also clears LangGraph checkpoint data.
"""

import os
import sqlite3
from pathlib import Path
from database import SessionLocal
from models import DisputeTicket, AuditLog


def clear_checkpoints():
    """Clear LangGraph checkpoint data from checkpoints.db"""
    backend_dir = Path(__file__).parent
    checkpoint_db = backend_dir / "checkpoints.db"
    
    if not checkpoint_db.exists():
        print("checkpoints.db not found - no checkpoint data to clear.")
        return
    
    try:
        # Connect to the checkpoint database
        conn = sqlite3.connect(str(checkpoint_db))
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in checkpoints.db")
            conn.close()
            return
        
        # Delete data from all tables
        deleted_tables = []
        for table in tables:
            table_name = table[0]
            try:
                # Get count before deletion
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    cursor.execute(f"DELETE FROM {table_name}")
                    deleted_tables.append(f"{table_name} ({count} rows)")
                    print(f"Cleared {count} row(s) from table: {table_name}")
            except Exception as e:
                print(f"Warning: Could not clear table {table_name}: {e}")
        
        # Commit changes
        conn.commit()
        
        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        
        conn.close()
        
        if deleted_tables:
            print(f"Successfully cleared checkpoint data from {len(deleted_tables)} table(s).")
        else:
            print("No checkpoint data found to clear.")
            
    except Exception as e:
        print(f"Error clearing checkpoint database: {e}")
        raise


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
    print("=" * 50)
    print("Clearing Dispute Management System Data")
    print("=" * 50)
    print()
    
    # Clear disputes and audit logs
    print("Step 1: Clearing disputes and audit logs...")
    clear_disputes()
    print()
    
    # Clear checkpoint data
    print("Step 2: Clearing LangGraph checkpoint data...")
    clear_checkpoints()
    print()
    
    print("=" * 50)
    print("All data cleared successfully!")
    print("=" * 50)

# Made with Bob
