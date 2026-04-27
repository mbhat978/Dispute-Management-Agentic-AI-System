"""
Seed script to populate the SQLite database with realistic mock data.
This script creates customers, transactions, ATM logs, and dispute tickets
covering various scenarios for testing the dispute management system.
"""

import sys
import io
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Create all tables
Base.metadata.create_all(bind=engine)


def clear_database(db: Session):
    """Clear all existing data from the database."""
    print("Clearing existing data...")
    db.query(models.AuditLog).delete()
    db.query(models.DisputeTicket).delete()
    db.query(models.ATM_Log).delete()
    db.query(models.Transaction).delete()
    db.query(models.LoanAccount).delete()
    db.query(models.Customer).delete()
    db.commit()
    print("Database cleared.")


def create_customers(db: Session):
    """Create dummy customers with different account tiers."""
    print("\nCreating customers...")
    
    customers = [
        models.Customer(
            name="John Smith",
            account_tier="Premium",
            current_account_balance=15000.00,
            card_number="**** **** **** 4921",
            card_status="Active"
        ),
        models.Customer(
            name="Sarah Johnson",
            account_tier="Gold",
            current_account_balance=50000.00,
            card_number="**** **** **** 8832",
            card_status="Active"
        ),
        models.Customer(
            name="Michael Chen",
            account_tier="Basic",
            current_account_balance=3500.00,
            card_number="**** **** **** 1194",
            card_status="Active"
        ),
        models.Customer(
            name="Emily Rodriguez",
            account_tier="Premium",
            current_account_balance=22000.00,
            card_number="**** **** **** 7543",
            card_status="Active"
        ),
        models.Customer(
            name="David Kumar",
            account_tier="Basic",
            current_account_balance=5000.00,
            card_number="**** **** **** 0092",
            card_status="Active"
        )
    ]
    
    db.add_all(customers)
    db.commit()
    
    for customer in customers:
        db.refresh(customer)
        print(f"  ✓ Created: {customer.name} (ID: {customer.id}, Tier: {customer.account_tier})")
    
    return customers


def create_loan_accounts(db: Session, customers):
    """Create mock loan accounts for some customers."""
    print("\nCreating loan accounts...")
    
    loan_accounts = [
        models.LoanAccount(
            customer_id=customers[0].id,  # John Smith
            monthly_emi_amount=5000.00,
            total_outstanding=150000.00
        ),
        models.LoanAccount(
            customer_id=customers[1].id,  # Sarah Johnson
            monthly_emi_amount=8500.00,
            total_outstanding=280000.00
        ),
        models.LoanAccount(
            customer_id=customers[3].id,  # Emily Rodriguez
            monthly_emi_amount=3200.00,
            total_outstanding=95000.00
        )
    ]
    
    db.add_all(loan_accounts)
    db.commit()
    
    for loan in loan_accounts:
        db.refresh(loan)
        customer = db.query(models.Customer).filter(models.Customer.id == loan.customer_id).first()
        print(f"  ✓ Loan ID: {loan.id} - Customer: {customer.name if customer else 'Unknown'}, EMI: ${loan.monthly_emi_amount}, Outstanding: ${loan.total_outstanding}")
    
    return loan_accounts


