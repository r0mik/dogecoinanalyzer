"""Scheduler for running data collection at regular intervals."""

import signal
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database.models import init_db, ScriptStatus, get_db_session
from collector.data_fetcher import DataFetcher
from config.settings import COLLECTION_INTERVAL_MINUTES
from utils.logger import setup_logger

logger = setup_logger('scheduler')

# Global scheduler instance
scheduler = BlockingScheduler()
data_fetcher = DataFetcher()


def collect_data():
    """Wrapper function for data collection."""
    try:
        logger.info("=" * 60)
        logger.info(f"Starting scheduled data collection at {datetime.utcnow()}")
        logger.info("=" * 60)
        
        # Update status to running
        update_status('running', 'Data collection in progress...')
        
        # Fetch and store data
        success = data_fetcher.fetch_and_store()
        
        if success:
            logger.info("Data collection completed successfully")
        else:
            logger.error("Data collection completed with errors")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in data collection: {e}", exc_info=True)
        update_status('error', f"Error: {str(e)}")


def update_status(status: str, message: str = None):
    """
    Update script status in database.
    
    Args:
        status: Status string ('running', 'success', 'error')
        message: Optional status message
    """
    db = get_db_session()
    try:
        script_status = db.query(ScriptStatus).filter(
            ScriptStatus.script_name == 'collector'
        ).first()
        
        if not script_status:
            script_status = ScriptStatus(script_name='collector')
            db.add(script_status)
        
        script_status.last_run = datetime.utcnow()
        script_status.status = status
        script_status.message = message
        
        # Calculate next run time
        next_run = datetime.utcnow() + timedelta(minutes=COLLECTION_INTERVAL_MINUTES)
        script_status.next_run = next_run
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to update script status: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    scheduler.shutdown()
    update_status('error', 'Service stopped')
    sys.exit(0)


def main():
    """Main entry point for the collector scheduler."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized")
        
        # Initialize script status
        update_status('running', 'Service starting...')
        
        # Run initial collection immediately
        logger.info("Running initial data collection...")
        collect_data()
        
        # Schedule periodic collection
        trigger = IntervalTrigger(minutes=COLLECTION_INTERVAL_MINUTES)
        scheduler.add_job(
            collect_data,
            trigger=trigger,
            id='collect_dogecoin_data',
            name='Collect Dogecoin Market Data',
            replace_existing=True
        )
        
        logger.info(f"Scheduler started. Collecting data every {COLLECTION_INTERVAL_MINUTES} minutes")
        logger.info("Press Ctrl+C to stop")
        
        # Start scheduler (this will block)
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        scheduler.shutdown()
        update_status('error', 'Service stopped by user')
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}", exc_info=True)
        update_status('error', f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

