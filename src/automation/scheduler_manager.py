from datetime import datetime
import json
import os

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

# Import backend tasks for scheduling
from .file_organizer import (
    backup_files,
    compress_files,
    detect_duplicates,
    rename_files,
    sort_by_date,
    sort_by_size,
    sort_by_type,
)

# Maps task identifiers to their respective functions
TASK_FUNCTIONS = {
    "sort_by_type": sort_by_type,
    "sort_by_date": sort_by_date,
    "sort_by_size": sort_by_size,
    "detect_duplicates": detect_duplicates,
    "rename_files": rename_files,
    "compress_files": compress_files,
    "backup_files": backup_files,
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
}


class SchedulerManager:
    """
    Manages task scheduling using APScheduler, storing jobs persistently in a JSON file.
    """

    def __init__(self, jobs_file: str = "scheduled_jobs.json"):
        # Initialize the scheduler and job storage
        self.jobs_file = jobs_file
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.start()
        self.load_jobs_from_file()

    def _job_listener(self, event):
        """Handle job events (e.g., job completion or error)."""
        job = self.scheduler.get_job(event.job_id)
        if not job:
            return  # Skip if the job no longer exists

        # Automatically remove one-time jobs after execution
        if "DateTrigger" in str(job.trigger):
            self.remove_scheduled_job(event.job_id)

    def load_jobs_from_file(self):
        """Load scheduled jobs from a JSON file into the scheduler."""
        if not os.path.exists(self.jobs_file):
            return

        with open(self.jobs_file, "r") as f:
            try:
                job_list = json.load(f)
            except json.JSONDecodeError:
                job_list = []

        for job_data in job_list:
            self._schedule_job(job_data, persist=False)

    def list_scheduled_jobs(self):
        """Provide a summary of currently scheduled jobs."""
        scheduled = []
        for job in self.scheduler.get_jobs():
            scheduled.append(
                {
                    "job_id": job.id,
                    "task_type": job.kwargs.get("task_type"),
                    "folder_target": job.kwargs.get("source_directory"),
                    "trigger": str(job.trigger),
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                }
            )
        return scheduled

    def add_scheduled_job(self, task_type, folder_target, run_time, recurring_days=None, job_id=None):
        """
        Add a new job to the scheduler. Supports recurring or one-time scheduling.
        """
        if not job_id:
            job_id = f"{task_type}_{datetime.now().timestamp()}"

        job_data = {
            "job_id": job_id,
            "task_type": task_type,
            "folder_target": folder_target,
            "run_time": run_time,
            "recurring_days": recurring_days or [],
        }
        self._schedule_job(job_data, persist=True)
        return job_id

    def _schedule_job(self, job_data, persist=True):
        """Internal: Add a job to APScheduler and optionally persist it."""
        job_id = job_data["job_id"]
        task_type = job_data["task_type"]
        folder_target = job_data["folder_target"]
        run_time = job_data["run_time"]
        recurring_days = job_data.get("recurring_days", [])

        hour, minute = map(int, run_time.split(":"))
        now = datetime.now()

        # Choose trigger type based on recurrence
        if recurring_days:
            day_map = {
                "Monday": "mon",
                "Tuesday": "tue",
                "Wednesday": "wed",
                "Thursday": "thu",
                "Friday": "fri",
                "Saturday": "sat",
                "Sunday": "sun",
            }
            day_of_week = ",".join(day_map[d] for d in recurring_days)
            trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        else:
            # Schedule one-time for today or tomorrow
            schedule_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if schedule_today <= now:
                schedule_today = schedule_today.replace(day=schedule_today.day + 1)
            trigger = DateTrigger(run_date=schedule_today)

        # Retrieve the callable task function
        task_callable = TASK_FUNCTIONS.get(task_type)
        if not task_callable:
            print(f"Warning: No function found for '{task_type}'.")
            return

        # Schedule the job in APScheduler
        self.scheduler.add_job(
            func=task_callable,
            trigger=trigger,
            id=job_id,
            kwargs={"source_directory": folder_target, "task_type": task_type},
            replace_existing=True,
        )

        if persist:
            self._write_job_to_file(job_data)

    def _write_job_to_file(self, job_data):
        """Persist job data in a JSON file."""
        job_list = []
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file, "r") as f:
                try:
                    job_list = json.load(f)
                except json.JSONDecodeError:
                    job_list = []

        # Remove old job data if updating
        job_list = [j for j in job_list if j["job_id"] != job_data["job_id"]]
        job_list.append(job_data)

        with open(self.jobs_file, "w") as f:
            json.dump(job_list, f, indent=2)

    def remove_scheduled_job(self, job_id):
        """Remove a job from APScheduler and the JSON file."""
        self.scheduler.remove_job(job_id)
        if os.path.exists(self.jobs_file):
            with open(self.jobs_file, "r") as f:
                try:
                    job_list = json.load(f)
                except json.JSONDecodeError:
                    job_list = []
            job_list = [j for j in job_list if j["job_id"] != job_id]
            with open(self.jobs_file, "w") as f:
                json.dump(job_list, f, indent=2)

    def shutdown(self):
        """Shut down the APScheduler instance."""
        self.scheduler.shutdown()


if __name__ == "__main__":
    manager = SchedulerManager()
