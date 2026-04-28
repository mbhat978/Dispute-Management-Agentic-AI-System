"""
Seed script to populate the SQLite database with realistic mock data.
This script creates 6 customers with necessary transactions for testing all 10 scenarios.
Includes 15 historic disputes for one customer to establish high-risk merchant pattern.
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
    print("✓ Database cleared.")


def create_customers(db: Session):
    """Create 6 customers with different profiles for comprehensive testing."""
    print("\n📋 Creating 6 customers...")
    
    customers = [
        # Customer 1: Premium tier - For fraud scenarios (international + velocity)
        models.Customer(
            name="Priya Sharma",
            account_tier="Premium",
            current_account_balance=12500.00,
            card_number="**** **** **** 9876",
            card_status="Active"
        ),
        # Customer 2: Gold tier - For merchant disputes (Amazon + high-risk merchant)
        models.Customer(
            name="Rahul Verma",
            account_tier="Gold",
            current_account_balance=8500.00,
            card_number="**** **** **** 5432",
            card_status="Active"
        ),
        # Customer 3: Basic tier - For ATM disputes
        models.Customer(
            name="Ananya Patel",
            account_tier="Basic",
            current_account_balance=3500.00,
            card_number="**** **** **** 3210",
            card_status="Active"
        ),
        # Customer 4: Premium tier - For duplicate transaction + EMI dispute
        models.Customer(
            name="Vikram Singh",
            account_tier="Premium",
            current_account_balance=25000.00,
            card_number="**** **** **** 6789",
            card_status="Active"
        ),
        # Customer 5: Gold tier - For subscription + refund disputes
        models.Customer(
            name="Meera Reddy",
            account_tier="Gold",
            current_account_balance=6500.00,
            card_number="**** **** **** 1357",
            card_status="Active"
        ),
        # Customer 6: Basic tier - For incorrect amount + quality disputes
        models.Customer(
            name="Karthik Menon",
            account_tier="Basic",
            current_account_balance=4200.00,
            card_number="**** **** **** 4680",
            card_status="Active"
        )
    ]
    
    db.add_all(customers)
    db.commit()
    
    for customer in customers:
        db.refresh(customer)
        print(f"  ✓ {customer.name} (ID: {customer.id}, Tier: {customer.account_tier}, Balance: ${customer.current_account_balance:,.2f})")
    
    return customers


def create_loan_accounts(db: Session, customers):
    """Create loan accounts for EMI dispute testing."""
    print("\n💰 Creating loan accounts...")
    
    loan_accounts = [
        # Loan for Customer 4 (Vikram Singh) - for EMI dispute scenario
        models.LoanAccount(
            customer_id=customers[3].id,
            monthly_emi_amount=1200.00,
            total_outstanding=35000.00
        )
    ]
    
    db.add_all(loan_accounts)
    db.commit()
    
    for loan in loan_accounts:
        db.refresh(loan)
        customer = db.query(models.Customer).filter(models.Customer.id == loan.customer_id).first()
        customer_name = customer.name if customer else "Unknown"
        print(f"  ✓ Loan ID: {loan.id} - {customer_name}, EMI: ${loan.monthly_emi_amount:,.2f}, Outstanding: ${loan.total_outstanding:,.2f}")
    
    return loan_accounts


def create_common_transactions(db: Session, customers):
    """Create 1-2 common successful transactions per customer for context."""
    print("\n✅ Creating common successful transactions...")
    
    base_time = datetime.utcnow() - timedelta(days=30)
    transactions = []
    
    common_txns = [
        (customers[0].id, 1200.00, "Swiggy", False),
        (customers[0].id, 850.00, "Uber", False),
        (customers[1].id, 2500.00, "Flipkart", False),
        (customers[1].id, 450.00, "BookMyShow", False),
        (customers[2].id, 180.00, "Starbucks", False),
        (customers[2].id, 320.00, "Big Bazaar", False),
        (customers[3].id, 5000.00, "Croma", False),
        (customers[3].id, 1800.00, "Westside", False),
        (customers[4].id, 3200.00, "Zomato", False),
        (customers[4].id, 890.00, "Myntra", False),
        (customers[5].id, 1500.00, "Apple Store", False),
        (customers[5].id, 650.00, "Reliance Digital", False),
    ]
    
    for cust_id, amount, merchant, is_intl in common_txns:
        trans = models.Transaction(
            customer_id=cust_id,
            amount=amount,
            merchant_name=merchant,
            transaction_date=base_time + timedelta(days=2, hours=12),
            status="success",
            is_international=is_intl,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans)
        db.commit()
        db.refresh(trans)
        transactions.append(trans)
    
    print(f"  ✓ Created {len(common_txns)} common successful transactions")
    return transactions


def create_test_scenario_transactions(db: Session, customers):
    """Create transactions for all 10 test scenarios from AGENT_TESTING_GUIDE.md."""
    print("\n🎯 Creating test scenario transactions...")
    
    base_time = datetime.utcnow() - timedelta(days=30)
    transactions = []
    
    # ========================================================================
    # SCENARIO 1: FRAUDULENT TRANSACTION - International (Customer 1)
    # ========================================================================
    print("\n  📍 Scenario 1: Fraudulent Transaction - International")
    trans_fraud = models.Transaction(
        customer_id=customers[0].id,  # Priya Sharma
        amount=250.00,
        merchant_name="Harrods Department Store",
        transaction_date=base_time + timedelta(days=1, hours=14),
        status="success",
        is_international=True,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_fraud)
    db.commit()
    db.refresh(trans_fraud)
    transactions.append(trans_fraud)
    print(f"    ✓ ID {trans_fraud.id}: ${trans_fraud.amount:,.2f} to {trans_fraud.merchant_name} (London, UK)")
    
    # ========================================================================
    # SCENARIO 2: MERCHANT DISPUTE - Item Not Delivered (Customer 2)
    # ========================================================================
    print("\n  📍 Scenario 2: Merchant Dispute - Item Not Delivered")
    trans_amazon = models.Transaction(
        customer_id=customers[1].id,  # Rahul Verma
        amount=799.99,
        merchant_name="Amazon India",
        transaction_date=base_time + timedelta(days=5, hours=11),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_amazon)
    db.commit()
    db.refresh(trans_amazon)
    transactions.append(trans_amazon)
    print(f"    ✓ ID {trans_amazon.id}: ${trans_amazon.amount:,.2f} to {trans_amazon.merchant_name} (iPhone not delivered)")
    
    # ========================================================================
    # SCENARIO 3: ATM DISPUTE - Cash Not Dispensed (Customer 3)
    # ========================================================================
    print("\n  📍 Scenario 3: ATM Dispute - Cash Not Dispensed")
    trans_atm_fault = models.Transaction(
        customer_id=customers[2].id,  # Ananya Patel
        amount=100.00,
        merchant_name="ATM Withdrawal",
        transaction_date=base_time + timedelta(days=7, hours=14, minutes=30),
        status="failed",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_atm_fault)
    db.commit()
    db.refresh(trans_atm_fault)
    transactions.append(trans_atm_fault)
    
    # Create ATM log with dispense fault
    atm_log_fault = models.ATM_Log(
        transaction_id=trans_atm_fault.id,
        atm_id="ATM_MUM_BKC_001",
        status_code="DISPENSE_FAULT"
    )
    db.add(atm_log_fault)
    db.commit()
    print(f"    ✓ ID {trans_atm_fault.id}: ${trans_atm_fault.amount:,.2f} ATM Withdrawal (FAULT - No cash dispensed)")
    
    # ATM Success case for comparison (Test Case 3.2)
    trans_atm_success = models.Transaction(
        customer_id=customers[2].id,  # Ananya Patel (same customer)
        amount=50.00,
        merchant_name="ATM Withdrawal",
        transaction_date=base_time + timedelta(days=8, hours=10),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_atm_success)
    db.commit()
    db.refresh(trans_atm_success)
    transactions.append(trans_atm_success)
    
    atm_log_success = models.ATM_Log(
        transaction_id=trans_atm_success.id,
        atm_id="ATM_MUM_BKC_001",
        status_code="200_DISPENSED"
    )
    db.add(atm_log_success)
    db.commit()
    print(f"    ✓ ID {trans_atm_success.id}: ${trans_atm_success.amount:,.2f} ATM Withdrawal (SUCCESS - for comparison)")
    
    # ========================================================================
    # SCENARIO 4: DUPLICATE TRANSACTION (Customer 4)
    # ========================================================================
    print("\n  📍 Scenario 4: Duplicate Transaction")
    duplicate_time = base_time + timedelta(days=10, hours=19, minutes=30)
    
    trans_dup1 = models.Transaction(
        customer_id=customers[3].id,  # Vikram Singh
        amount=25.00,
        merchant_name="Taj Restaurant",
        transaction_date=duplicate_time,
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_dup1)
    db.commit()
    db.refresh(trans_dup1)
    transactions.append(trans_dup1)
    
    trans_dup2 = models.Transaction(
        customer_id=customers[3].id,  # Vikram Singh
        amount=25.00,
        merchant_name="Taj Restaurant",
        transaction_date=duplicate_time + timedelta(minutes=5),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_dup2)
    db.commit()
    db.refresh(trans_dup2)
    transactions.append(trans_dup2)
    
    print(f"    ✓ ID {trans_dup1.id}: ${trans_dup1.amount:,.2f} to {trans_dup1.merchant_name}")
    print(f"    ✓ ID {trans_dup2.id}: ${trans_dup2.amount:,.2f} to {trans_dup2.merchant_name} (5 min later - DUPLICATE)")
    
    # ========================================================================
    # SCENARIO 5: INCORRECT AMOUNT - Overcharged (Customer 6)
    # ========================================================================
    print("\n  📍 Scenario 5: Incorrect Amount - Overcharged")
    trans_overcharge = models.Transaction(
        customer_id=customers[5].id,  # Karthik Menon
        amount=50.00,
        merchant_name="Electronics Store",
        transaction_date=base_time + timedelta(days=12, hours=16),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_overcharge)
    db.commit()
    db.refresh(trans_overcharge)
    transactions.append(trans_overcharge)
    print(f"    ✓ ID {trans_overcharge.id}: ${trans_overcharge.amount:,.2f} to {trans_overcharge.merchant_name} (Receipt shows $45.00)")
    
    # ========================================================================
    # SCENARIO 6: SUBSCRIPTION DISPUTE (Customer 5)
    # ========================================================================
    print("\n  📍 Scenario 6: Subscription Dispute - Cancelled but Still Charged")
    subscription_start = base_time - timedelta(days=330)
    
    # Create 11 months of Netflix charges (to establish subscription pattern)
    for month in range(11):
        trans_netflix = models.Transaction(
            customer_id=customers[4].id,  # Meera Reddy
            amount=15.99,
            merchant_name="Netflix",
            transaction_date=subscription_start + timedelta(days=30*month),
            status="success",
            is_international=False,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans_netflix)
        db.commit()
        db.refresh(trans_netflix)
        transactions.append(trans_netflix)
    
    # Disputed charge (after claimed cancellation on day 330)
    trans_netflix_disputed = models.Transaction(
        customer_id=customers[4].id,  # Meera Reddy
        amount=15.99,
        merchant_name="Netflix",
        transaction_date=subscription_start + timedelta(days=360),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_netflix_disputed)
    db.commit()
    db.refresh(trans_netflix_disputed)
    transactions.append(trans_netflix_disputed)
    print(f"    ✓ ID {trans_netflix_disputed.id}: ${trans_netflix_disputed.amount:,.2f} to Netflix (Cancelled on day 330, charged on day 360)")
    
    # Test Case 6.2: Active Spotify subscription (no cancellation) - for comparison
    print("\n  📍 Scenario 6.2: Active Subscription - Spotify (No Cancellation)")
    spotify_start = base_time - timedelta(days=330)
    
    # Create 12 months of Spotify charges (active subscription)
    for month in range(12):
        trans_spotify = models.Transaction(
            customer_id=customers[3].id,  # Vikram Singh
            amount=10.99,
            merchant_name="Spotify",
            transaction_date=spotify_start + timedelta(days=30*month),
            status="success",
            is_international=False,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans_spotify)
        db.commit()
        db.refresh(trans_spotify)
        transactions.append(trans_spotify)
    
    print(f"    ✓ Created 12 Spotify charges for {customers[3].name} (Active subscription - no cancellation)")
    
    # ========================================================================
    # SCENARIO 7: LOAN/EMI DISPUTE (Customer 4)
    # ========================================================================
    print("\n  📍 Scenario 7: Loan/EMI Dispute - Incorrect Amount")
    trans_emi_wrong = models.Transaction(
        customer_id=customers[3].id,  # Vikram Singh (has loan with EMI $1200)
        amount=1500.00,  # Charged $1500 instead of $1200
        merchant_name="Loan EMI Payment",
        transaction_date=base_time + timedelta(days=15, hours=9),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_emi_wrong)
    db.commit()
    db.refresh(trans_emi_wrong)
    transactions.append(trans_emi_wrong)
    print(f"    ✓ ID {trans_emi_wrong.id}: ${trans_emi_wrong.amount:,.2f} EMI (Should be $1200 - Overcharged $300)")
    
    # ========================================================================
    # SCENARIO 8: REFUND NOT RECEIVED (Customer 5)
    # ========================================================================
    print("\n  📍 Scenario 8: Refund Not Received")
    trans_refund_delayed = models.Transaction(
        customer_id=customers[4].id,  # Meera Reddy
        amount=35.00,
        merchant_name="Fashion Store",
        transaction_date=base_time + timedelta(days=8, hours=14),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_refund_delayed)
    db.commit()
    db.refresh(trans_refund_delayed)
    transactions.append(trans_refund_delayed)
    print(f"    ✓ ID {trans_refund_delayed.id}: ${trans_refund_delayed.amount:,.2f} to {trans_refund_delayed.merchant_name} (Refund promised 10 days ago)")
    
    # ========================================================================
    # SCENARIO 9: QUALITY/SERVICE DISPUTE (Customer 6)
    # ========================================================================
    print("\n  📍 Scenario 9: Quality/Service Dispute")
    trans_quality = models.Transaction(
        customer_id=customers[5].id,  # Karthik Menon
        amount=250.00,
        merchant_name="Electronics Mart",
        transaction_date=base_time + timedelta(days=18, hours=11),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_quality)
    db.commit()
    db.refresh(trans_quality)
    transactions.append(trans_quality)
    print(f"    ✓ ID {trans_quality.id}: ${trans_quality.amount:,.2f} to {trans_quality.merchant_name} (Damaged product)")
    
    # ========================================================================
    # SCENARIO 10: CHARGEBACK - Merchant Non-Response (Customer 1)
    # ========================================================================
    print("\n  📍 Scenario 10: Chargeback - Merchant Non-Response")
    trans_chargeback = models.Transaction(
        customer_id=customers[0].id,  # Priya Sharma
        amount=180.00,
        merchant_name="Online Gadgets",
        transaction_date=base_time + timedelta(days=5, hours=10),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_chargeback)
    db.commit()
    db.refresh(trans_chargeback)
    transactions.append(trans_chargeback)
    print(f"    ✓ ID {trans_chargeback.id}: ${trans_chargeback.amount:,.2f} to {trans_chargeback.merchant_name} (Merchant not responding for 15 days)")
    
    return transactions


def create_high_risk_merchant_history(db: Session, customers):
    """Create 15 historic disputes for Customer 2 with ShopXYZ Online (high-risk merchant)."""
    print("\n📊 Creating High-Risk Merchant History: ShopXYZ Online")
    
    base_time = datetime.utcnow() - timedelta(days=60)
    shopxyz_transaction_ids = []
    
    # Create 15 past transactions with ShopXYZ Online
    for i in range(15):
        trans_shopxyz = models.Transaction(
            customer_id=customers[1].id,  # Rahul Verma
            amount=100.00 + (i * 10),
            merchant_name="ShopXYZ Online",
            transaction_date=base_time - timedelta(days=45 - (i * 3)),
            status="success",
            is_international=False,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans_shopxyz)
        db.commit()
        db.refresh(trans_shopxyz)
        shopxyz_transaction_ids.append(trans_shopxyz.id)
    
    # Create 15 dispute tickets for ShopXYZ Online
    # 13 approved, 2 denied = 86.7% approval rate (HIGH-RISK)
    approved_count = 0
    denied_count = 0
    
    for i in range(15):
        # First 13 are approved, last 2 are denied
        if i < 13:
            ticket_status = "resolved"
            ticket_decision = "approve"
            approved_count += 1
        else:
            ticket_status = "resolved"
            ticket_decision = "deny"
            denied_count += 1
        
        dispute_ticket = models.DisputeTicket(
            transaction_id=shopxyz_transaction_ids[i],
            customer_id=customers[1].id,
            dispute_category="merchant_dispute",
            dispute_reason=f"ShopXYZ dispute #{i+1}: Item not received or empty box",
            status=ticket_status,
            final_decision=ticket_decision,
            resolution_notes=f"Historical dispute - {'Approved' if ticket_decision == 'approve' else 'Denied'}",
            created_at=base_time - timedelta(days=45 - (i * 3)),
            updated_at=base_time - timedelta(days=40 - (i * 3))
        )
        db.add(dispute_ticket)
        db.commit()
    
    print(f"  ✓ Created 15 historical transactions for ShopXYZ Online")
    print(f"  ✓ Created 15 dispute tickets: {approved_count} approved, {denied_count} denied")
    print(f"  ✓ Approval rate: {(approved_count/15)*100:.1f}% (HIGH-RISK MERCHANT)")
    
    # Now create the current dispute transaction for testing
    trans_shopxyz_current = models.Transaction(
        customer_id=customers[1].id,  # Rahul Verma
        amount=150.00,
        merchant_name="ShopXYZ Online",
        transaction_date=datetime.utcnow() - timedelta(days=6),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_shopxyz_current)
    db.commit()
    db.refresh(trans_shopxyz_current)
    print(f"  ✓ ID {trans_shopxyz_current.id}: ${trans_shopxyz_current.amount:,.2f} to ShopXYZ Online (Current dispute - Empty box)")
    
    return trans_shopxyz_current


def print_summary(db: Session):
    """Print summary of seeded data with scenario mapping."""
    print("\n" + "="*70)
    print("DATABASE SEEDING SUMMARY")
    print("="*70)
    
    customer_count = db.query(models.Customer).count()
    loan_count = db.query(models.LoanAccount).count()
    transaction_count = db.query(models.Transaction).count()
    atm_log_count = db.query(models.ATM_Log).count()
    dispute_count = db.query(models.DisputeTicket).count()
    
    print(f"\n📊 Total Records Created:")
    print(f"  • Customers: {customer_count}")
    print(f"  • Loan Accounts: {loan_count}")
    print(f"  • Transactions: {transaction_count}")
    print(f"  • ATM Logs: {atm_log_count}")
    print(f"  • Historic Disputes: {dispute_count}")
    
    print(f"\n🎯 Test Scenario Coverage (AGENT_TESTING_GUIDE.md):")
    print(f"  ✓ Scenario 1: Fraudulent Transaction (International)")
    print(f"  ✓ Scenario 2: Merchant Dispute - Item Not Delivered")
    print(f"  ✓ Scenario 3: ATM Dispute - Cash Not Dispensed")
    print(f"  ✓ Scenario 4: Duplicate Transaction")
    print(f"  ✓ Scenario 5: Incorrect Amount - Overcharged")
    print(f"  ✓ Scenario 6: Subscription Dispute (Netflix)")
    print(f"  ✓ Scenario 7: Loan/EMI Dispute")
    print(f"  ✓ Scenario 8: Refund Not Received")
    print(f"  ✓ Scenario 9: Quality/Service Dispute")
    print(f"  ✓ Scenario 10: Chargeback Scenario")
    print(f"  ✓ High-Risk Merchant: 15 historic disputes for ShopXYZ Online")
    
    print(f"\n💡 Quick Test Transaction IDs:")
    
    # Get specific transaction IDs for easy testing
    fraud_intl = db.query(models.Transaction).filter(
        models.Transaction.merchant_name == "Harrods Department Store"
    ).first()
    
    amazon = db.query(models.Transaction).filter(
        models.Transaction.merchant_name == "Amazon India"
    ).first()
    
    atm_fault = db.query(models.Transaction).join(models.ATM_Log).filter(
        models.ATM_Log.status_code == "DISPENSE_FAULT"
    ).first()
    
    duplicate = db.query(models.Transaction).filter(
        models.Transaction.merchant_name == "Taj Restaurant"
    ).first()
    
    netflix = db.query(models.Transaction).filter(
        models.Transaction.merchant_name == "Netflix"
    ).order_by(models.Transaction.id.desc()).first()
    
    emi = db.query(models.Transaction).filter(
        models.Transaction.merchant_name == "Loan EMI Payment"
    ).first()
    
    shopxyz = db.query(models.Transaction).filter(
        models.Transaction.merchant_name == "ShopXYZ Online"
    ).order_by(models.Transaction.id.desc()).first()
    
    print(f"  • Fraudulent (International): Transaction ID {fraud_intl.id if fraud_intl else 'N/A'}")
    print(f"  • Merchant Dispute (Amazon): Transaction ID {amazon.id if amazon else 'N/A'}")
    print(f"  • ATM Fault: Transaction ID {atm_fault.id if atm_fault else 'N/A'}")
    print(f"  • Duplicate: Transaction ID {duplicate.id if duplicate else 'N/A'}")
    print(f"  • Subscription (Netflix): Transaction ID {netflix.id if netflix else 'N/A'}")
    print(f"  • EMI Overcharge: Transaction ID {emi.id if emi else 'N/A'}")
    print(f"  • High-Risk Merchant (ShopXYZ): Transaction ID {shopxyz.id if shopxyz else 'N/A'}")
    
    print("\n" + "="*70)
    print("✅ Database seeding completed successfully!")
    print("="*70)
    print("\n💡 Next Steps:")
    print("  1. Start your cluster: start_cluster.bat")
    print("  2. Open AGENT_TESTING_GUIDE.md")
    print("  3. Test each scenario using the transaction IDs above")
    print("  4. Create disputes via UI (http://localhost:3000) or API")
    print("\n📝 Customer Login Information:")
    print("  • All customers can log in using their customer ID")
    print("  • Customer IDs: 1-6")
    print("  • Use customer ID for authentication in the UI")
    print("="*70 + "\n")


def main():
    """Main function to seed the database."""
    print("\n" + "="*70)
    print("BANKING DISPUTE MANAGEMENT - DATABASE SEEDER")
    print("Streamlined Test Data: 6 Customers + All 10 Scenarios")
    print("="*70)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_database(db)
        
        # Create data in order
        customers = create_customers(db)
        loan_accounts = create_loan_accounts(db, customers)
        common_transactions = create_common_transactions(db, customers)
        test_transactions = create_test_scenario_transactions(db, customers)
        high_risk_merchant_trans = create_high_risk_merchant_history(db, customers)
        
        # Print summary
        print_summary(db)
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

# Made with Bob
