"""
Phase 4: Testing and Simulation Script
=======================================
This script tests the ReAct agents against real-world dispute scenarios.
It fetches valid ticket_ids and customer_ids from the SQLite database and
sends POST requests to the dispute processing endpoint.

Scenarios Tested:
1. Fraud Scenario - Unauthorized international transaction
2. ATM Scenario - ATM error with account debit
3. Duplicate Scenario - Double charge for same purchase
4. Merchant Dispute Scenario - Empty package delivery

Usage:
    python simulate_disputes.py
"""

import requests
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional


# Configuration
API_BASE_URL = "http://localhost:8000"
PROCESS_ENDPOINT = f"{API_BASE_URL}/api/disputes/process"
DATABASE_PATH = "dispute_management.db"


# Test Scenarios
SCENARIOS = [
    {
        "name": "Fraud Scenario",
        "query": "I am looking at my statement and there is a massive charge in a foreign country, but my card is in my wallet.",
        "expected_category": "fraud",
        "description": "Unauthorized international transaction - customer claims card is in possession"
    },
    {
        "name": "ATM Scenario",
        "query": "I tried to withdraw cash, the machine showed an error screen, but I still got a debit SMS.",
        "expected_category": "atm_dispute",
        "description": "ATM hardware fault - no cash dispensed but account debited"
    },
    {
        "name": "Duplicate Scenario",
        "query": "I bought a coffee today and I see you guys charged me twice for the exact same amount.",
        "expected_category": "duplicate_charge",
        "description": "Duplicate charge - same merchant, same amount, short time window"
    },
    {
        "name": "Merchant Dispute Scenario",
        "query": "I ordered a laptop from an online store, but when the package arrived, the box was completely empty.",
        "expected_category": "merchant_dispute",
        "description": "Merchant dispute - goods not as described or not received"
    }
]


def print_header(text: str, char: str = "=") -> None:
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")


def print_section(text: str) -> None:
    """Print a section divider."""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print(f"{'─' * 80}\n")


def get_database_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error connecting to database: {e}")
        raise


def fetch_valid_ids() -> Tuple[List[int], List[int]]:
    """
    Fetch valid ticket_ids and customer_ids from the database.
    
    Returns:
        Tuple of (ticket_ids, customer_ids)
    """
    print_section("Fetching Valid IDs from Database")
    
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Fetch all ticket IDs
        cursor.execute("SELECT id FROM dispute_tickets ORDER BY id")
        ticket_ids = [row[0] for row in cursor.fetchall()]
        
        # Fetch all customer IDs
        cursor.execute("SELECT id FROM customers ORDER BY id")
        customer_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"✓ Found {len(ticket_ids)} dispute tickets: {ticket_ids}")
        print(f"✓ Found {len(customer_ids)} customers: {customer_ids}")
        
        if not ticket_ids or not customer_ids:
            raise ValueError("No data found in database. Please run seed_data.py first.")
        
        return ticket_ids, customer_ids
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        raise
    finally:
        conn.close()


