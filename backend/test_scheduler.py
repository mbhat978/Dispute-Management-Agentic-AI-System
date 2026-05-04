"""
Test script for Compliance Scheduler

This script demonstrates how to test the scheduler in different modes:
1. One-time execution mode - Run tasks immediately
2. Test mode - Run with short intervals for testing
3. Production mode - Run with actual schedule (not recommended for testing)
"""

import sys
import argparse
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

try:
    from compliance_scheduler import (
        daily_data_cleanup,
        weekly_compliance_report,
        monthly_audit_archival,
        run_scheduler
    )
    import schedule
except ImportError:
    from backend.compliance_scheduler import (
        daily_data_cleanup,
        weekly_compliance_report,
        monthly_audit_archival,
        run_scheduler
    )
    import schedule


def test_one_time_execution():
    """Test running all tasks once immediately"""
    logger.info("=" * 80)
    logger.info("TEST MODE: One-time Execution")
    logger.info("=" * 80)
    
    logger.info("\n1. Testing Daily Cleanup Task...")
    logger.info("-" * 80)
    daily_data_cleanup()
    
    logger.info("\n2. Testing Weekly Compliance Report...")
    logger.info("-" * 80)
    weekly_compliance_report()
    
    logger.info("\n3. Testing Monthly Audit Archival...")
    logger.info("-" * 80)
    monthly_audit_archival()
    
    logger.success("\n✅ All tasks executed successfully!")
    logger.info("=" * 80)


def test_with_short_intervals():
    """Test scheduler with short intervals (every 30 seconds)"""
    logger.info("=" * 80)
    logger.info("TEST MODE: Short Intervals (30 seconds)")
    logger.info("=" * 80)
    logger.warning("Tasks will run every 30 seconds. Press Ctrl+C to stop.")
    logger.info("=" * 80)
    
    # Clear existing schedule
    schedule.clear()
    
    # Run tasks every 30 seconds
    schedule.every(30).seconds.do(daily_data_cleanup)
    schedule.every(30).seconds.do(weekly_compliance_report)
    schedule.every(30).seconds.do(monthly_audit_archival)
    
    logger.info("Scheduler started with 30-second intervals...")
    logger.info("Waiting for first execution in 30 seconds...")
    
    try:
        import time
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Scheduler stopped by user")


def test_production_schedule():
    """Test with actual production schedule (not recommended for testing)"""
    logger.info("=" * 80)
    logger.info("PRODUCTION MODE: Actual Schedule")
    logger.info("=" * 80)
    logger.warning("⚠️  This will run tasks on production schedule:")
    logger.warning("   - Daily cleanup: 2:00 AM")
    logger.warning("   - Weekly report: Monday 9:00 AM")
    logger.warning("   - Monthly archival: 1st of month")
    logger.warning("\nPress Ctrl+C to stop.")
    logger.info("=" * 80)
    
    run_scheduler()


def show_scheduler_info():
    """Show information about the scheduler"""
    logger.info("=" * 80)
    logger.info("COMPLIANCE SCHEDULER INFORMATION")
    logger.info("=" * 80)
    
    logger.info("\n📋 Scheduled Tasks:")
    logger.info("   1. Daily Cleanup (2:00 AM)")
    logger.info("      - Anonymizes expired data")
    logger.info("      - Removes data beyond retention period")
    logger.info("      - Logs all actions")
    
    logger.info("\n   2. Weekly Compliance Report (Sunday 3:00 AM)")
    logger.info("      - Generates compliance metrics")
    logger.info("      - Identifies expired data")
    logger.info("      - Sends email report (if configured)")
    
    logger.info("\n   3. Monthly Data Archival (1st of month 4:00 AM)")
    logger.info("      - Archives old data")
    logger.info("      - Optimizes database")
    logger.info("      - Generates archival report")
    
    logger.info("\n🔧 Testing Options:")
    logger.info("   --once        : Run all tasks once immediately")
    logger.info("   --test        : Run with 30-second intervals")
    logger.info("   --production  : Run with actual schedule")
    logger.info("   --info        : Show this information")
    
    logger.info("\n📝 Example Usage:")
    logger.info("   python test_scheduler.py --once")
    logger.info("   python test_scheduler.py --test")
    
    logger.info("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Test Compliance Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run all tasks once immediately"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run scheduler with 30-second intervals for testing"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run scheduler with production schedule"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show scheduler information"
    )
    
    args = parser.parse_args()
    
    if args.info:
        show_scheduler_info()
    elif args.once:
        test_one_time_execution()
    elif args.test:
        test_with_short_intervals()
    elif args.production:
        test_production_schedule()
    else:
        # Default: show info
        show_scheduler_info()
        logger.info("\n💡 Tip: Use --once to test all tasks immediately")


if __name__ == "__main__":
    main()

# Made with Bob
