import atexit
import logging
import multiprocessing
import os
import sys
import time

from PyQt5.QtCore import QCoreApplication, QStandardPaths
from watchdog.observers import Observer

from src.automation.scheduler import logging_config as logging_module, scheduler_manager as scheduler_module
from src.automation.scheduler.job_handler import JSONFileChangeHandler
from src.automation.scheduler.logging_config import setup_temporary_logging
from src.automation.scheduler.scheduler_manager import SchedulerManager

# Module-level logger
logger = logging.getLogger(__name__)
_initial_stderr_handler = logging.StreamHandler(sys.stderr)
_initial_stderr_handler.setFormatter(logging.Formatter("EARLY_LOG: %(levelname)s - %(message)s"))

# Global path variables
APP_DATA_DIR = None
TEMP_DIR = None
SCHEDULED_JOBS_FILE_PATH = None
ATTACHMENTS_BASE_DIR_PATH = None


def configure_daemon_paths():
    """Configure paths needed specifically for the daemon run."""
    global APP_DATA_DIR, TEMP_DIR, SCHEDULED_JOBS_FILE_PATH, ATTACHMENTS_BASE_DIR_PATH
    if not QCoreApplication.instance():
        raise RuntimeError("Daemon needs QCoreApplication for paths.")
    APP_DATA_DIR = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    TEMP_DIR = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    SCHEDULED_JOBS_FILE_PATH = os.path.join(APP_DATA_DIR, "scheduled_jobs.json")
    ATTACHMENTS_BASE_DIR_PATH = os.path.join(APP_DATA_DIR, "scheduled_attachments")
    logging_module.TEMP_DIR = TEMP_DIR
    scheduler_module.DEFAULT_JOBS_FILE = SCHEDULED_JOBS_FILE_PATH
    scheduler_module.ATTACHMENTS_BASE_DIR = ATTACHMENTS_BASE_DIR_PATH
    logger.info("Daemon paths configured:")
    logger.info(f"  logging_module.TEMP_DIR = {logging_module.TEMP_DIR}")
    logger.info(f"  scheduler_module.DEFAULT_JOBS_FILE = {scheduler_module.DEFAULT_JOBS_FILE}")
    logger.info(f"  scheduler_module.ATTACHMENTS_BASE_DIR = {scheduler_module.ATTACHMENTS_BASE_DIR}")


def run_daemon():
    """
    Run the daemon with watchdog. Assumes that paths are configured.
    """
    logger.info("run_daemon() started")
    manager = None
    observer = None
    try:
        logger.info("Configuring daemon paths...")
        configure_daemon_paths()
        logger.info("Setting up temporary logging...")
        setup_temporary_logging()
        logger.info("Temporary logging setup finished.")
        logger.info("Initializing SchedulerManager...")
        manager = SchedulerManager(start_scheduler=True)
        logger.info("SchedulerManager initialized and scheduler started.")
        logger.info("Setting up Watchdog observer...")
        event_handler = JSONFileChangeHandler(manager)
        observer = Observer()
        watch_dir = os.path.dirname(os.path.abspath(manager.jobs_file))
        logger.info(f"Determined watch directory: {watch_dir}")
        if not os.path.exists(watch_dir):
            logger.error(f"Watch directory {watch_dir} does not exist. Exiting run_daemon.")
            return
        observer.schedule(event_handler, path=watch_dir, recursive=False)
        logger.info("Starting observer...")
        observer.start()
        logger.info("Observer started. Entering main keep-alive loop.")
        while True:
            if not observer.is_alive():
                logger.warning("Watchdog observer thread is no longer alive. Exiting main loop.")
                break
            if not manager.scheduler.running:
                logger.warning("APScheduler is no longer running. Exiting main loop.")
                break
            logger.debug("Daemon keep-alive loop sleeping...")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt detected in run_daemon.")
    except Exception as e_run:
        logger.error(f"CRITICAL ERROR in run_daemon: {e_run}", exc_info=True)
    finally:
        logger.info("run_daemon finishing. Stopping components...")
        if observer and observer.is_alive():
            try:
                observer.stop()
                logger.info("Observer stop requested.")
                observer.join(timeout=5)
                if observer.is_alive():
                    logger.warning("Observer thread did not join cleanly.")
                else:
                    logger.info("Observer stopped.")
            except Exception as e_obs:
                logger.error(f"Error stopping observer: {e_obs}", exc_info=True)
        if manager and manager.scheduler.running:
            try:
                manager.shutdown()
                logger.info("Scheduler shutdown.")
            except Exception as shutdown_err:
                logger.error(f"Error during scheduler shutdown: {shutdown_err}", exc_info=True)
        logger.info("Daemon components stop sequence complete.")
        print("--- run_daemon() finished ---", flush=True)