def get_ticket_details(ticket_id: int) -> Optional[Dict]:
    """
    Fetch details for a specific ticket from the database.
    
    Args:
        ticket_id: The dispute ticket ID
        
    Returns:
        Dictionary with ticket details or None if not found
    """
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                dt.id as ticket_id,
                dt.customer_id,
                dt.transaction_id,
                dt.dispute_reason,
                dt.status,
                c.name as customer_name,
                c.account_tier,
                t.amount,
                t.merchant_name,
                t.is_international
            FROM dispute_tickets dt
            JOIN customers c ON dt.customer_id = c.id
            JOIN transactions t ON dt.transaction_id = t.id
            WHERE dt.id = ?
        """, (ticket_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
        
    except sqlite3.Error as e:
        print(f"❌ Error fetching ticket details: {e}")
        return None
    finally:
        conn.close()


def check_api_health() -> bool:
    """
    Check if the API is running and healthy.
    
    Returns:
        True if API is healthy, False otherwise
    """
    print_section("Checking API Health")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API is healthy and running")
            return True
        else:
            print(f"⚠ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Make sure the FastAPI server is running on {API_BASE_URL}")
        return False


def process_dispute(ticket_id: int, customer_query: str, scenario_name: str) -> Optional[Dict]:
    """
    Send a POST request to process a dispute.
    
    Args:
        ticket_id: The dispute ticket ID
        customer_query: The customer's query/complaint
        scenario_name: Name of the test scenario
        
    Returns:
        Response data as dictionary or None if request failed
    """
    print(f"\n🚀 Processing: {scenario_name}")
    print(f"   Ticket ID: {ticket_id}")
    print(f"   Query: {customer_query[:80]}...")
    
    payload = {
        "ticket_id": ticket_id,
        "customer_query": customer_query
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            PROCESS_ENDPOINT,
            json=payload,
            timeout=120  # 2 minutes timeout for AI processing
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Request successful (took {elapsed_time:.2f}s)")
            return data
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out after 120 seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None


def print_result(scenario: Dict, result: Optional[Dict]) -> None:
    """
    Print the result of a dispute processing request.
    
    Args:
        scenario: The test scenario dictionary
        result: The API response data
    """
    print(f"\n{'═' * 80}")
    print(f"  RESULT: {scenario['name']}")
    print(f"{'═' * 80}")
    
    if not result:
        print("❌ No result received")
        return
    
    print(f"\n📋 Scenario Details:")
    print(f"   Description: {scenario['description']}")
    print(f"   Expected Category: {scenario['expected_category']}")
    
    print(f"\n🤖 AI Analysis:")
    print(f"   Dispute Category: {result.get('dispute_category', 'N/A')}")
    print(f"   Final Decision: {result.get('final_decision', 'N/A').upper()}")
    
    # Check if category matches expected
    actual_category = result.get('dispute_category', '').lower()
    expected_category = scenario['expected_category'].lower()
    
    if actual_category == expected_category:
        print(f"   ✓ Category matches expected")
    else:
        print(f"   ⚠ Category mismatch (expected: {expected_category})")
    
    # Print gathered data summary
    gathered_data = result.get('gathered_data', {})
    if gathered_data:
        print(f"\n📊 Evidence Gathered:")
        for key, value in gathered_data.items():
            if isinstance(value, dict):
                print(f"   • {key}: {len(value)} items")
            elif isinstance(value, list):
                print(f"   • {key}: {len(value)} entries")
            else:
                print(f"   • {key}: {value}")
    
    # Print audit trail summary
    audit_trail = result.get('audit_trail', [])
    if audit_trail:
        print(f"\n📝 Audit Trail: {len(audit_trail)} entries")
        
        # Count by action type
        action_counts = {}
        for entry in audit_trail:
            action_type = entry.get('action_type', 'unknown')
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        for action_type, count in action_counts.items():
            print(f"   • {action_type}: {count}")
    
    print(f"\n{'═' * 80}\n")


def run_simulation() -> None:
    """
    Main simulation function that runs all test scenarios.
    """
    print_header("PHASE 4: DISPUTE RESOLUTION TESTING & SIMULATION")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check API health
    if not check_api_health():
        print("\n❌ Cannot proceed - API is not available")
        print("   Please start the FastAPI server with: python main.py")
        return
    
    # Fetch valid IDs from database
    try:
        ticket_ids, customer_ids = fetch_valid_ids()
    except Exception as e:
        print(f"\n❌ Failed to fetch IDs from database: {e}")
        print("   Please ensure the database is seeded with: python seed_data.py")
        return
    
    # Ensure we have enough tickets for all scenarios
    if len(ticket_ids) < len(SCENARIOS):
        print(f"\n⚠ Warning: Only {len(ticket_ids)} tickets available for {len(SCENARIOS)} scenarios")
        print("   Some scenarios will reuse ticket IDs")
    
    # Run each scenario
    print_header("RUNNING TEST SCENARIOS", "=")
    
    results = []
    for i, scenario in enumerate(SCENARIOS):
        # Use ticket IDs cyclically if we don't have enough
        ticket_id = ticket_ids[i % len(ticket_ids)]
        
        # Get ticket details for context
        ticket_details = get_ticket_details(ticket_id)
        if ticket_details:
            print(f"\n📌 Using Ticket #{ticket_id}:")
            print(f"   Customer: {ticket_details['customer_name']} ({ticket_details['account_tier']})")
            print(f"   Transaction: ${ticket_details['amount']} to {ticket_details['merchant_name']}")
        
        # Process the dispute
        result = process_dispute(ticket_id, scenario['query'], scenario['name'])
        
        # Store result
        results.append({
            'scenario': scenario,
            'ticket_id': ticket_id,
            'result': result
        })
        
        # Print result
        print_result(scenario, result)
        
        # Wait between requests to avoid overwhelming the system
        if i < len(SCENARIOS) - 1:
            print("⏳ Waiting 3 seconds before next scenario...")
            time.sleep(3)
    
    # Print final summary
    print_header("SIMULATION SUMMARY", "=")
    
    successful = sum(1 for r in results if r['result'] is not None)
    failed = len(results) - successful
    
    print(f"📊 Overall Results:")
    print(f"   Total Scenarios: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    
    print(f"\n📋 Detailed Results:")
    for i, r in enumerate(results, 1):
        scenario_name = r['scenario']['name']
        result = r['result']
        
        if result:
            category = result.get('dispute_category', 'N/A')
            decision = result.get('final_decision', 'N/A').upper()
            print(f"   {i}. {scenario_name}")
            print(f"      Category: {category} | Decision: {decision}")
        else:
            print(f"   {i}. {scenario_name}")
            print(f"      ❌ FAILED")
    
    print(f"\n{'═' * 80}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═' * 80}\n")


if __name__ == "__main__":
    try:
        run_simulation()
    except KeyboardInterrupt:
        print("\n\n⚠ Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        raise

# Made with Bob
