import atexit
import logging
import os
import sys
import time

# This module sets up temporary logging for the daemon process
TEMP_DIR = None


def setup_temporary_logging():
    """
    Sets up logging to a temporary file.
    That file is removed when the daemon ends.
    """
    if not TEMP_DIR:
        print("ERROR: TEMP_DIR path not set for temporary logging.", file=sys.stderr)
        log_filename = None
    else:
        timestamp_str = str(int(time.time()))
        log_filename = os.path.join(TEMP_DIR, f"automate_daemon_temp_{timestamp_str}.log")
        print(f"Daemon logging to: {log_filename}")

    # Create a file handler
    file_handler = None  # Initialize to None
    if log_filename:  # Only create if path is valid
        try:
            file_handler = logging.FileHandler(log_filename, mode='w')
            file_handler.setLevel(logging.INFO)
            file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
            file_handler.setFormatter(file_format)
        except Exception as e:
            print(f"ERROR: Failed to create log file handler for {log_filename}: {e}", file=sys.stderr)
            file_handler = None  # Ensure it's None if creation

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

    def remove_logfile():
        """Remove the temporary log file on exit."""
        if log_filename:  # Only try to remove if we had a filename
            try:
                if os.path.exists(log_filename):
                    if file_handler:  # Close handler before removing
                        file_handler.close()
                    os.remove(log_filename)
                    print(f"Temporary log file {log_filename} deleted.")
            except Exception as e:
                print(f"Error removing log file {log_filename}: {e}", file=sys.stderr)

        atexit.register(remove_logfile)

        # Log an initial message
        if log_filename:
            root_logger.info(f"Temporary logging active. Writing logs to {log_filename}.")
        else:
            root_logger.info("Temporary logging to file disabled due to path error.")
