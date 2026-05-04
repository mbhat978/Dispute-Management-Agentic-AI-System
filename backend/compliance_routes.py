"""
Compliance API Routes for Data Retention and GDPR

Provides endpoints for:
- Data retention management
- GDPR Right to be Forgotten
- GDPR Right to Data Portability
- Compliance reporting
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

try:
    from .database import get_db
    from .data_retention import (
        cleanup_expired_data,
        process_gdpr_deletion_request,
        export_customer_data,
        generate_retention_compliance_report,
        check_legal_holds,
        count_customer_data,
        RetentionPolicy,
        find_expired_transactions,
        find_expired_disputes,
        find_expired_audit_logs
    )
    from .models import Customer
except ImportError:
    from database import get_db
    from data_retention import (
        cleanup_expired_data,
        process_gdpr_deletion_request,
        export_customer_data,
        generate_retention_compliance_report,
        check_legal_holds,
        count_customer_data,
        RetentionPolicy,
        find_expired_transactions,
        find_expired_disputes,
        find_expired_audit_logs
    )
    from models import Customer

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GDPRDeletionRequest(BaseModel):
    """GDPR deletion request model"""
    customer_id: int
    reason: str = "Customer request - Right to be Forgotten"
    confirmation: bool  # Customer must confirm deletion


class GDPRDeletionResponse(BaseModel):
    """GDPR deletion response model"""
    request_id: str
    customer_id: int
    status: str
    message: str
    can_delete: bool
    legal_holds: list
    data_to_delete: Optional[Dict[str, int]] = None
    estimated_completion: Optional[str] = None


class DataExportRequest(BaseModel):
    """Data export request model"""
    customer_id: int
    email: EmailStr
    format: str = "json"  # json, csv, pdf


class RetentionPolicyResponse(BaseModel):
    """Retention policy information"""
    transaction_retention_days: int
    dispute_retention_days: int
    audit_log_retention_days: int
    customer_inactive_days: int
    anonymize_after_retention: bool


class CleanupRequest(BaseModel):
    """Data cleanup request"""
    dry_run: bool = True
    notify_admin: bool = True


# ============================================================================
# GDPR ENDPOINTS
# ============================================================================

@router.post("/gdpr/deletion-request", response_model=GDPRDeletionResponse)
async def request_data_deletion(
    request: GDPRDeletionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process GDPR Right to be Forgotten request
    
    This endpoint:
    1. Validates the customer exists
    2. Checks for legal holds
    3. Initiates data deletion process
    4. Returns status and timeline
    
    **Important:** This is a destructive operation and cannot be undone.
    """
    logger.info(f"GDPR deletion request received for customer {request.customer_id}")
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if confirmation is provided
    if not request.confirmation:
        raise HTTPException(
            status_code=400,
            detail="Deletion confirmation required. Set 'confirmation: true' to proceed."
        )
    
    # Check for legal holds
    legal_holds = check_legal_holds(db, request.customer_id)
    
    if legal_holds:
        return GDPRDeletionResponse(
            request_id=f"GDPR_{request.customer_id}_{int(datetime.utcnow().timestamp())}",
            customer_id=request.customer_id,
            status="blocked",
            message="Cannot delete data due to legal holds",
            can_delete=False,
            legal_holds=legal_holds
        )
    
    # Count data to be deleted
    data_count = count_customer_data(db, request.customer_id)
    
    # Process deletion in background
    background_tasks.add_task(
        process_gdpr_deletion_request,
        db=db,
        customer_id=request.customer_id,
        reason=request.reason,
        dry_run=False
    )
    
    return GDPRDeletionResponse(
        request_id=f"GDPR_{request.customer_id}_{int(datetime.utcnow().timestamp())}",
        customer_id=request.customer_id,
        status="processing",
        message="Data deletion request accepted and is being processed",
        can_delete=True,
        legal_holds=[],
        data_to_delete=data_count,
        estimated_completion=(datetime.utcnow()).isoformat()
    )


