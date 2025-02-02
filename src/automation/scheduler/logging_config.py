import atexit
import logging
import os
import time


def setup_temporary_logging():
    """
    Sets up logging to a temporary file.
    That file is removed when the daemon ends.
    """

    timestamp_str = str(int(time.time()))
    log_filename = f"daemon_temp_{timestamp_str}.log"

    # Create a file handler
    file_handler = logging.FileHandler(log_filename, mode='w')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    file_handler.setFormatter(file_format)

    # Remove existing handlers
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # Attach the file handler to the root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Register a function to remove the log file on exit
    def remove_logfile():
        if os.path.exists(log_filename):
            os.remove(log_filename)

    atexit.register(remove_logfile)

    # Log an initial message
    root_logger.info(f"Temporary logging active. Writing logs to {log_filename}.")
