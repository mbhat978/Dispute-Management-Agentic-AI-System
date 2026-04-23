"""
Migration script to add final_decision and decision_reasoning columns to dispute_tickets table.
This fixes the issue where the Decision Agent couldn't save these fields to the database.
"""

import sqlite3
from pathlib import Path

def migrate_database():
    """Add missing columns to dispute_tickets table"""
    db_path = Path(__file__).parent / "dispute_management.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(dispute_tickets)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add final_decision column if it doesn't exist
        if 'final_decision' not in columns:
            print("Adding final_decision column...")
            cursor.execute("""
                ALTER TABLE dispute_tickets
                ADD COLUMN final_decision VARCHAR(100)
            """)
            print("[OK] final_decision column added")
        else:
            print("[OK] final_decision column already exists")
        
        # Add decision_reasoning column if it doesn't exist
        if 'decision_reasoning' not in columns:
            print("Adding decision_reasoning column...")
            cursor.execute("""
                ALTER TABLE dispute_tickets
                ADD COLUMN decision_reasoning TEXT
            """)
            print("[OK] decision_reasoning column added")
        else:
            print("[OK] decision_reasoning column already exists")
        
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

# Made with Bob
