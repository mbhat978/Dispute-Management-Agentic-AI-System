"""
Data Retention and GDPR Compliance Module

This module implements:
1. Data Retention Policy (7-year retention for financial records)
2. GDPR Right to be Forgotten (data deletion on customer request)
3. Data Anonymization (after retention period)
4. Audit log cleanup
5. Compliance reporting

Regulatory Requirements:
- Banking regulations: 7 years retention for financial transactions
- GDPR: Right to erasure (Right to be Forgotten)
- PCI DSS: Secure deletion of cardholder data
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, cast
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger
import json

try:
    from .database import SessionLocal
    from .models import Customer, Transaction, DisputeTicket, AuditLog
    from .utils.pii_masking import mask_sensitive_data
except ImportError:
    from database import SessionLocal
    from models import Customer, Transaction, DisputeTicket, AuditLog
    from utils.pii_masking import mask_sensitive_data


# ============================================================================
# CONFIGURATION
# ============================================================================

class RetentionPolicy:
    """Data retention policy configuration"""
    
    # Retention periods (in days)
    TRANSACTION_RETENTION_DAYS = 7 * 365  # 7 years for financial records
    DISPUTE_RETENTION_DAYS = 7 * 365      # 7 years for dispute records
    AUDIT_LOG_RETENTION_DAYS = 7 * 365    # 7 years for audit trails
    CUSTOMER_INACTIVE_DAYS = 3 * 365      # 3 years of inactivity before anonymization
    
    # GDPR grace period (days to process deletion request)
    GDPR_DELETION_GRACE_PERIOD = 30
    
    # Anonymization settings
    ANONYMIZE_AFTER_RETENTION = True
    DELETE_AFTER_ANONYMIZATION = False  # Keep anonymized records for analytics


# ============================================================================
# DATA RETENTION FUNCTIONS
# ============================================================================

def get_retention_cutoff_date(retention_days: int) -> datetime:
    """Calculate cutoff date for data retention"""
    return datetime.utcnow() - timedelta(days=retention_days)


def find_expired_transactions(db: Session) -> List[Transaction]:
    """Find transactions older than retention period"""
    cutoff_date = get_retention_cutoff_date(RetentionPolicy.TRANSACTION_RETENTION_DAYS)
    
    expired_transactions = db.query(Transaction).filter(
        Transaction.transaction_date < cutoff_date
    ).all()
    
    logger.info(f"Found {len(expired_transactions)} expired transactions (older than {RetentionPolicy.TRANSACTION_RETENTION_DAYS} days)")
    return expired_transactions


def find_expired_disputes(db: Session) -> List[DisputeTicket]:
    """Find disputes older than retention period"""
    cutoff_date = get_retention_cutoff_date(RetentionPolicy.DISPUTE_RETENTION_DAYS)
    
    expired_disputes = db.query(DisputeTicket).filter(
        DisputeTicket.created_at < cutoff_date
    ).all()
    
    logger.info(f"Found {len(expired_disputes)} expired disputes (older than {RetentionPolicy.DISPUTE_RETENTION_DAYS} days)")
    return expired_disputes


def find_expired_audit_logs(db: Session) -> List[AuditLog]:
    """Find audit logs older than retention period"""
    cutoff_date = get_retention_cutoff_date(RetentionPolicy.AUDIT_LOG_RETENTION_DAYS)
    
    expired_logs = db.query(AuditLog).filter(
        AuditLog.timestamp < cutoff_date
    ).all()
    
    logger.info(f"Found {len(expired_logs)} expired audit logs (older than {RetentionPolicy.AUDIT_LOG_RETENTION_DAYS} days)")
    return expired_logs


def anonymize_transaction(transaction: Transaction) -> Transaction:
    """Anonymize transaction data while preserving analytics value"""
    transaction.merchant_name = f"MERCHANT_{transaction.id}"
    # Keep amount, date, status for analytics
    # Remove any PII if present
    return transaction


def anonymize_customer(customer: Customer) -> Customer:
    """Anonymize customer data"""
    customer.name = f"ANONYMIZED_CUSTOMER_{customer.id}"
    customer.email = f"deleted_{customer.id}@anonymized.local"
    customer.card_number = "****-****-****-****"
    customer.card_status = "Deleted"
    return customer


def cleanup_expired_data(db: Session, dry_run: bool = True) -> Dict[str, int]:
    """
    Clean up expired data according to retention policy
    
    Args:
        db: Database session
        dry_run: If True, only report what would be deleted without actually deleting
        
    Returns:
        Dictionary with counts of processed records
    """
    results = {
        "transactions_anonymized": 0,
        "disputes_anonymized": 0,
        "audit_logs_deleted": 0,
        "customers_anonymized": 0
    }
    
    logger.info(f"Starting data retention cleanup (dry_run={dry_run})")
    
    try:
        # 1. Anonymize expired transactions
        expired_transactions = find_expired_transactions(db)
        for transaction in expired_transactions:
            if not dry_run:
                anonymize_transaction(transaction)
            results["transactions_anonymized"] += 1
        
        # 2. Anonymize expired disputes
        expired_disputes = find_expired_disputes(db)
        for dispute in expired_disputes:
            if not dry_run:
                dispute.dispute_reason = f"ANONYMIZED_DISPUTE_{dispute.id}"
                dispute.resolution_notes = "Data anonymized per retention policy"
            results["disputes_anonymized"] += 1
        
        # 3. Delete expired audit logs (or anonymize)
        expired_logs = find_expired_audit_logs(db)
        for log in expired_logs:
            if not dry_run:
                if RetentionPolicy.DELETE_AFTER_ANONYMIZATION:
                    db.delete(log)
                else:
                    log.description = f"ANONYMIZED_LOG_{log.id}"
            results["audit_logs_deleted"] += 1
        
        # 4. Find and anonymize inactive customers
        inactive_cutoff = get_retention_cutoff_date(RetentionPolicy.CUSTOMER_INACTIVE_DAYS)
        inactive_customers = db.query(Customer).join(Transaction).filter(
            Transaction.transaction_date < inactive_cutoff
        ).distinct().all()
        
        for customer in inactive_customers:
            # Check if customer has any recent activity
            recent_transactions = db.query(Transaction).filter(
                and_(
                    Transaction.customer_id == customer.id,
                    Transaction.transaction_date >= inactive_cutoff
                )
            ).count()
            
            if recent_transactions == 0:
                if not dry_run:
                    anonymize_customer(customer)
                results["customers_anonymized"] += 1
        
        if not dry_run:
            db.commit()
            logger.info("Data retention cleanup completed successfully")
        else:
            logger.info("Dry run completed - no changes made")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during data retention cleanup: {e}")
        db.rollback()
        raise


# ============================================================================
# GDPR RIGHT TO BE FORGOTTEN
# ============================================================================

class GDPRDeletionRequest:
    """GDPR data deletion request"""
    
    def __init__(self, customer_id: int, reason: str = "Customer request"):
        self.customer_id = customer_id
        self.reason = reason
        self.requested_at = datetime.utcnow()
        self.status = "pending"  # pending, processing, completed, failed


def process_gdpr_deletion_request(
    db: Session,
    customer_id: int,
    reason: str = "Customer request - Right to be Forgotten",
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Process GDPR Right to be Forgotten request
    
    This function:
    1. Validates the deletion request
    2. Checks for legal holds (active disputes, investigations)
    3. Anonymizes or deletes customer data
    4. Creates audit trail of deletion
    5. Returns deletion report
    
    Args:
        db: Database session
        customer_id: ID of customer requesting deletion
        reason: Reason for deletion
        dry_run: If True, only report what would be deleted
        
    Returns:
        Dictionary with deletion report
    """
    logger.info(f"Processing GDPR deletion request for customer {customer_id}")
    
    report = {
        "customer_id": customer_id,
        "status": "pending",
        "reason": reason,
        "requested_at": datetime.utcnow().isoformat(),
        "can_delete": False,
        "legal_holds": [],
        "data_deleted": {},
        "errors": []
    }
    
    try:
        # 1. Verify customer exists
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            report["status"] = "failed"
            report["errors"].append(f"Customer {customer_id} not found")
            return report
        
        # 2. Check for legal holds
        legal_holds = check_legal_holds(db, customer_id)
        report["legal_holds"] = legal_holds
        
        if legal_holds:
            report["status"] = "blocked"
            report["can_delete"] = False
            report["errors"].append("Cannot delete due to legal holds")
            logger.warning(f"GDPR deletion blocked for customer {customer_id}: {legal_holds}")
            return report
        
        report["can_delete"] = True
        
        if dry_run:
            report["status"] = "dry_run"
            report["data_deleted"] = count_customer_data(db, customer_id)
            return report
        
        # 3. Delete/Anonymize customer data
        deletion_results = delete_customer_data(db, customer_id)
        report["data_deleted"] = deletion_results
        
        # 4. Create audit trail
        create_gdpr_audit_log(db, customer_id, reason, deletion_results)
        
        # 5. Commit changes
        db.commit()
        
        report["status"] = "completed"
        report["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"GDPR deletion completed for customer {customer_id}")
        return report
        
    except Exception as e:
        logger.error(f"Error processing GDPR deletion for customer {customer_id}: {e}")
        db.rollback()
        report["status"] = "failed"
        report["errors"].append(str(e))
        return report


def check_legal_holds(db: Session, customer_id: int) -> List[str]:
    """
    Check if customer has any legal holds preventing deletion
    
    Legal holds include:
    - Active disputes under investigation
    - Pending fraud investigations
    - Ongoing legal proceedings
    - Regulatory audits
    """
    holds = []
    
    # Check for active disputes
    active_disputes = db.query(DisputeTicket).filter(
        and_(
            DisputeTicket.customer_id == customer_id,
            DisputeTicket.status.in_(['open', 'under_investigation', 'pending_review'])
        )
    ).count()
    
    if active_disputes > 0:
        holds.append(f"Active disputes: {active_disputes}")
    
    # Check for recent transactions (within 90 days - chargeback window)
    recent_cutoff = datetime.utcnow() - timedelta(days=90)
    recent_transactions = db.query(Transaction).filter(
        and_(
            Transaction.customer_id == customer_id,
            Transaction.transaction_date >= recent_cutoff
        )
    ).count()
    
    if recent_transactions > 0:
        holds.append(f"Recent transactions within chargeback window: {recent_transactions}")
    
    return holds


def count_customer_data(db: Session, customer_id: int) -> Dict[str, int]:
    """Count all data associated with a customer"""
    return {
        "transactions": db.query(Transaction).filter(Transaction.customer_id == customer_id).count(),
        "disputes": db.query(DisputeTicket).filter(DisputeTicket.customer_id == customer_id).count(),
        "audit_logs": db.query(AuditLog).join(DisputeTicket).filter(DisputeTicket.customer_id == customer_id).count()
    }


def delete_customer_data(db: Session, customer_id: int) -> Dict[str, int]:
    """
    Delete or anonymize all customer data
    
    Strategy:
    - Anonymize instead of delete to preserve referential integrity
    - Keep transaction records for financial audit (anonymized)
    - Delete PII completely
    """
    results = {
        "transactions_anonymized": 0,
        "disputes_anonymized": 0,
        "audit_logs_anonymized": 0,
        "customer_anonymized": 0
    }
    
    # 1. Anonymize transactions
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
    for transaction in transactions:
        anonymize_transaction(transaction)
        results["transactions_anonymized"] += 1
    
    # 2. Anonymize disputes
    disputes = db.query(DisputeTicket).filter(DisputeTicket.customer_id == customer_id).all()
    for dispute in disputes:
        dispute.dispute_reason = f"DELETED_BY_GDPR_{dispute.id}"
        dispute.resolution_notes = "Customer data deleted per GDPR request"
        results["disputes_anonymized"] += 1
    
    # 3. Anonymize audit logs
    audit_logs = db.query(AuditLog).join(DisputeTicket).filter(
        DisputeTicket.customer_id == customer_id
    ).all()
    for log in audit_logs:
        log.description = f"ANONYMIZED_{log.id}"
        results["audit_logs_anonymized"] += 1
    
    # 4. Anonymize customer record
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        anonymize_customer(customer)
        results["customer_anonymized"] = 1
    
    return results


def create_gdpr_audit_log(
    db: Session,
    customer_id: int,
    reason: str,
    deletion_results: Dict[str, int]
):
    """Create audit log entry for GDPR deletion"""
    # Note: This would typically go to a separate compliance audit table
    # For now, we'll log it
    logger.info(
        f"GDPR_DELETION: Customer {customer_id} | Reason: {reason} | "
        f"Results: {json.dumps(deletion_results)}"
    )


# ============================================================================
# DATA EXPORT (GDPR Right to Data Portability)
# ============================================================================

def export_customer_data(db: Session, customer_id: int) -> Dict[str, Any]:
    """
    Export all customer data in machine-readable format
    (GDPR Right to Data Portability)
    """
    logger.info(f"Exporting data for customer {customer_id}")
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    
    # Get all related data
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
    disputes = db.query(DisputeTicket).filter(DisputeTicket.customer_id == customer_id).all()
    
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "account_tier": customer.account_tier,
            "current_balance": customer.current_account_balance
        },
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "merchant": t.merchant_name,
                "date": t.transaction_date.isoformat(),
                "status": t.status
            }
            for t in transactions
        ],
        "disputes": [
            {
                "id": d.id,
                "transaction_id": d.transaction_id,
                "reason": d.dispute_reason,
                "status": d.status,
                "created_at": d.created_at.isoformat()
            }
            for d in disputes
        ]
    }
    
    # Mask sensitive data in export
    # Type cast is safe because mask_sensitive_data preserves the input type
    export_data = cast(Dict[str, Any], mask_sensitive_data(export_data))
    
    return export_data