@router.get("/gdpr/deletion-eligibility/{customer_id}")
async def check_deletion_eligibility(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if customer data can be deleted (GDPR eligibility check)
    
    Returns:
    - Whether deletion is allowed
    - Any legal holds preventing deletion
    - Amount of data that would be deleted
    """
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check legal holds
    legal_holds = check_legal_holds(db, customer_id)
    
    # Count data
    data_count = count_customer_data(db, customer_id)
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "can_delete": len(legal_holds) == 0,
        "legal_holds": legal_holds,
        "data_summary": data_count,
        "estimated_deletion_time": "Immediate (< 1 minute)" if len(legal_holds) == 0 else "N/A"
    }


@router.post("/gdpr/data-export")
async def export_customer_data_endpoint(
    request: DataExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export customer data (GDPR Right to Data Portability)
    
    Returns all customer data in machine-readable format:
    - Personal information
    - Transaction history
    - Dispute history
    - Account details
    """
    logger.info(f"Data export requested for customer {request.customer_id}")
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify email matches
    if customer.email != request.email:
        raise HTTPException(
            status_code=403,
            detail="Email does not match customer record"
        )
    
    # Export data
    export_data = export_customer_data(db, request.customer_id)
    
    if "error" in export_data:
        raise HTTPException(status_code=500, detail=export_data["error"])
    
    return {
        "status": "success",
        "format": request.format,
        "data": export_data,
        "download_url": f"/api/compliance/gdpr/download/{request.customer_id}",
        "expires_at": (datetime.utcnow()).isoformat()
    }


# ============================================================================
# DATA RETENTION ENDPOINTS
# ============================================================================

@router.get("/retention/policy", response_model=RetentionPolicyResponse)
async def get_retention_policy():
    """
    Get current data retention policy
    
    Returns the configured retention periods for different data types
    """
    return RetentionPolicyResponse(
        transaction_retention_days=RetentionPolicy.TRANSACTION_RETENTION_DAYS,
        dispute_retention_days=RetentionPolicy.DISPUTE_RETENTION_DAYS,
        audit_log_retention_days=RetentionPolicy.AUDIT_LOG_RETENTION_DAYS,
        customer_inactive_days=RetentionPolicy.CUSTOMER_INACTIVE_DAYS,
        anonymize_after_retention=RetentionPolicy.ANONYMIZE_AFTER_RETENTION
    )


@router.post("/retention/cleanup")
async def run_data_cleanup(
    request: CleanupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run data retention cleanup
    
    This endpoint:
    1. Identifies expired data
    2. Anonymizes or deletes data per retention policy
    3. Generates cleanup report
    
    **dry_run=true**: Only reports what would be cleaned up
    **dry_run=false**: Actually performs cleanup
    """
    logger.info(f"Data cleanup initiated (dry_run={request.dry_run})")
    
    # Run cleanup
    results = cleanup_expired_data(db, dry_run=request.dry_run)
    
    return {
        "status": "completed" if not request.dry_run else "dry_run",
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
        "message": "Cleanup completed successfully" if not request.dry_run else "Dry run completed - no changes made"
    }


@router.get("/retention/report")
async def get_retention_report(db: Session = Depends(get_db)):
    """
    Generate data retention compliance report
    
    Returns:
    - Current retention policy
    - Data summary (total records)
    - Expired data counts
    - Recommendations for cleanup
    """
    report = generate_retention_compliance_report(db)
    return report


@router.get("/retention/expired-data")
async def get_expired_data_summary(db: Session = Depends(get_db)):
    """
    Get summary of expired data that should be cleaned up
    """
    from backend.data_retention import (
        find_expired_transactions,
        find_expired_disputes,
        find_expired_audit_logs
    )
    
    expired_transactions = find_expired_transactions(db)
    expired_disputes = find_expired_disputes(db)
    expired_logs = find_expired_audit_logs(db)
    
    return {
        "summary": {
            "expired_transactions": len(expired_transactions),
            "expired_disputes": len(expired_disputes),
            "expired_audit_logs": len(expired_logs)
        },
        "oldest_transaction": expired_transactions[0].transaction_date.isoformat() if expired_transactions else None,
        "oldest_dispute": expired_disputes[0].created_at.isoformat() if expired_disputes else None,
        "recommendation": "Run cleanup to anonymize expired data" if (expired_transactions or expired_disputes) else "No cleanup needed"
    }


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.get("/admin/compliance-dashboard")
async def get_compliance_dashboard(db: Session = Depends(get_db)):
    """
    Get compliance dashboard with key metrics
    
    For admin/compliance officer use
    """
    # Get counts
    total_customers = db.query(Customer).count()
    expired_transactions = len(find_expired_transactions(db))
    expired_disputes = len(find_expired_disputes(db))
    expired_logs = len(find_expired_audit_logs(db))
    
    # Calculate compliance score
    total_expired = expired_transactions + expired_disputes + expired_logs
    compliance_score = 100 if total_expired == 0 else max(0, 100 - (total_expired / 10))
    
    return {
        "compliance_score": round(compliance_score, 2),
        "status": "compliant" if compliance_score >= 90 else "needs_attention",
        "metrics": {
            "total_customers": total_customers,
            "expired_data": {
                "transactions": expired_transactions,
                "disputes": expired_disputes,
                "audit_logs": expired_logs,
                "total": total_expired
            }
        },
        "retention_policy": {
            "transaction_retention": f"{RetentionPolicy.TRANSACTION_RETENTION_DAYS} days (7 years)",
            "dispute_retention": f"{RetentionPolicy.DISPUTE_RETENTION_DAYS} days (7 years)",
            "audit_log_retention": f"{RetentionPolicy.AUDIT_LOG_RETENTION_DAYS} days (7 years)"
        },
        "recommendations": [
            "Run data cleanup to anonymize expired records" if total_expired > 0 else "System is compliant",
            "Review GDPR deletion requests regularly",
            "Maintain audit trail of all deletions"
        ],
        "last_updated": datetime.utcnow().isoformat()
    }


# Made with Bob - Compliance API Routes