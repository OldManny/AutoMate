import glob
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

# This module sets up temporary logging for the daemon process
TEMP_DIR = None

# Global configuration
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # Keep 3 backup files
LOG_FILENAME = "automate_daemon.log"  # Fixed filename


def cleanup_old_temp_logs():
    """Clean up old temporary log files that match the pattern."""
    if not TEMP_DIR:
        return

    try:
        # Find all temporary log files with the old naming pattern
        old_logs = glob.glob(os.path.join(TEMP_DIR, "automate_daemon_temp_*.log"))
        for old_log in old_logs:
            try:
                os.remove(old_log)
                print(f"Cleaned up old log file: {old_log}")
            except OSError as e:
                print(f"Failed to clean up old log file {old_log}: {e}")
    except Exception as e:
        print(f"Error during cleanup of old logs: {e}")


def setup_temporary_logging():
    """
    Sets up logging with a rotating file handler to manage log size.
    """
    if not TEMP_DIR:
        print("ERROR: TEMP_DIR path not set for temporary logging.", file=sys.stderr)
        log_filename = None
    else:
        # Clean up old temporary log files
        cleanup_old_temp_logs()

        # Use a fixed filename instead of timestamp
        log_filename = os.path.join(TEMP_DIR, LOG_FILENAME)
        print(f"Daemon logging to: {log_filename}")

    # Create a rotating file handler
    file_handler = None
    if log_filename:
        try:
            file_handler = RotatingFileHandler(
                log_filename,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                mode='a',  # Append mode to keep logs across restarts
            )
            file_handler.setLevel(logging.INFO)
            file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
            file_handler.setFormatter(file_format)
        except Exception as e:
            print(f"ERROR: Failed to create log file handler for {log_filename}: {e}", file=sys.stderr)
            file_handler = None

    # Remove existing handlers
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # Attach the file handler to the root logger
    root_logger.setLevel(logging.INFO)
    if file_handler:
        root_logger.addHandler(file_handler)
    else:
        # Optionally add a StreamHandler to see logs on console if file logging failed
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_format = logging.Formatter("TEMP_LOG_FALLBACK: %(asctime)s [%(levelname)s] %(name)s - %(message)s")
        stream_handler.setFormatter(stream_format)
        root_logger.addHandler(stream_handler)
        root_logger.warning("File logging failed, using console fallback.")

    # Log an initial message
    if log_filename:
        root_logger.info(f"Temporary logging active. Writing logs to {log_filename}.")
    else:
        root_logger.info("Temporary logging to file disabled due to path error.")

    return log_filename