def create_scenario_transactions(db: Session, customers):
    """Create transactions covering specific test scenarios."""
    print("\nCreating scenario-based transactions...")
    
    base_time = datetime.utcnow() - timedelta(days=7)
    transactions = []
    
    # Scenario 1: High-value international transaction (potential fraud)
    print("\n  Scenario 1: High-value international transaction")
    trans1 = models.Transaction(
        customer_id=customers[1].id,  # Sarah Johnson (Gold tier)
        amount=8500.00,
        merchant_name="Luxury Watches International",
        transaction_date=base_time + timedelta(hours=2),
        status="success",
        is_international=True,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans1)
    db.commit()
    db.refresh(trans1)
    transactions.append(trans1)
    print(f"    ✓ Transaction ID: {trans1.id} - ${trans1.amount} to {trans1.merchant_name}")
    
    # Scenario 2: Failed transaction but amount was deducted (no refund)
    print("\n  Scenario 2: Failed transaction with amount deducted")
    trans2 = models.Transaction(
        customer_id=customers[2].id,  # Michael Chen (Basic tier)
        amount=450.00,
        merchant_name="Electronics Store",
        transaction_date=base_time + timedelta(days=1, hours=5),
        status="failed",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans2)
    db.commit()
    db.refresh(trans2)
    transactions.append(trans2)
    print(f"    ✓ Transaction ID: {trans2.id} - ${trans2.amount} to {trans2.merchant_name} (FAILED)")
    
    # Scenario 3: Standard e-commerce transaction (merchant dispute)
    print("\n  Scenario 3: Standard e-commerce transaction")
    trans3 = models.Transaction(
        customer_id=customers[0].id,  # John Smith (Premium tier)
        amount=299.99,
        merchant_name="TechGadgets Online",
        transaction_date=base_time + timedelta(days=2, hours=10),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans3)
    db.commit()
    db.refresh(trans3)
    transactions.append(trans3)
    print(f"    ✓ Transaction ID: {trans3.id} - ${trans3.amount} to {trans3.merchant_name}")
    
    # Scenario 4: Duplicate charges (two identical transactions within 5 minutes)
    print("\n  Scenario 4: Duplicate charges to same merchant")
    duplicate_time = base_time + timedelta(days=3, hours=14, minutes=30)
    
    trans4a = models.Transaction(
        customer_id=customers[3].id,  # Emily Rodriguez
        amount=89.99,
        merchant_name="Coffee Shop Downtown",
        transaction_date=duplicate_time,
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans4a)
    db.commit()
    db.refresh(trans4a)
    transactions.append(trans4a)
    
    trans4b = models.Transaction(
        customer_id=customers[3].id,  # Emily Rodriguez
        amount=89.99,
        merchant_name="Coffee Shop Downtown",
        transaction_date=duplicate_time + timedelta(minutes=3),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans4b)
    db.commit()
    db.refresh(trans4b)
    transactions.append(trans4b)
    
    print(f"    ✓ Transaction ID: {trans4a.id} - ${trans4a.amount} to {trans4a.merchant_name}")
    print(f"    ✓ Transaction ID: {trans4b.id} - ${trans4b.amount} to {trans4b.merchant_name} (3 minutes later)")
    
    # Scenario 5: ATM transaction with hardware fault
    print("\n  Scenario 5: ATM transaction with hardware fault")
    trans5 = models.Transaction(
        customer_id=customers[4].id,  # David Kumar
        amount=200.00,
        merchant_name="ATM Withdrawal",
        transaction_date=base_time + timedelta(days=4, hours=9),
        status="failed",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans5)
    db.commit()
    db.refresh(trans5)
    transactions.append(trans5)
    
    # Create ATM log with hardware fault
    atm_log = models.ATM_Log(
        transaction_id=trans5.id,
        atm_id="ATM_NYC_5TH_AVE_001",
        status_code="500_HARDWARE_FAULT"
    )
    db.add(atm_log)
    db.commit()
    db.refresh(atm_log)
    
    print(f"    ✓ Transaction ID: {trans5.id} - ${trans5.amount} ATM Withdrawal (FAILED)")
    print(f"    ✓ ATM Log ID: {atm_log.id} - ATM: {atm_log.atm_id}, Status: {atm_log.status_code}")
    
    # Add some successful ATM transactions for comparison
    trans6 = models.Transaction(
        customer_id=customers[0].id,
        amount=100.00,
        merchant_name="ATM Withdrawal",
        transaction_date=base_time + timedelta(days=5, hours=11),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans6)
    db.commit()
    db.refresh(trans6)
    transactions.append(trans6)
    
    atm_log_success = models.ATM_Log(
        transaction_id=trans6.id,
        atm_id="ATM_NYC_MAIN_ST_042",
        status_code="200_DISPENSED"
    )
    db.add(atm_log_success)
    db.commit()
    print(f"    ✓ Transaction ID: {trans6.id} - ${trans6.amount} ATM Withdrawal (SUCCESS)")
    
    # Scenario 6: Salary deposit (credit transaction) - CANNOT BE DISPUTED
    print("\n  Scenario 6: Salary deposit (credit transaction)")
    trans7 = models.Transaction(
        customer_id=customers[0].id,  # John Smith (Premium tier)
        amount=5000.00,
        merchant_name="Payroll Deposit",
        transaction_date=base_time + timedelta(days=6, hours=8),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="credit"
    )
    db.add(trans7)
    db.commit()
    db.refresh(trans7)
    transactions.append(trans7)
    print(f"    ✓ Transaction ID: {trans7.id} - ${trans7.amount} Payroll Deposit (CREDIT)")
    
    return transactions


