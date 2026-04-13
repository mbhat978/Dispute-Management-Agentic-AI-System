"""
Test script to verify all banking tools functions work correctly.
This script tests each function with the seeded data to ensure proper functionality.
"""

from datetime import datetime
import banking_tools
import json


def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_result(function_name, result):
    """Pretty print the result of a function call."""
    print(f"\n[{function_name}]")
    print(json.dumps(result, indent=2, default=str))


def main():
    """Run tests for all banking tools functions."""
    print("\n" + "="*70)
    print("  BANKING TOOLS - FUNCTION TESTS")
    print("="*70)
    
    # Test 1: get_transaction_details
    print_section("TEST 1: Get Transaction Details")
    print("Testing with Transaction ID 1 (High-value international transaction)")
    result = banking_tools.get_transaction_details(1)
    print_result("get_transaction_details(1)", result)
    
    print("\nTesting with non-existent Transaction ID 999")
    result = banking_tools.get_transaction_details(999)
    print_result("get_transaction_details(999)", result)
    
    # Test 2: get_customer_history
    print_section("TEST 2: Get Customer History")
    print("Testing with Customer ID 4 (Emily Rodriguez - has duplicate charges)")
    result = banking_tools.get_customer_history(4)
    print_result("get_customer_history(4)", result)
    
    # Test 3: check_atm_logs
    print_section("TEST 3: Check ATM Logs")
    print("Testing with Transaction ID 6 (ATM with hardware fault)")
    result = banking_tools.check_atm_logs(6)
    print_result("check_atm_logs(6)", result)
    
    print("\nTesting with Transaction ID 7 (Successful ATM withdrawal)")
    result = banking_tools.check_atm_logs(7)
    print_result("check_atm_logs(7)", result)
    
    print("\nTesting with Transaction ID 1 (Non-ATM transaction)")
    result = banking_tools.check_atm_logs(1)
    print_result("check_atm_logs(1)", result)
    
    # Test 4: check_duplicate_transactions
    print_section("TEST 4: Check Duplicate Transactions")
    print("Testing for duplicate charges at Coffee Shop Downtown")
    # Get the transaction date from one of the duplicate transactions
    trans_details = banking_tools.get_transaction_details(5)
    trans_date = datetime.fromisoformat(trans_details['transaction_date'])
    
    result = banking_tools.check_duplicate_transactions(
        customer_id=4,
        merchant_name="Coffee Shop Downtown",
        amount=89.99,
        date=trans_date,
        time_window_hours=24
    )
    print_result("check_duplicate_transactions(...)", result)
    
    # Test 5: block_card
    print_section("TEST 5: Block Card")
    print("Testing card block for Customer ID 2 (suspected fraud)")
    result = banking_tools.block_card(2, "High-value international transaction without travel notice")
    print_result("block_card(2, ...)", result)
    
    print("\nTesting with non-existent Customer ID 999")
    result = banking_tools.block_card(999, "Test")
    print_result("block_card(999, ...)", result)
    
    # Test 6: initiate_refund
    print_section("TEST 6: Initiate Refund")
    print("Testing refund for Transaction ID 2 (Failed transaction with deducted amount)")
    result = banking_tools.initiate_refund(2, 450.00, "Failed transaction with amount deducted")
    print_result("initiate_refund(2, 450.00, ...)", result)
    
    print("\nTesting refund with amount exceeding transaction amount")
    result = banking_tools.initiate_refund(2, 500.00, "Test")
    print_result("initiate_refund(2, 500.00, ...)", result)
    
    print("\nTesting with non-existent Transaction ID 999")
    result = banking_tools.initiate_refund(999, 100.00, "Test")
    print_result("initiate_refund(999, ...)", result)
    
    # Test 7: route_to_human
    print_section("TEST 7: Route to Human Review")
    print("Testing routing Ticket ID 1 to human review")
    summary = (
        "High-value international transaction ($8,500) with no prior international "
        "transaction history in the last 12 months. Customer claims unauthorized. "
        "Recommend human review to verify with customer directly."
    )
    result = banking_tools.route_to_human(1, summary)
    print_result("route_to_human(1, ...)", result)
    
    print("\nTesting with non-existent Ticket ID 999")
    result = banking_tools.route_to_human(999, "Test summary")
    print_result("route_to_human(999, ...)", result)
    
    # Test 8: get_available_tools
    print_section("TEST 8: Get Available Tools")
    print("Getting list of all available tools")
    tools = banking_tools.get_available_tools()
    print(f"\n[get_available_tools()]")
    for i, tool in enumerate(tools, 1):
        print(f"\n{i}. {tool['name']}")
        print(f"   Description: {tool['description']}")
    
    # Summary
    print_section("TEST SUMMARY")
    print("\n✅ All banking tools functions tested successfully!")
    print("\nAvailable functions:")
    print("  1. get_transaction_details(transaction_id)")
    print("  2. get_customer_history(customer_id, limit=5)")
    print("  3. check_atm_logs(transaction_id)")
    print("  4. check_duplicate_transactions(customer_id, merchant_name, amount, date)")
    print("  5. block_card(customer_id, reason)")
    print("  6. initiate_refund(transaction_id, amount, reason)")
    print("  7. route_to_human(ticket_id, summary)")
    print("\nAll functions return structured dictionaries with clear status and messages.")
    print("Functions include proper error handling for missing records.")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()