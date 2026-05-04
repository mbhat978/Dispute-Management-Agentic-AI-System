"""
Automated Scheduler for Data Retention and GDPR Compliance

This module provides automated scheduling for:
1. Daily data retention cleanup
2. Weekly compliance reports
3. Monthly audit log archival
4. Automated anonymization of expired data

Can be run as:
- Standalone script (cron job)
- Background task in FastAPI
- Scheduled task in production
"""

import schedule
import time
from datetime import datetime
from loguru import logger
from typing import Optional

try:
    from .database import SessionLocal
    from .data_retention import (
        cleanup_expired_data,
        generate_retention_compliance_report
    )
except ImportError:
    from database import SessionLocal
    from data_retention import (
        cleanup_expired_data,
        generate_retention_compliance_report
    )


# ============================================================================
# SCHEDULER CONFIGURATION
# ============================================================================

class SchedulerConfig:
    """Configuration for automated tasks"""
    
    # Schedule times (24-hour format)
    DAILY_CLEANUP_TIME: str = "02:00"  # 2 AM daily
    WEEKLY_REPORT_DAY: str = "monday"  # Weekly report day
    WEEKLY_REPORT_TIME: str = "09:00"  # 9 AM
    
    # Cleanup settings
    DRY_RUN_MODE: bool = False  # Set to True for testing
    SEND_EMAIL_NOTIFICATIONS: bool = False  # Email notifications (requires SMTP setup)
    
    # Logging
    LOG_FILE: str = "compliance_scheduler.log"


# ============================================================================
# SCHEDULED TASKS
# ============================================================================

