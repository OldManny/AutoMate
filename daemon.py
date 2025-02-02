import logging
import os
import time

from watchdog.observers import Observer

from src.automation.scheduler.job_handler import JSONFileChangeHandler
from src.automation.scheduler.logging_config import setup_temporary_logging
from src.automation.scheduler.scheduler_manager import SchedulerManager

# Create a logger object
logger = logging.getLogger(__name__)


def run_daemon():
    """
    Run the daemon with watchdog to detect changes in scheduled_jobs.json.
    Logs go to a temporary file, deleted on normal exit or interrupt.
    """
    # Set up temporary logging
    setup_temporary_logging()

    logger.info("Starting daemon process.")
    manager = SchedulerManager()

    # Set up watchdog event handler
    event_handler = JSONFileChangeHandler(manager)
    observer = Observer()
    watch_dir = os.path.dirname(os.path.abspath(manager.jobs_file))

    logger.info(f"Watching directory: {watch_dir} for changes in scheduled_jobs.json")
    observer.schedule(event_handler, path=watch_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt detected. Shutting down gracefully.")
        print("\nShutting down daemon...")
        manager.shutdown()
        observer.stop()

        # Explicitly remove the temporary log file
        for handler in logging.getLogger().handlers[:]:
            if isinstance(handler, logging.FileHandler):
                try:
                    log_filename = handler.baseFilename
                    handler.close()
                    os.remove(log_filename)
                    logger.info(f"Temporary log file {log_filename} deleted.")
                except Exception as e:
                    logger.error(f"Failed to delete temporary log file: {e}")
    except Exception as e:
        logger.error(f"Daemon error: {e}")
        manager.shutdown()
        observer.stop()

    observer.join()
    logger.info("Daemon has stopped.")


if __name__ == "__main__":
    run_daemon()
