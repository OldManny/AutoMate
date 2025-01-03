from datetime import datetime
import json
import os

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

# Backend tasks for scheduling
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
    Manages task scheduling using APScheduler.
    Allows jobs to be stored persistently in a JSON file for reloading.
    """

    def __init__(self, jobs_file: str = "scheduled_jobs.json"):
        # Initialize the scheduler and job metadata storage
        self.jobs_file = jobs_file
        self.scheduler = BackgroundScheduler()
        self.job_metadata = {}
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.start()
        self.load_jobs_from_file()

    def _job_listener(self, event):
        """
        Handle job execution events and cleanup
        one-time jobs from JSON after execution.
        """
        if event.code == EVENT_JOB_ERROR:
            return  # Skip error handling for now

        job_data = self._get_job_from_file(event.job_id)
        if job_data and not job_data.get('recurring_days', []):  # Only clean up non-recurring jobs
            self._cleanup_json_file(event.job_id)

    def _get_job_from_file(self, job_id):
        """
        Retrieve job details from the JSON file by job ID.
        """
        try:
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, "r") as f:
                    job_list = json.load(f)
                    return next((job for job in job_list if job["job_id"] == job_id), None)
        except Exception:
            return None

    def _cleanup_json_file(self, job_id):
        """
        Remove a job's data from the JSON file.
        """
        try:
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, "r") as f:
                    job_list = json.load(f)

                # Keep all jobs except the one to be removed
                updated_jobs = [j for j in job_list if j["job_id"] != job_id]

                # Rewrite the file if there are changes
                if len(updated_jobs) != len(job_list):
                    with open(self.jobs_file, "w") as f:
                        json.dump(updated_jobs, f, indent=2)
        except Exception:
            pass  # Ignore errors to avoid breaking functionality

    def add_scheduled_job(self, task_type, folder_target, run_time, recurring_days=None, job_id=None):
        """
        Schedule a new job in APScheduler.
        Supports both recurring and one-time jobs.
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
        """
        Add a job to APScheduler.
        """
        job_id = job_data["job_id"]
        task_type = job_data["task_type"]
        folder_target = job_data["folder_target"]
        run_time = job_data["run_time"]
        recurring_days = job_data.get("recurring_days", [])

        hour, minute = map(int, run_time.split(":"))
        now = datetime.now()

        self.job_metadata[job_id] = {"recurring_days": recurring_days}

        # Determine the appropriate trigger for the job
        if recurring_days:
            # Convert days to APScheduler's day_of_week format
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
            # Schedule for today or tomorrow if time has passed
            schedule_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if schedule_today <= now:
                schedule_today = schedule_today.replace(day=schedule_today.day + 1)
            trigger = DateTrigger(run_date=schedule_today)

        #  Get the corresponding function for the task
        task_callable = TASK_FUNCTIONS.get(task_type)
        if not task_callable:
            return

        # Add the job to the scheduler
        self.scheduler.add_job(
            func=task_callable,
            trigger=trigger,
            id=job_id,
            kwargs={
                "source_directory": folder_target,
                "task_type": task_type,
                "recurring_days": recurring_days,
            },
            replace_existing=True,
        )

        if persist:
            self._write_job_to_file(job_data)

    def _write_job_to_file(self, job_data):
        """
        Save or update job details in the JSON file.
        """
        try:
            job_list = []
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, "r") as f:
                    job_list = json.load(f)

            # Remove old entry for the same job ID and add the new one
            job_list = [j for j in job_list if j["job_id"] != job_data["job_id"]]
            job_list.append(job_data)

            with open(self.jobs_file, "w") as f:
                json.dump(job_list, f, indent=2)
        except Exception:
            pass

    def list_scheduled_jobs(self):
        """
        Return a list of currently scheduled jobs with their details.
        """
        return [
            {
                "job_id": job.id,
                "task_type": job.kwargs.get("task_type"),
                "folder_target": job.kwargs.get("source_directory"),
                "trigger": str(job.trigger),
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "recurring_days": job.kwargs.get("recurring_days", []),
            }
            for job in self.scheduler.get_jobs()
        ]

    def load_jobs_from_file(self):
        """
        Load jobs from the JSON file and schedule them in APScheduler.
        """
        if not os.path.exists(self.jobs_file):
            return

        try:
            with open(self.jobs_file, "r") as f:
                job_list = json.load(f)
                for job_data in job_list:
                    self._schedule_job(job_data, persist=False)
        except Exception:
            pass

    def remove_scheduled_job(self, job_id):
        """
        Remove a job from both the scheduler and the JSON file.
        """
        self._cleanup_json_file(job_id)
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass

    def shutdown(self):
        """
        Shut down the APScheduler instance.
        """
        self.scheduler.shutdown()