def daily_data_cleanup():
    """
    Daily task: Clean up expired data
    
    Runs at 2 AM daily to:
    - Anonymize expired transactions
    - Anonymize expired disputes
    - Clean up expired audit logs
    """
    logger.info("=" * 70)
    logger.info("SCHEDULED TASK: Daily Data Cleanup")
    logger.info("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Run cleanup
        results = cleanup_expired_data(
            db,
            dry_run=SchedulerConfig.DRY_RUN_MODE
        )
        
        logger.info("Cleanup Results:")
        logger.info(f"  - Transactions anonymized: {results['transactions_anonymized']}")
        logger.info(f"  - Disputes anonymized: {results['disputes_anonymized']}")
        logger.info(f"  - Audit logs deleted: {results['audit_logs_deleted']}")
        logger.info(f"  - Customers anonymized: {results['customers_anonymized']}")
        
        # Send notification if configured
        if SchedulerConfig.SEND_EMAIL_NOTIFICATIONS:
            send_cleanup_notification(results)
        
        logger.info("Daily cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during daily cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def weekly_compliance_report():
    """
    Weekly task: Generate compliance report
    
    Runs every Monday at 9 AM to:
    - Generate retention compliance report
    - Check for expired data
    - Provide recommendations
    """
    logger.info("=" * 70)
    logger.info("SCHEDULED TASK: Weekly Compliance Report")
    logger.info("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Generate report
        report = generate_retention_compliance_report(db)
        
        logger.info("Compliance Report:")
        logger.info(f"  Report Date: {report['report_date']}")
        logger.info(f"  Total Transactions: {report['data_summary']['total_transactions']}")
        logger.info(f"  Total Disputes: {report['data_summary']['total_disputes']}")
        logger.info(f"  Total Customers: {report['data_summary']['total_customers']}")
        logger.info(f"  Expired Transactions: {report['expired_data']['transactions']}")
        logger.info(f"  Expired Disputes: {report['expired_data']['disputes']}")
        logger.info(f"  Expired Audit Logs: {report['expired_data']['audit_logs']}")
        
        if report['recommendations']:
            logger.info("Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"  - {rec}")
        
        # Send report if configured
        if SchedulerConfig.SEND_EMAIL_NOTIFICATIONS:
            send_compliance_report_email(report)
        
        logger.info("Weekly compliance report generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def monthly_audit_archival():
    """
    Monthly task: Archive old audit logs
    
    Runs on the 1st of each month to:
    - Archive audit logs older than retention period
    - Generate archival report
    """
    logger.info("=" * 70)
    logger.info("SCHEDULED TASK: Monthly Audit Log Archival")
    logger.info("=" * 70)
    
    db = SessionLocal()
    
    try:
        try:
            from .data_retention import find_expired_audit_logs
        except ImportError:
            from data_retention import find_expired_audit_logs
        
        expired_logs = find_expired_audit_logs(db)
        
        logger.info(f"Found {len(expired_logs)} audit logs to archive")
        
        # In production, you would:
        # 1. Export logs to archive storage (S3, etc.)
        # 2. Delete from active database
        # 3. Update archival index
        
        logger.info("Monthly audit archival completed")
        
    except Exception as e:
        logger.error(f"Error during audit archival: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ============================================================================
# NOTIFICATION FUNCTIONS
# ============================================================================

def send_cleanup_notification(results: dict):
    """Send email notification about cleanup results"""
    # Placeholder for email notification
    # In production, integrate with your email service
    logger.info("Email notification would be sent here")
    logger.info(f"Cleanup results: {results}")


def send_compliance_report_email(report: dict):
    """Send compliance report via email"""
    # Placeholder for email notification
    # In production, integrate with your email service
    logger.info("Compliance report email would be sent here")
    logger.info(f"Report summary: {report['data_summary']}")


# ============================================================================
# SCHEDULER SETUP
# ============================================================================

def setup_scheduler():
    """
    Set up all scheduled tasks
    
    Tasks:
    - Daily cleanup at 2 AM
    - Weekly report on Monday at 9 AM
    - Monthly archival on 1st of month
    """
    logger.info("Setting up compliance scheduler...")
    
    # Daily cleanup
    schedule.every().day.at(SchedulerConfig.DAILY_CLEANUP_TIME).do(daily_data_cleanup)
    logger.info(f"✓ Scheduled daily cleanup at {SchedulerConfig.DAILY_CLEANUP_TIME}")
    
    # Weekly report
    getattr(schedule.every(), SchedulerConfig.WEEKLY_REPORT_DAY).at(
        SchedulerConfig.WEEKLY_REPORT_TIME
    ).do(weekly_compliance_report)
    logger.info(f"✓ Scheduled weekly report on {SchedulerConfig.WEEKLY_REPORT_DAY} at {SchedulerConfig.WEEKLY_REPORT_TIME}")
    
    # Monthly archival (1st of month at 3 AM)
    schedule.every().day.at("03:00").do(check_and_run_monthly_archival)
    logger.info("✓ Scheduled monthly archival on 1st of month at 03:00")
    
    logger.info("Scheduler setup complete")


def check_and_run_monthly_archival():
    """Check if today is 1st of month and run archival"""
    if datetime.now().day == 1:
        monthly_audit_archival()


def run_scheduler():
    """
    Run the scheduler continuously
    
    This function runs indefinitely and executes scheduled tasks
    """
    logger.info("=" * 70)
    logger.info("COMPLIANCE SCHEDULER STARTED")
    logger.info("=" * 70)
    logger.info(f"Mode: {'DRY RUN' if SchedulerConfig.DRY_RUN_MODE else 'PRODUCTION'}")
    logger.info(f"Email Notifications: {'Enabled' if SchedulerConfig.SEND_EMAIL_NOTIFICATIONS else 'Disabled'}")
    logger.info("=" * 70)
    
    setup_scheduler()
    
    logger.info("\nScheduler is running. Press Ctrl+C to stop.")
    logger.info("Next scheduled tasks:")
    for job in schedule.get_jobs():
        logger.info(f"  - {job}")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")


# ============================================================================
# MANUAL EXECUTION
# ============================================================================

def run_manual_cleanup():
    """Run cleanup manually (for testing or immediate execution)"""
    logger.info("Running manual cleanup...")
    daily_data_cleanup()


def run_manual_report():
    """Generate report manually (for testing or immediate execution)"""
    logger.info("Generating manual report...")
    weekly_compliance_report()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Retention & GDPR Compliance Scheduler")
    parser.add_argument(
        "--mode",
        choices=["scheduler", "cleanup", "report"],
        default="scheduler",
        help="Run mode: scheduler (continuous), cleanup (one-time), report (one-time)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual changes)"
    )
    
    args = parser.parse_args()
    
    # Set dry-run mode
    if args.dry_run:
        SchedulerConfig.DRY_RUN_MODE = True
        logger.info("Running in DRY RUN mode - no changes will be made")
    
    # Execute based on mode
    if args.mode == "scheduler":
        run_scheduler()
    elif args.mode == "cleanup":
        run_manual_cleanup()
    elif args.mode == "report":
        run_manual_report()


if __name__ == "__main__":
    main()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
USAGE:

1. Run continuous scheduler:
   python backend/compliance_scheduler.py --mode scheduler

2. Run one-time cleanup:
   python backend/compliance_scheduler.py --mode cleanup

3. Generate one-time report:
   python backend/compliance_scheduler.py --mode report

4. Dry run (test without making changes):
   python backend/compliance_scheduler.py --mode cleanup --dry-run

5. Set up as Windows Task Scheduler:
   - Open Task Scheduler
   - Create Basic Task
   - Trigger: Daily at 2:00 AM
   - Action: Start a program
   - Program: python
   - Arguments: backend/compliance_scheduler.py --mode cleanup
   - Start in: C:/path/to/your/project

6. Set up as Linux cron job:
   # Edit crontab
   crontab -e
   
   # Add daily cleanup at 2 AM
   0 2 * * * cd /path/to/project && python backend/compliance_scheduler.py --mode cleanup
   
   # Add weekly report on Monday at 9 AM
   0 9 * * 1 cd /path/to/project && python backend/compliance_scheduler.py --mode report

7. Run in Docker:
   docker run -d --name compliance-scheduler \
     -v $(pwd):/app \
     python:3.11 \
     python /app/backend/compliance_scheduler.py --mode scheduler
"""

# Made with Bob - Compliance Scheduler