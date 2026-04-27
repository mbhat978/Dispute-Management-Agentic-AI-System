"""
Dispute Fraud Detection for Banking Dispute Management System

This module detects fraudulent dispute patterns to prevent "friendly fraud"
where customers file illegitimate disputes to get free refunds.
"""

from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta
from loguru import logger

try:
    from ..database import SessionLocal
    from ..models import DisputeTicket, Transaction
except ImportError:
    from database import SessionLocal
    from models import DisputeTicket, Transaction


def detect_dispute_fraud(customer_id: int) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Detect fraudulent dispute patterns for a customer
    
    Red flags:
    - Multiple disputes in short time period
    - High dispute rate (disputes on most transactions)
    - Pattern of winning disputes then making large purchases
    - Disputes on all recent transactions
    - Repeated disputes on same merchant
    
    Args:
        customer_id: Customer ID to check
        
    Returns:
        Tuple of (is_suspicious, reason, details)
    """
    db = SessionLocal()
    try:
        logger.info(
            "[DISPUTE FRAUD DETECTOR] Analyzing customer dispute patterns",
            customer_id=customer_id
        )
        
        # Get customer's dispute history (last 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        recent_disputes = db.query(DisputeTicket).filter(
            DisputeTicket.customer_id == customer_id,
            DisputeTicket.created_at > ninety_days_ago
        ).all()
        
        # Get customer's transaction history (last 90 days)
        recent_transactions = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_date > ninety_days_ago
        ).all()
        
        if not recent_transactions:
            return False, "", {}
        
        # Calculate metrics
        dispute_count = len(recent_disputes)
        transaction_count = len(recent_transactions)
        dispute_rate = dispute_count / max(transaction_count, 1)
        
        # Check 1: Too many disputes in short time
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        disputes_last_30_days = len([
            d for d in recent_disputes
            if d.created_at and d.created_at > thirty_days_ago  # type: ignore
        ])
        
        if disputes_last_30_days > 5:
            reason = f"SUSPICIOUS: {disputes_last_30_days} disputes filed in last 30 days"
            details = {
                "pattern": "high_frequency",
                "disputes_30_days": disputes_last_30_days,
                "threshold": 5,
                "severity": "high"
            }
            logger.warning(
                "[DISPUTE FRAUD DETECTOR] High frequency pattern detected",
                customer_id=customer_id,
                disputes_30_days=disputes_last_30_days
            )
            return True, reason, details
        
        # Check 2: High dispute rate (>50% of transactions)
        if dispute_rate > 0.5 and dispute_count >= 3:
            reason = f"SUSPICIOUS: {dispute_rate*100:.0f}% dispute rate ({dispute_count}/{transaction_count} transactions)"
            details = {
                "pattern": "high_dispute_rate",
                "dispute_rate": dispute_rate,
                "dispute_count": dispute_count,
                "transaction_count": transaction_count,
                "threshold": 0.5,
                "severity": "high"
            }
            logger.warning(
                "[DISPUTE FRAUD DETECTOR] High dispute rate detected",
                customer_id=customer_id,
                dispute_rate=f"{dispute_rate*100:.0f}%"
            )
            return True, reason, details
        
        # Check 3: Disputes on all recent transactions
        if transaction_count >= 5 and dispute_count == transaction_count:
            reason = f"SUSPICIOUS: Customer disputed ALL {transaction_count} recent transactions"
            details = {
                "pattern": "disputes_all_transactions",
                "dispute_count": dispute_count,
                "transaction_count": transaction_count,
                "severity": "critical"
            }
            logger.warning(
                "[DISPUTE FRAUD DETECTOR] All transactions disputed",
                customer_id=customer_id
            )
            return True, reason, details
        
        # Check 4: Pattern of approved disputes followed by large purchases
        approved_disputes = [
            d for d in recent_disputes
            if d.status in ["auto_approved", "resolved_approved"]
        ]
        
        if len(approved_disputes) >= 3:
            # Check if customer made large purchases after winning disputes
            approved_dates = [d.created_at for d in approved_disputes if d.created_at]  # type: ignore
            large_purchases_after = []
            
            for trans in recent_transactions:
                if not trans.transaction_date:  # type: ignore
                    continue
                for approved_date in approved_dates:
                    if trans.transaction_date > approved_date:  # type: ignore
                        time_diff = (trans.transaction_date - approved_date).days  # type: ignore
                        if time_diff <= 7 and float(trans.amount) > 1000:  # type: ignore
                            large_purchases_after.append({
                                "amount": float(trans.amount),  # type: ignore
                                "days_after_dispute": time_diff
                            })
            
            if len(large_purchases_after) >= 2:
                reason = f"SUSPICIOUS: Pattern of large purchases after winning disputes"
                details = {
                    "pattern": "win_then_spend",
                    "approved_disputes": len(approved_disputes),
                    "large_purchases_after": large_purchases_after,
                    "severity": "medium"
                }
                logger.warning(
                    "[DISPUTE FRAUD DETECTOR] Win-then-spend pattern detected",
                    customer_id=customer_id
                )
                return True, reason, details
        
        # Check 5: Repeated disputes on same merchant
        merchant_dispute_counts = {}
        for dispute in recent_disputes:
            trans = db.query(Transaction).filter(
                Transaction.id == dispute.transaction_id
            ).first()
            if trans:
                merchant = trans.merchant_name
                merchant_dispute_counts[merchant] = merchant_dispute_counts.get(merchant, 0) + 1
        
        for merchant, count in merchant_dispute_counts.items():
            if count >= 3:
                reason = f"SUSPICIOUS: {count} disputes filed against same merchant '{merchant}'"
                details = {
                    "pattern": "repeated_merchant_disputes",
                    "merchant": merchant,
                    "dispute_count": count,
                    "threshold": 3,
                    "severity": "medium"
                }
                logger.warning(
                    "[DISPUTE FRAUD DETECTOR] Repeated merchant disputes",
                    customer_id=customer_id,
                    merchant=merchant,
                    count=count
                )
                return True, reason, details
        
        # Check 6: Velocity spike (multiple disputes in one day)
        disputes_by_date = {}
        for dispute in recent_disputes:
            date_key = dispute.created_at.date()
            disputes_by_date[date_key] = disputes_by_date.get(date_key, 0) + 1
        
        max_disputes_per_day = max(disputes_by_date.values()) if disputes_by_date else 0
        if max_disputes_per_day >= 3:
            reason = f"SUSPICIOUS: {max_disputes_per_day} disputes filed in a single day"
            details = {
                "pattern": "velocity_spike",
                "max_disputes_per_day": max_disputes_per_day,
                "threshold": 3,
                "severity": "high"
            }
            logger.warning(
                "[DISPUTE FRAUD DETECTOR] Velocity spike detected",
                customer_id=customer_id,
                disputes_per_day=max_disputes_per_day
            )
            return True, reason, details
        
        # No suspicious patterns detected
        logger.info(
            "[DISPUTE FRAUD DETECTOR] No suspicious patterns detected",
            customer_id=customer_id,
            dispute_count=dispute_count,
            dispute_rate=f"{dispute_rate*100:.0f}%"
        )
        return False, "", {
            "dispute_count": dispute_count,
            "transaction_count": transaction_count,
            "dispute_rate": dispute_rate,
            "status": "clean"
        }
        
    except Exception as e:
        logger.exception(
            "[DISPUTE FRAUD DETECTOR] Error during fraud detection",
            customer_id=customer_id,
            error=str(e)
        )
        return False, "", {"error": str(e)}
    finally:
        db.close()


def get_customer_dispute_propensity_score(customer_id: int) -> Dict[str, Any]:
    """
    Calculate a customer's propensity to file disputes (0-100 score)
    
    Higher score = more likely to file disputes
    
    Args:
        customer_id: Customer ID to analyze
        
    Returns:
        Dict with propensity score and contributing factors
    """
    db = SessionLocal()
    try:
        # Get all-time dispute and transaction history
        all_disputes = db.query(DisputeTicket).filter(
            DisputeTicket.customer_id == customer_id
        ).all()
        
        all_transactions = db.query(Transaction).filter(
            Transaction.customer_id == customer_id
        ).all()
        
        if not all_transactions:
            return {
                "propensity_score": 0,
                "risk_level": "unknown",
                "factors": []
            }
        
        score = 0
        factors = []
        
        # Factor 1: Overall dispute rate (40 points max)
        dispute_rate = len(all_disputes) / len(all_transactions)
        if dispute_rate > 0.3:
            score += 40
            factors.append(f"Very high lifetime dispute rate: {dispute_rate*100:.0f}%")
        elif dispute_rate > 0.15:
            score += 25
            factors.append(f"High lifetime dispute rate: {dispute_rate*100:.0f}%")
        elif dispute_rate > 0.05:
            score += 10
            factors.append(f"Moderate lifetime dispute rate: {dispute_rate*100:.0f}%")
        
        # Factor 2: Recent dispute activity (30 points max)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_disputes = [d for d in all_disputes if d.created_at and d.created_at > thirty_days_ago]  # type: ignore
        if len(recent_disputes) > 3:
            score += 30
            factors.append(f"High recent activity: {len(recent_disputes)} disputes in 30 days")
        elif len(recent_disputes) > 1:
            score += 15
            factors.append(f"Moderate recent activity: {len(recent_disputes)} disputes in 30 days")
        
        # Factor 3: Dispute win rate (20 points max)
        approved_disputes = [
            d for d in all_disputes
            if d.status in ["auto_approved", "resolved_approved"]
        ]
        win_rate = len(approved_disputes) / max(len(all_disputes), 1)
        if win_rate > 0.8 and len(all_disputes) >= 3:
            score += 20
            factors.append(f"Very high win rate: {win_rate*100:.0f}%")
        elif win_rate > 0.6 and len(all_disputes) >= 3:
            score += 10
            factors.append(f"High win rate: {win_rate*100:.0f}%")
        
        # Factor 4: Account age vs dispute frequency (10 points max)
        if all_disputes:
            dispute_dates = [d.created_at for d in all_disputes if d.created_at]  # type: ignore
            if dispute_dates:
                first_dispute = min(dispute_dates)  # type: ignore
                account_age_days = (datetime.utcnow() - first_dispute).days  # type: ignore
            else:
                account_age_days = 0
                if account_age_days < 90 and len(all_disputes) >= 3:
                    score += 10
                    factors.append(f"New account with multiple disputes ({len(all_disputes)} in {account_age_days} days)")
        
        # Determine risk level
        if score >= 70:
            risk_level = "very_high"
        elif score >= 50:
            risk_level = "high"
        elif score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "propensity_score": min(score, 100),
            "risk_level": risk_level,
            "factors": factors,
            "lifetime_disputes": len(all_disputes),
            "lifetime_transactions": len(all_transactions),
            "lifetime_dispute_rate": dispute_rate,
            "win_rate": win_rate
        }
        
    except Exception as e:
        logger.exception(
            "[DISPUTE FRAUD DETECTOR] Error calculating propensity score",
            customer_id=customer_id,
            error=str(e)
        )
        return {
            "propensity_score": 0,
            "risk_level": "unknown",
            "factors": [],
            "error": str(e)
        }
    finally:
        db.close()


# Made with Bob - Dispute Fraud Detection