def create_dispute_tickets(db: Session, transactions):
    """Create dispute tickets for problematic transactions."""
    print("\nCreating dispute tickets...")
    
    disputes = []
    
    # Dispute for high-value international transaction (Scenario 1)
    dispute1 = models.DisputeTicket(
        transaction_id=transactions[0].id,
        customer_id=transactions[0].customer_id,
        dispute_reason="I did not authorize this high-value international transaction. I was not traveling abroad and did not make this purchase.",
        dispute_category=None,  # Will be set by Triage Agent
        status="open",
        final_decision=None,
        decision_reasoning=None,
        resolution_notes=None
    )
    db.add(dispute1)
    disputes.append(dispute1)
    
    # Dispute for failed transaction with deducted amount (Scenario 2)
    dispute2 = models.DisputeTicket(
        transaction_id=transactions[1].id,
        customer_id=transactions[1].customer_id,
        dispute_reason="Transaction shows as failed but the money was still deducted from my account. I never received the goods.",
        dispute_category=None,  # Will be set by Triage Agent
        status="open",
        final_decision=None,
        decision_reasoning=None,
        resolution_notes=None
    )
    db.add(dispute2)
    disputes.append(dispute2)
    
    # Dispute for e-commerce transaction (Scenario 3)
    dispute3 = models.DisputeTicket(
        transaction_id=transactions[2].id,
        customer_id=transactions[2].customer_id,
        dispute_reason="Item received was not as described on the website. Merchant refusing to accept return.",
        dispute_category=None,  # Will be set by Triage Agent
        status="under_investigation",
        final_decision=None,
        decision_reasoning=None,
        resolution_notes=None
    )
    db.add(dispute3)
    disputes.append(dispute3)
    
    # Dispute for duplicate charge (Scenario 4)
    dispute4 = models.DisputeTicket(
        transaction_id=transactions[4].id,  # Second duplicate transaction
        customer_id=transactions[4].customer_id,
        dispute_reason="I was charged twice for the same purchase within minutes. This appears to be a duplicate charge.",
        dispute_category=None,  # Will be set by Triage Agent
        status="open",
        final_decision=None,
        decision_reasoning=None,
        resolution_notes=None
    )
    db.add(dispute4)
    disputes.append(dispute4)
    
    # Dispute for ATM hardware fault (Scenario 5)
    dispute5 = models.DisputeTicket(
        transaction_id=transactions[5].id,
        customer_id=transactions[5].customer_id,
        dispute_reason="ATM did not dispense cash but my account was debited. ATM showed error message.",
        dispute_category=None,  # Will be set by Triage Agent
        status="open",
        final_decision=None,
        decision_reasoning=None,
        resolution_notes=None
    )
    db.add(dispute5)
    disputes.append(dispute5)
    
    db.commit()
    
    for i, dispute in enumerate(disputes, 1):
        db.refresh(dispute)
        print(f"  ✓ Dispute ID: {dispute.id} - Status: {dispute.status}")
        print(f"    Reason: {dispute.dispute_reason[:80]}...")
    
    return disputes