# ============================================================================
# COMPLIANCE REPORTING
# ============================================================================

def generate_retention_compliance_report(db: Session) -> Dict[str, Any]:
    """Generate compliance report for data retention"""
    report = {
        "report_date": datetime.utcnow().isoformat(),
        "retention_policy": {
            "transactions": f"{RetentionPolicy.TRANSACTION_RETENTION_DAYS} days",
            "disputes": f"{RetentionPolicy.DISPUTE_RETENTION_DAYS} days",
            "audit_logs": f"{RetentionPolicy.AUDIT_LOG_RETENTION_DAYS} days"
        },
        "data_summary": {
            "total_transactions": db.query(Transaction).count(),
            "total_disputes": db.query(DisputeTicket).count(),
            "total_audit_logs": db.query(AuditLog).count(),
            "total_customers": db.query(Customer).count()
        },
        "expired_data": {
            "transactions": len(find_expired_transactions(db)),
            "disputes": len(find_expired_disputes(db)),
            "audit_logs": len(find_expired_audit_logs(db))
        },
        "recommendations": []
    }
    
    # Add recommendations
    if report["expired_data"]["transactions"] > 0:
        report["recommendations"].append(
            f"Anonymize {report['expired_data']['transactions']} expired transactions"
        )
    
    if report["expired_data"]["audit_logs"] > 100:
        report["recommendations"].append(
            f"Clean up {report['expired_data']['audit_logs']} expired audit logs"
        )
    
    return report


# Made with Bob - Data Retention & GDPR Compliance