# Global variables for logging and lock file
output_log_path = None
LOCK_FILE_PATH = None


def log_message(msg):
    """Log a message to stdout and append it to the output log file if available."""
    print(msg, flush=True)
    if output_log_path:
        try:
            with open(output_log_path, "a") as f:
                f.write(f"{msg}\n")
        except Exception as e_log:
            print(f"!!! Failed to write to log file {output_log_path}: {e_log}", flush=True, file=sys.stderr)


def _daemon_cleanup_lock_file():
    """Cleanup the daemon lock file."""
    if LOCK_FILE_PATH and os.path.exists(LOCK_FILE_PATH):
        try:
            os.remove(LOCK_FILE_PATH)
            log_message("Daemon cleaned up lock file.")
        except Exception as e:
            log_message(f"Daemon error cleaning lock file: {e}")


if __name__ == "__main__":
    try:
        home_dir = os.path.expanduser("~")
        temp_log_dir = os.path.join(home_dir, ".automate_daemon_logs")
        os.makedirs(temp_log_dir, exist_ok=True)
        output_log_path = os.path.join(temp_log_dir, "daemon_startup.log")
        with open(output_log_path, "w") as f:
            f.write(f"--- Daemon __main__ started at {time.time()} ---\n")
    except Exception as e_log_init:
        print(f"!!! Initial logging setup failed: {e_log_init}", flush=True, file=sys.stderr)

    log_message("--- Starting daemon directly (__main__ block) ---")

    try:
        multiprocessing.freeze_support()
        log_message("--- freeze_support() called ---")
    except Exception as e_freeze:
        log_message(f"!!! EXCEPTION during freeze_support(): {e_freeze}")
        sys.exit(1)

    log_message("--- Daemon __main__ attempting QCoreApplication init ---")
    try:
        daemon_app_instance = QCoreApplication(sys.argv if hasattr(sys, 'argv') else [''])
        log_message("--- Daemon __main__ QCoreApplication created ---")

        ORGANIZATION_NAME = "AutoMate"
        APPLICATION_NAME = "AutoMate"
        QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
        QCoreApplication.setApplicationName(APPLICATION_NAME)
        log_message(f"--- Daemon __main__ set Org/App Name: {ORGANIZATION_NAME}/{APPLICATION_NAME} ---")

        temp_dir_for_lock = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        if not temp_dir_for_lock:
            log_message("!!! CRITICAL: Cannot determine TempLocation.")
            sys.exit(1)
        LOCK_FILE_PATH = os.path.join(temp_dir_for_lock, "automate_daemon.lock")
        log_message(f"--- Daemon __main__ Lock File Path: {LOCK_FILE_PATH} ---")

        log_message("--- Daemon __main__ checking for existing lock file ---")
        if os.path.exists(LOCK_FILE_PATH):
            log_message("Daemon lock file exists. Another instance might be running. Exiting.")
            sys.exit(1)
        log_message("--- Daemon __main__ lock file does not exist. Proceeding. ---")

        log_message("--- Daemon __main__ attempting to create lock file ---")
        with open(LOCK_FILE_PATH, "w") as f:
            f.write(str(os.getpid()))
        log_message(f"Daemon created lock file: {LOCK_FILE_PATH}")
        atexit.register(_daemon_cleanup_lock_file)
        log_message("--- Daemon __main__ registered lock file cleanup ---")

        log_message("--- Daemon __main__ calling run_daemon() ---")
        run_daemon()
        log_message("--- Daemon __main__ run_daemon() returned ---")

    except Exception as e_main:
        log_message(f"!!! DAEMON MAIN BLOCK EXCEPTION: {e_main}")
        import traceback

        if output_log_path:
            with open(output_log_path, "a") as f:
                traceback.print_exc(file=f)
        traceback.print_exc()
        _daemon_cleanup_lock_file()
        sys.exit(1)

    log_message("--- Daemon __main__ finished successfully ---")
    sys.exit(0)
