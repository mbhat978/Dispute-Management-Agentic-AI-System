"""
Database migration script to add dispute_category column to dispute_tickets table.
Run this script to update your existing database schema.
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str = "dispute_management.db"):
    """Add dispute_category column to dispute_tickets table if it doesn't exist."""
    
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(dispute_tickets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'dispute_category' in columns:
            print("[OK] Column 'dispute_category' already exists in dispute_tickets table.")
            return True
        
        # Add the new column
        print("Adding 'dispute_category' column to dispute_tickets table...")
        cursor.execute("""
            ALTER TABLE dispute_tickets
            ADD COLUMN dispute_category VARCHAR(100)
        """)
        
        conn.commit()
        print("[OK] Successfully added 'dispute_category' column to dispute_tickets table.")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(dispute_tickets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'dispute_category' in columns:
            print("[OK] Migration verified successfully.")
            return True
        else:
            print("[ERROR] Migration verification failed.")
            return False
            
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else "dispute_management.db"
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"[ERROR] Database file '{db_path}' not found.")
        print("Please ensure you're running this script from the backend directory.")
        sys.exit(1)
    
    print(f"Migrating database: {db_path}")
    print("-" * 50)
    
    success = migrate_database(db_path)
    
    print("-" * 50)
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)

# Made with Bob
