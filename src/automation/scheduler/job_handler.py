import logging

from watchdog.events import FileSystemEventHandler

from src.automation.email_sender import send_email_via_mailgun
from src.automation.file_organizer import (
    backup_files,
    compress_files,
    detect_duplicates,
    rename_files,
    sort_by_date,
    sort_by_size,
    sort_by_type,
)

logger = logging.getLogger(__name__)

# Maps task identifiers to their respective functions
TASK_FUNCTIONS = {
    "sort_by_type": sort_by_type,
    "sort_by_date": sort_by_date,
    "sort_by_size": sort_by_size,
    "detect_duplicates": detect_duplicates,
    "rename_files": rename_files,
    "compress_files": compress_files,
    "backup_files": backup_files,
    "send_email": send_email_via_mailgun,
}

# User-friendly task labels
TASK_LABELS = {
    "sort_by_type": "Sort by Type",
    "sort_by_date": "Sort by Date",
    "sort_by_size": "Sort by Size",
    "detect_duplicates": "Detect Duplicates",
    "rename_files": "Rename Files",
    "compress_files": "Compress Files",
    "backup_files": "Backup Files",
    "send_email": "Send Email",
}


class JSONFileChangeHandler(FileSystemEventHandler):
    """
    Watchdog handler that reloads scheduled
    jobs whenever the JSON file is modified.
    """

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def on_modified(self, event):
        if event.src_path.endswith("scheduled_jobs.json"):
            logger.info("Detected changes in scheduled_jobs.json; reloading jobs.")
            self.manager.load_jobs_from_file()
