"""
Seed script to populate the SQLite database with realistic mock data.
This script creates customers, transactions, ATM logs, and dispute tickets
covering all 10 test scenarios from AGENT_TESTING_GUIDE.md.
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
    """Create dummy customers with different profiles for testing."""
    print("\n📋 Creating customers...")
    
    customers = [
        # ========================================================================
        # ORIGINAL CUSTOMERS (from initial seed_data.py)
        # ========================================================================
        # Customer 1: Premium tier - John Smith
        models.Customer(
            name="John Smith",
            account_tier="Premium",
            current_account_balance=15000.00,
            card_number="**** **** **** 4921",
            card_status="Active"
        ),
        # Customer 2: Gold tier - Sarah Johnson
        models.Customer(
            name="Sarah Johnson",
            account_tier="Gold",
            current_account_balance=50000.00,
            card_number="**** **** **** 8832",
            card_status="Active"
        ),
        # Customer 3: Basic tier - Michael Chen
        models.Customer(
            name="Michael Chen",
            account_tier="Basic",
            current_account_balance=3500.00,
            card_number="**** **** **** 1194",
            card_status="Active"
        ),
        # Customer 4: Premium tier - Emily Rodriguez
        models.Customer(
            name="Emily Rodriguez",
            account_tier="Premium",
            current_account_balance=22000.00,
            card_number="**** **** **** 7543",
            card_status="Active"
        ),
        # Customer 5: Basic tier - David Kumar
        models.Customer(
            name="David Kumar",
            account_tier="Basic",
            current_account_balance=5000.00,
            card_number="**** **** **** 0092",
            card_status="Active"
        ),
        
        # ========================================================================
        # NEW TEST SCENARIO CUSTOMERS (Indian names for comprehensive testing)
        # ========================================================================
        # Customer 6: Premium tier, frequent traveler
        models.Customer(
            name="Priya Sharma",
            account_tier="Premium",
            current_account_balance=12500.00,
            card_number="**** **** **** 9876",
            card_status="Active"
        ),
        # Customer 7: Gold tier, online shopper
        models.Customer(
            name="Rahul Verma",
            account_tier="Gold",
            current_account_balance=8500.00,
            card_number="**** **** **** 5432",
            card_status="Active"
        ),
        # Customer 8: Basic tier, student
        models.Customer(
            name="Ananya Patel",
            account_tier="Basic",
            current_account_balance=1500.00,
            card_number="**** **** **** 3210",
            card_status="Active"
        ),
        # Customer 9: Premium tier, business owner
        models.Customer(
            name="Vikram Singh",
            account_tier="Premium",
            current_account_balance=25000.00,
            card_number="**** **** **** 6789",
            card_status="Active"
        ),
        # Customer 10: Gold tier, subscription user
        models.Customer(
            name="Meera Reddy",
            account_tier="Gold",
            current_account_balance=6500.00,
            card_number="**** **** **** 1357",
            card_status="Active"
        ),
        # Customer 11: Basic tier, first-time user
        models.Customer(
            name="Arjun Kumar",
            account_tier="Basic",
            current_account_balance=800.00,
            card_number="**** **** **** 2468",
            card_status="Active"
        ),
        # Customer 12: Gold tier, frequent diner
        models.Customer(
            name="Sneha Iyer",
            account_tier="Gold",
            current_account_balance=9500.00,
            card_number="**** **** **** 3579",
            card_status="Active"
        ),
        # Customer 13: Premium tier, tech enthusiast
        models.Customer(
            name="Karthik Menon",
            account_tier="Premium",
            current_account_balance=18000.00,
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
    """Create mock loan accounts for loan dispute scenarios."""
    print("\n💰 Creating loan accounts...")
    
    loan_accounts = [
        models.LoanAccount(
            customer_id=customers[0].id,  # John Smith
            monthly_emi_amount=500.00,
            total_outstanding=15000.00
        ),
        models.LoanAccount(
            customer_id=customers[1].id,  # Sarah Johnson
            monthly_emi_amount=850.00,
            total_outstanding=28000.00
        ),
        models.LoanAccount(
            customer_id=customers[5].id,  # Priya Sharma
            monthly_emi_amount=1200.00,
            total_outstanding=35000.00
        ),
        models.LoanAccount(
            customer_id=customers[8].id,  # Vikram Singh
            monthly_emi_amount=2500.00,
            total_outstanding=85000.00
        ),
        models.LoanAccount(
            customer_id=customers[12].id,  # Karthik Menon
            monthly_emi_amount=850.00,
            total_outstanding=18000.00
        )
    ]
    
    db.add_all(loan_accounts)
    db.commit()
    
    for loan in loan_accounts:
        db.refresh(loan)
        customer = db.query(models.Customer).filter(models.Customer.id == loan.customer_id).first()
        print(f"  ✓ Loan ID: {loan.id} - {customer.name if customer else 'Unknown'}, EMI: ${loan.monthly_emi_amount:,.2f}, Outstanding: ${loan.total_outstanding:,.2f}")
    
    return loan_accounts


def create_test_scenario_transactions(db: Session, customers):
    """Create transactions for all 10 test scenarios from AGENT_TESTING_GUIDE.md."""
    print("\n🎯 Creating test scenario transactions...")
    
    base_time = datetime.utcnow() - timedelta(days=30)
    transactions = []
    
    # ========================================================================
    # SCENARIO 1: FRAUDULENT TRANSACTION (Auto-Decision)
    # ========================================================================
    print("\n  📍 Scenario 1: Fraudulent Transaction - International")
    
    # 1.1: High-value international transaction (London)
    trans1 = models.Transaction(
        customer_id=customers[5].id,  # Priya Sharma (Customer 6)
        amount=250.00,
        merchant_name="Harrods Department Store",
        transaction_date=base_time + timedelta(days=1, hours=14),
        status="success",
        is_international=True,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans1)
    db.commit()
    db.refresh(trans1)
    transactions.append(trans1)
    print(f"    ✓ ID {trans1.id}: ${trans1.amount:,.2f} to {trans1.merchant_name} (London, UK)")
    
    # 1.2: Velocity fraud - Multiple transactions in 30 minutes
    velocity_time = base_time + timedelta(days=2, hours=10)
    velocity_merchants = [
        ("Delhi Electronics", "Delhi"),
        ("Mumbai Fashion Store", "Mumbai"),
        ("Bangalore Tech Hub", "Bangalore"),
        ("Chennai Jewelers", "Chennai"),
        ("Kolkata Boutique", "Kolkata")
    ]
    
    print("\n  📍 Scenario 1.2: Velocity Fraud - 5 transactions in 30 minutes")
    for i, (merchant, location) in enumerate(velocity_merchants):
        trans = models.Transaction(
            customer_id=customers[6].id,  # Rahul Verma (Customer 7)
            amount=90.00,
            merchant_name=merchant,
            transaction_date=velocity_time + timedelta(minutes=i*6),
            status="success",
            is_international=False,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans)
        db.commit()
        db.refresh(trans)
        transactions.append(trans)
        print(f"    ✓ ID {trans.id}: ${trans.amount:,.2f} to {merchant} ({location})")
    
    # ========================================================================
    # SCENARIO 2: MERCHANT DISPUTE - ITEM NOT DELIVERED (Human-in-Loop)
    # ========================================================================
    print("\n  📍 Scenario 2: Merchant Dispute - Item Not Delivered")
    
    # 2.1: Amazon order not delivered
    trans_amazon = models.Transaction(
        customer_id=customers[7].id,  # Ananya Patel (Customer 8)
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
    print(f"    ✓ ID {trans_amazon.id}: ${trans_amazon.amount:,.2f} to {trans_amazon.merchant_name} (iPhone 15 Pro)")
    
    # 2.2: High-risk merchant - empty box received
    trans_shady = models.Transaction(
        customer_id=customers[8].id,  # Vikram Singh (Customer 9)
        amount=150.00,
        merchant_name="ShopXYZ Online",
        transaction_date=base_time + timedelta(days=6, hours=15),
        status="success",
        is_international=False,
        refunded_amount=0.0,
        transaction_type="debit"
    )
    db.add(trans_shady)
    db.commit()
    db.refresh(trans_shady)
    transactions.append(trans_shady)
    print(f"    ✓ ID {trans_shady.id}: ${trans_shady.amount:,.2f} to {trans_shady.merchant_name} (Laptop - Empty Box)")
    
    # ========================================================================
    # SCENARIO 3: ATM DISPUTE - CASH NOT DISPENSED
    # ========================================================================
    print("\n  📍 Scenario 3: ATM Dispute - Cash Not Dispensed")
    
    # 3.1: ATM hardware fault
    trans_atm_fault = models.Transaction(
        customer_id=customers[9].id,  # Meera Reddy (Customer 10)
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
    
    # 3.2: ATM success (for comparison)
    trans_atm_success = models.Transaction(
        customer_id=customers[9].id,  # Meera Reddy (Customer 10)
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
        status_code="SUCCESS"
    )
    db.add(atm_log_success)
    db.commit()
    print(f"    ✓ ID {trans_atm_success.id}: ${trans_atm_success.amount:,.2f} ATM Withdrawal (SUCCESS)")
    
    # ========================================================================
    # SCENARIO 4: DUPLICATE TRANSACTION
    # ========================================================================
    print("\n  📍 Scenario 4: Duplicate Transaction")
    
    duplicate_time = base_time + timedelta(days=10, hours=19, minutes=30)
    
    trans_dup1 = models.Transaction(
        customer_id=customers[11].id,  # Sneha Iyer (Customer 12)
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
        customer_id=customers[11].id,  # Sneha Iyer (Customer 12)
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
    # SCENARIO 5: INCORRECT AMOUNT - OVERCHARGED
    # ========================================================================
    print("\n  📍 Scenario 5: Incorrect Amount - Overcharged")
    
    trans_overcharge = models.Transaction(
        customer_id=customers[12].id,  # Karthik Menon (Customer 13)
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
    # SCENARIO 6: SUBSCRIPTION DISPUTE - UNAUTHORIZED RECURRING CHARGE
    # ========================================================================
    print("\n  📍 Scenario 6: Subscription Dispute")
    
    # 6.1: Netflix - Cancelled but still charged
    subscription_start = base_time + timedelta(days=1)
    
    # Create 12 months of Netflix charges (to establish subscription pattern)
    for month in range(12):
        trans_netflix = models.Transaction(
            customer_id=customers[9].id,  # Meera Reddy (Customer 10)
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
        customer_id=customers[9].id,  # Meera Reddy (Customer 10)
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
    
    # 6.2: Spotify - Active subscription (no cancellation)
    for month in range(12):
        trans_spotify = models.Transaction(
            customer_id=customers[10].id,  # Arjun Kumar (Customer 11)
            amount=10.99,
            merchant_name="Spotify",
            transaction_date=subscription_start + timedelta(days=30*month),
            status="success",
            is_international=False,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans_spotify)
        db.commit()
        db.refresh(trans_spotify)
        transactions.append(trans_spotify)
    
    print(f"    ✓ Created 12 Spotify charges for customer {customers[10].name} (Active subscription)")
    
    # ========================================================================
    # SCENARIO 7: LOAN/EMI DISPUTE
    # ========================================================================
    print("\n  📍 Scenario 7: Loan/EMI Dispute - Incorrect Amount")
    
    trans_emi_wrong = models.Transaction(
        customer_id=customers[5].id,  # Priya Sharma (Customer 6, has loan with EMI ₹12,000)
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
    # SCENARIO 8: REFUND NOT RECEIVED
    # ========================================================================
    print("\n  📍 Scenario 8: Refund Not Received")
    
    # 8.1: Merchant refund delayed >7 days
    trans_refund_delayed = models.Transaction(
        customer_id=customers[7].id,  # Ananya Patel (Customer 8)
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
    # SCENARIO 9: QUALITY/SERVICE DISPUTE
    # ========================================================================
    print("\n  📍 Scenario 9: Quality/Service Dispute")
    
    trans_quality = models.Transaction(
        customer_id=customers[8].id,  # Vikram Singh (Customer 9)
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
    # SCENARIO 10: CHARGEBACK SCENARIO
    # ========================================================================
    print("\n  📍 Scenario 10: Chargeback - Merchant Non-Response")
    
    trans_chargeback = models.Transaction(
        customer_id=customers[6].id,  # Rahul Verma (Customer 7)
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
    
    # ========================================================================
    # HIGH-RISK MERCHANT SETUP: Create dispute history for ShopXYZ Online
    # ========================================================================
    print("\n  📍 Creating High-Risk Merchant History: ShopXYZ Online")
    
    # Create 20 past transactions with ShopXYZ Online (high-risk merchant)
    # These will be used to establish a pattern of disputes
    shopxyz_customers = [customers[0], customers[1], customers[2], customers[3], customers[4]]
    shopxyz_transaction_ids = []
    
    for i in range(20):
        trans_shopxyz_hist = models.Transaction(
            customer_id=shopxyz_customers[i % 5].id,
            amount=100.00 + (i * 10),
            merchant_name="ShopXYZ Online",
            transaction_date=base_time - timedelta(days=150 - (i * 5)),  # Spread over 150 days
            status="success",
            is_international=False,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans_shopxyz_hist)
        db.commit()
        db.refresh(trans_shopxyz_hist)
        shopxyz_transaction_ids.append(trans_shopxyz_hist.id)
        transactions.append(trans_shopxyz_hist)
    
    # Create 15 dispute tickets for ShopXYZ Online (75% approval rate = high-risk)
    # 13 approved, 2 denied = 65% approval rate
    approved_count = 0
    denied_count = 0
    
    for i in range(15):
        # Determine status: first 13 are approved, last 2 are denied
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
            customer_id=shopxyz_customers[i % 5].id,
            dispute_category="merchant_dispute",
            dispute_reason=f"ShopXYZ dispute #{i+1}: Item not received or empty box",
            status=ticket_status,
            final_decision=ticket_decision,
            resolution_notes=f"Historical dispute - {'Approved' if ticket_decision == 'approve' else 'Denied'}",
            created_at=base_time - timedelta(days=140 - (i * 5)),
            updated_at=base_time - timedelta(days=135 - (i * 5))
        )
        db.add(dispute_ticket)
        db.commit()
    
    print(f"    ✓ Created 20 historical transactions for ShopXYZ Online")
    print(f"    ✓ Created 15 dispute tickets: {approved_count} approved, {denied_count} denied")
    print(f"    ✓ Approval rate: {(approved_count/15)*100:.1f}% (HIGH-RISK MERCHANT)")
    
    # ========================================================================
    # ADDITIONAL: Normal transactions for context
    # ========================================================================
    print("\n  📍 Additional: Normal transactions for customer history")
    
    normal_transactions = [
        # Original customers
        (customers[0].id, 299.99, "TechGadgets Online", False),  # John Smith
        (customers[1].id, 8500.00, "Luxury Watches International", False),  # Sarah Johnson
        (customers[2].id, 450.00, "Electronics Store", False),  # Michael Chen
        (customers[3].id, 89.99, "Coffee Shop Downtown", False),  # Emily Rodriguez
        (customers[4].id, 1200.00, "Grocery Store", False),  # David Kumar
        # New test customers
        (customers[5].id, 1200.00, "Swiggy", False),  # Priya Sharma
        (customers[5].id, 850.00, "Uber", False),  # Priya Sharma
        (customers[6].id, 2500.00, "Flipkart", False),  # Rahul Verma
        (customers[7].id, 450.00, "BookMyShow", False),  # Ananya Patel
        (customers[8].id, 5000.00, "Croma", False),  # Vikram Singh
        (customers[9].id, 3200.00, "Zomato", False),  # Meera Reddy
        (customers[10].id, 180.00, "Starbucks", False),  # Arjun Kumar
        (customers[11].id, 1800.00, "Westside", False),  # Sneha Iyer
        (customers[12].id, 12000.00, "Apple Store", False),  # Karthik Menon
    ]
    
    for cust_id, amount, merchant, is_intl in normal_transactions:
        trans = models.Transaction(
            customer_id=cust_id,
            amount=amount,
            merchant_name=merchant,
            transaction_date=base_time + timedelta(days=3, hours=12),
            status="success",
            is_international=is_intl,
            refunded_amount=0.0,
            transaction_type="debit"
        )
        db.add(trans)
        db.commit()
        db.refresh(trans)
        transactions.append(trans)
    
    print(f"    ✓ Created {len(normal_transactions)} normal transactions for customer history")
    
    return transactions


def print_summary(db: Session):
    """Print summary of seeded data with scenario mapping."""
    print("\n" + "="*70)
    print("DATABASE SEEDING SUMMARY")
    print("="*70)
    
    customer_count = db.query(models.Customer).count()
    loan_count = db.query(models.LoanAccount).count()
    transaction_count = db.query(models.Transaction).count()
    atm_log_count = db.query(models.ATM_Log).count()
    
    print(f"\n📊 Total Records Created:")
    print(f"  • Customers: {customer_count}")
    print(f"  • Loan Accounts: {loan_count}")
    print(f"  • Transactions: {transaction_count}")
    print(f"  • ATM Logs: {atm_log_count}")
    
    print(f"\n🎯 Test Scenario Coverage (AGENT_TESTING_GUIDE.md):")
    print(f"  ✓ Scenario 1: Fraudulent Transaction (International + Velocity)")
    print(f"  ✓ Scenario 2: Merchant Dispute - Item Not Delivered")
    print(f"  ✓ Scenario 3: ATM Dispute - Cash Not Dispensed")
    print(f"  ✓ Scenario 4: Duplicate Transaction")
    print(f"  ✓ Scenario 5: Incorrect Amount - Overcharged")
    print(f"  ✓ Scenario 6: Subscription Dispute (Netflix + Spotify)")
    print(f"  ✓ Scenario 7: Loan/EMI Dispute")
    print(f"  ✓ Scenario 8: Refund Not Received")
    print(f"  ✓ Scenario 9: Quality/Service Dispute")
    print(f"  ✓ Scenario 10: Chargeback Scenario")
    
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
    
    print(f"  • Fraudulent (International): Transaction ID {fraud_intl.id if fraud_intl else 'N/A'}")
    print(f"  • Merchant Dispute (Amazon): Transaction ID {amazon.id if amazon else 'N/A'}")
    print(f"  • ATM Fault: Transaction ID {atm_fault.id if atm_fault else 'N/A'}")
    print(f"  • Duplicate: Transaction ID {duplicate.id if duplicate else 'N/A'}")
    print(f"  • Subscription (Netflix): Transaction ID {netflix.id if netflix else 'N/A'}")
    print(f"  • EMI Overcharge: Transaction ID {emi.id if emi else 'N/A'}")
    
    print("\n" + "="*70)
    print("✅ Database seeding completed successfully!")
    print("="*70)
    print("\n💡 Next Steps:")
    print("  1. Start your cluster: start_cluster.bat")
    print("  2. Open AGENT_TESTING_GUIDE.md")
    print("  3. Test each scenario using the transaction IDs above")
    print("  4. Create disputes via UI (http://localhost:3000) or API")
    print("="*70 + "\n")


def main():
    """Main function to seed the database."""
    print("\n" + "="*70)
    print("BANKING DISPUTE MANAGEMENT - DATABASE SEEDER")
    print("Comprehensive Test Data for All 10 Scenarios")
    print("="*70)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_database(db)
        
        # Create data in order
        customers = create_customers(db)
        loan_accounts = create_loan_accounts(db, customers)
        transactions = create_test_scenario_transactions(db, customers)
        
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