def create_audit_logs(db: Session, disputes):
    """Create sample audit logs for dispute investigation."""
    print("\nCreating audit logs for disputes...")
    
    audit_logs = []
    
    # Audit logs for first dispute (fraud detection)
    log1 = models.AuditLog(
        ticket_id=disputes[0].id,
        agent_name="FraudDetectionAgent",
        action_type="thought",
        description="Analyzing transaction for potential fraud indicators: high-value, international, customer's typical spending pattern.",
        timestamp=datetime.utcnow() - timedelta(hours=2)
    )
    audit_logs.append(log1)
    
    log2 = models.AuditLog(
        ticket_id=disputes[0].id,
        agent_name="FraudDetectionAgent",
        action_type="tool_call",
        description="Checking customer's transaction history for international purchases.",
        timestamp=datetime.utcnow() - timedelta(hours=1, minutes=55)
    )
    audit_logs.append(log2)
    
    log3 = models.AuditLog(
        ticket_id=disputes[0].id,
        agent_name="FraudDetectionAgent",
        action_type="observation",
        description="Customer has no prior international transactions in the last 12 months. Flagging for human review.",
        timestamp=datetime.utcnow() - timedelta(hours=1, minutes=50)
    )
    audit_logs.append(log3)
    
    # Audit log for ATM dispute
    log4 = models.AuditLog(
        ticket_id=disputes[4].id,
        agent_name="ATMDisputeAgent",
        action_type="tool_call",
        description="Retrieving ATM log for transaction verification.",
        timestamp=datetime.utcnow() - timedelta(hours=1)
    )
    audit_logs.append(log4)
    
    log5 = models.AuditLog(
        ticket_id=disputes[4].id,
        agent_name="ATMDisputeAgent",
        action_type="observation",
        description="ATM log shows status code 500_HARDWARE_FAULT. Cash was not dispensed. Recommending automatic approval.",
        timestamp=datetime.utcnow() - timedelta(minutes=55)
    )
    audit_logs.append(log5)
    
    db.add_all(audit_logs)
    db.commit()
    
    print(f"  ✓ Created {len(audit_logs)} audit log entries")
    
    return audit_logs


def print_summary(db: Session):
    """Print summary of seeded data."""
    print("\n" + "="*60)
    print("DATABASE SEEDING SUMMARY")
    print("="*60)
    
    customer_count = db.query(models.Customer).count()
    loan_count = db.query(models.LoanAccount).count()
    transaction_count = db.query(models.Transaction).count()
    atm_log_count = db.query(models.ATM_Log).count()
    dispute_count = db.query(models.DisputeTicket).count()
    audit_log_count = db.query(models.AuditLog).count()
    
    print(f"\n📊 Total Records Created:")
    print(f"  • Customers: {customer_count}")
    print(f"  • Loan Accounts: {loan_count}")
    print(f"  • Transactions: {transaction_count}")
    print(f"  • ATM Logs: {atm_log_count}")
    print(f"  • Dispute Tickets: {dispute_count}")
    print(f"  • Audit Logs: {audit_log_count}")
    
    print(f"\n🎯 Scenario Coverage:")
    print(f"  ✓ High-value international transaction")
    print(f"  ✓ Failed transaction with amount deducted")
    print(f"  ✓ Standard e-commerce transaction")
    print(f"  ✓ Duplicate charges (same merchant, 3 min apart)")
    print(f"  ✓ ATM transaction with hardware fault")
    print(f"  ✓ Loan/EMI accounts for dispute scenarios")
    
    print("\n" + "="*60)
    print("✅ Database seeding completed successfully!")
    print("="*60 + "\n")


def main():
    """Main function to seed the database."""
    print("\n" + "="*60)
    print("BANKING DISPUTE MANAGEMENT - DATABASE SEEDER")
    print("="*60)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_database(db)
        
        # Create data in order
        customers = create_customers(db)
        loan_accounts = create_loan_accounts(db, customers)
        transactions = create_scenario_transactions(db, customers)
        disputes = create_dispute_tickets(db, transactions)
        audit_logs = create_audit_logs(db, disputes)
        
        # Print summary
        print_summary(db)
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
