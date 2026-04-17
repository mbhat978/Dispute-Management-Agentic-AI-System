"""
Test script for MCP SSE Client

This script tests the new SSE-based MCP client to ensure it can connect
to the persistent server and call tools successfully.

Before running this test:
1. Start the MCP server by running: run_mcp_server.bat
2. Wait for the server to start (you should see "Server running on port 8001")
3. Run this test script: python test_mcp_sse.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from mcp_client import (
    get_transaction_details,
    get_customer_history,
    check_atm_logs,
    get_available_tools
)


def test_connection():
    """Test basic connection to the MCP server"""
    print("=" * 60)
    print("Testing MCP SSE Client Connection")
    print("=" * 60)
    print()
    
    # Test 1: Get available tools
    print("Test 1: Getting available tools...")
    try:
        tools = get_available_tools()
        print(f"✓ Successfully retrieved {len(tools)} tools")
        print()
    except Exception as e:
        print(f"✗ Failed to get tools: {e}")
        return False
    
    # Test 2: Get transaction details
    print("Test 2: Getting transaction details (transaction_id=1)...")
    try:
        result = get_transaction_details(1)
        if "error" in result:
            print(f"✗ Error: {result['error']}")
            return False
        print(f"✓ Successfully retrieved transaction details")
        print(f"  Customer: {result.get('customer_name', 'N/A')}")
        print(f"  Amount: ${result.get('amount', 0)}")
        print(f"  Merchant: {result.get('merchant_name', 'N/A')}")
        print()
    except Exception as e:
        print(f"✗ Failed to get transaction details: {e}")
        return False
    
    # Test 3: Get customer history
    print("Test 3: Getting customer history (customer_id=1)...")
    try:
        result = get_customer_history(1, limit=3)
        if "error" in result:
            print(f"✗ Error: {result['error']}")
            return False
        print(f"✓ Successfully retrieved customer history")
        print(f"  Customer: {result.get('customer_name', 'N/A')}")
        print(f"  Transactions: {len(result.get('transactions', []))}")
        print()
    except Exception as e:
        print(f"✗ Failed to get customer history: {e}")
        return False
    
    # Test 4: Check ATM logs
    print("Test 4: Checking ATM logs (transaction_id=1)...")
    try:
        result = check_atm_logs(1)
        if "error" in result:
            print(f"✗ Error: {result['error']}")
            return False
        print(f"✓ Successfully checked ATM logs")
        print(f"  Status: {result.get('status', 'N/A')}")
        print()
    except Exception as e:
        print(f"✗ Failed to check ATM logs: {e}")
        return False
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    print()
    print("IMPORTANT: Make sure the MCP server is running!")
    print("Run 'run_mcp_server.bat' in a separate terminal first.")
    print()
    input("Press Enter when the server is ready...")
    print()
    
    success = test_connection()
    
    if not success:
        print()
        print("Tests failed. Please check:")
        print("1. Is the MCP server running? (run_mcp_server.bat)")
        print("2. Is the server accessible at http://localhost:8001/sse?")
        print("3. Check the server logs for any errors")
        sys.exit(1)
    
    sys.exit(0)

# Made with Bob
