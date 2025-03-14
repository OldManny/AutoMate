from datetime import datetime, timedelta
import json
import logging
import os
import shutil
import threading
import time

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from src.automation.scheduler.job_handler import TASK_FUNCTIONS, TASK_LABELS

logger = logging.getLogger(__name__)


class SchedulerManager:
    """
    Manages task scheduling using APScheduler,
    storing jobs persistently in a JSON file.
    """

    def __init__(self, jobs_file: str = "scheduled_jobs.json", start_scheduler: bool = True):
        self.jobs_file = jobs_file
        self.job_metadata = {}

        # Configure executors and job defaults
        executors = {
            'default': ThreadPoolExecutor(10),
            'processpool': ProcessPoolExecutor(3),
        }

        job_defaults = {
            # Coalesce ensures that only one instance of a job runs at a time
            'coalesce': True,
            'misfire_grace_time': 300,
        }

        # Create the scheduler
        self.scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

        # Start the scheduler
        if start_scheduler:
            self.scheduler.start()
            logger.info("Scheduler started with coalesce=True and misfire_grace_time=300.")
        else:
            logger.info("Scheduler created but NOT started (start_scheduler=False).")

        # Load existing jobs
        self.load_jobs_from_file()

        # Start a background thread to detect wake-ups
        if start_scheduler:
            wake_thread = threading.Thread(target=self._detect_wake_up, daemon=True)
            wake_thread.start()

    def _detect_wake_up(self):
        """
        Detects if the system has resumed from sleep and forces APScheduler to refresh.
        """
        last_time = time.time()

        while True:
            time.sleep(1)
            current_time = time.time()

            # If the time jumped forward significantly, assume wake-up
            if current_time - last_time > 10:  # If the system was "frozen" for 10+ sec
                logger.warning("System wake-up detected! Refreshing APScheduler without shutdown.")

                # Pause scheduling temporarily
                self.scheduler.pause()

                # Reload jobs to make sure they are still scheduled
                self.load_jobs_from_file()

                # Resume scheduling
                self.scheduler.resume()

            last_time = current_time

    def _job_listener(self, event):
        """
        Handle job execution events and cleanup for
        one-time jobs from JSON after execution.
        """
        if event.code == EVENT_JOB_ERROR:
            logger.error(f"Job {event.job_id} raised an error during execution.")

        elif event.code == EVENT_JOB_MISSED:
            logger.warning(f"Job {event.job_id} was missed.")

        elif event.code == EVENT_JOB_EXECUTED:
            job_data = self._get_job_from_file(event.job_id)
            # Only clean up non-recurring jobs
            if job_data and not job_data.get('recurring_days', []):
                self._cleanup_json_file(event.job_id)
                logger.info(f"One-time job {event.job_id} has been executed and removed from JSON.")

                # Clean up attachments for one time jobs
                self._cleanup_attachments(job_data)

        else:
            logger.debug(f"Unhandled event code: {event.code} for job {event.job_id}")

    def _get_job_from_file(self, job_id):
        """
        Retrieve job details from the JSON file by job ID.
        """
        try:
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, "r") as f:
                    job_list = json.load(f)
                    for job in job_list:
                        if job["job_id"] == job_id:
                            return job
        except Exception as e:
            logger.warning(f"Failed to read job {job_id} from file: {e}")
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

                # Only rewrite if something changed
                if len(updated_jobs) != len(job_list):
                    with open(self.jobs_file, "w") as f:
                        json.dump(updated_jobs, f, indent=2)
                    logger.info(f"Job {job_id} removed from scheduled_jobs.json.")
        except Exception as e:
            logger.error(f"Error removing job {job_id} from JSON: {e}")

    def _persist_attachments(self, job_id, attachments):
        """
        Copies each attachment into a dedicated folder to ensure they remain available
        when APScheduler runs the job in the future.
        """
        if not attachments:
            return []

        base_dir = "scheduled_attachments"
        os.makedirs(base_dir, exist_ok=True)

        new_paths = []
        for original_path in attachments:
            if not os.path.isfile(original_path):
                logger.warning(f"Attachment {original_path} does not exist or is not accessible.")
                continue

            # Prevent filename collisions by prefixing with job_id
            filename = os.path.basename(original_path)
            new_filename = f"{job_id}_{filename}"
            new_path = os.path.join(base_dir, new_filename)

            try:
                shutil.copyfile(original_path, new_path)
                new_paths.append(new_path)
                logger.info(f"Copied attachment '{original_path}' -> '{new_path}'")
            except Exception as e:
                logger.error(f"Failed to copy attachment '{original_path}': {e}")

        return new_paths

    def _cleanup_attachments(self, job_data):
        """
        Removes attachments from storage after a one-time email job has been executed.
        """
        attachments = job_data.get("email_params", {}).get("attachments", [])
        for path in attachments:
            try:
                os.remove(path)
                logger.info(f"Removed attachment file: {path}")
            except Exception as e:
                logger.warning(f"Could not remove {path}: {e}")

    def add_scheduled_job(
        self, task_type, folder_target, run_time, recurring_days=None, job_id=None, email_params=None, data_params=None
    ):
        """
        Schedule a new job in APScheduler.
        Supports both recurring and one-time jobs.
        """
        if not job_id:
            job_id = f"{task_type}_{datetime.now().timestamp()}"

        logger.info(f"Adding job {job_id} -> Task: {task_type}, Time: {run_time}, Days: {recurring_days}")

        # Build job_data with both email_params and data_params
        job_data = {
            "job_id": job_id,
            "task_type": task_type,
            "folder_target": folder_target,
            "run_time": run_time,
            "recurring_days": recurring_days or [],
            "email_params": email_params or {},
            "data_params": data_params or {},
        }

        self._schedule_job(job_data, persist=True)
        return job_id

    def _schedule_job(self, job_data, persist=True):
        """
        Add a job to APScheduler and save it to the JSON file if persist=True.
        """
        job_id = job_data["job_id"]
        task_type = job_data["task_type"]
        folder_target = job_data["folder_target"]
        run_time = job_data["run_time"]
        recurring_days = job_data.get("recurring_days", [])
        email_params = job_data.get("email_params", {})
        data_params = job_data.get("data_params", {})

        hour, minute = map(int, run_time.split(":"))
        now = datetime.now()

        friendly_task_name = TASK_LABELS.get(task_type, task_type)
        logger.debug(f"Scheduling job {job_id}: {friendly_task_name} for {run_time} (persist={persist})")

        # Store metadata
        self.job_metadata[job_id] = {
            "recurring_days": recurring_days,
            "task_type": task_type,
            "folder_target": folder_target,
        }

        # Determine the appropriate trigger for the job
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
            logger.info(f"Job {job_id} is recurring on {recurring_days} at {run_time}.")
        else:
            # One-time job => schedule for today or tomorrow if time is past
            schedule_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if schedule_today <= now:
                schedule_today += timedelta(days=1)
            trigger = DateTrigger(run_date=schedule_today)
            logger.info(f"One-time job {job_id} scheduled for {schedule_today}.")

        # Get the function for the task
        task_callable = TASK_FUNCTIONS.get(task_type)
        if not task_callable:
            logger.error(f"Task function '{task_type}' not found. Job {job_id} not scheduled.")
            return

        # Decide how to add the job
        if task_type == "send_email":
            # Copy attachments in temp folder
            if persist:
                attachments = email_params.get("attachments", [])
                persisted_paths = self._persist_attachments(job_id, attachments)
                # Update the email_params with the new permanent paths
                email_params["attachments"] = persisted_paths

            self.scheduler.add_job(
                func=task_callable,
                trigger=trigger,
                id=job_id,
                kwargs={
                    "from_address": email_params.get("from_address"),
                    "to_addresses": email_params.get("to_addresses"),
                    "subject": email_params.get("subject"),
                    "body_text": email_params.get("body_text"),
                    "cc_addresses": email_params.get("cc_addresses"),
                    "attachments": email_params.get("attachments"),
                },
                replace_existing=True,
            )

        elif task_type in ("merge_data", "mirror_data"):
            self.scheduler.add_job(
                func=TASK_FUNCTIONS[task_type],
                trigger=trigger,
                id=job_id,
                kwargs={
                    "source_directory": folder_target,
                    "data_params": data_params,
                },
                replace_existing=True,
            )
        else:
            # File or other tasks
            self.scheduler.add_job(
                func=task_callable,
                trigger=trigger,
                id=job_id,
                kwargs={"source_directory": folder_target},
                replace_existing=True,
            )

        # Persist job_data if requested
        if persist:
            self._write_job_to_file(job_data)

    def _write_job_to_file(self, job_data):
        """
        Save or update job details in the JSON file.
        """
        try:
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, "r") as f:
                    job_list = json.load(f)
            else:
                job_list = []

            # Remove old entry for the same job_id and add the new one
            job_list = [j for j in job_list if j["job_id"] != job_data["job_id"]]
            job_list.append(job_data)

            with open(self.jobs_file, "w") as f:
                json.dump(job_list, f, indent=2)
            logger.info(f"Job {job_data['job_id']} saved to JSON.")
        except Exception as e:
            logger.error(f"Error writing job {job_data['job_id']} to JSON: {e}")

    def list_scheduled_jobs(self):
        """
        Return a list of currently scheduled jobs with their details.
        """
        jobs_data = []
        for job in self.scheduler.get_jobs():
            # Get metadata for the job
            metadata = self.job_metadata.get(job.id, {})
            task_type = metadata.get("task_type")
            recurring_days = metadata.get("recurring_days", [])

            # For one-time jobs, check if they are still in the JSON file. If not, skip them
            if not recurring_days:
                if self._get_job_from_file(job.id) is None:
                    continue

            # Determine the target based on job type
            if task_type == "send_email":
                # For email jobs, get recipients from the job kwargs
                to_addresses = job.kwargs.get("to_addresses", [])
                target = ", ".join(to_addresses) if to_addresses else "-"
            else:
                # For file jobs, get the source directory
                target = metadata.get("folder_target") or job.kwargs.get("source_directory", "-")

            # Get the next run time
            next_run = None
            try:
                job_info = self.scheduler._job_stores['default'].get_job(job.id)
                if job_info and hasattr(job_info, 'next_run_time'):
                    next_run = str(job_info.next_run_time) if job_info.next_run_time else None
            except Exception:
                try:
                    now = datetime.now()
                    # Get next fire time from trigger
                    next_time = job.trigger.get_next_fire_time(None, now)
                    if next_time:
                        next_run = str(next_time)
                except Exception:
                    # If all else fails, use trigger string to indicate schedule
                    next_run = f"According to: {str(job.trigger)}"

            jobs_data.append(
                {
                    "job_id": job.id,
                    "task_type": task_type,
                    "folder_target": target,
                    "trigger": str(job.trigger),
                    "next_run_time": next_run,
                    "recurring_days": metadata.get("recurring_days", []),
                }
            )

        logger.info(f"Listing {len(jobs_data)} active jobs.")
        return jobs_data

    def load_jobs_from_file(self):
        """
        Load (or reload) scheduled jobs from a JSON file into APScheduler.
        """
        if not os.path.exists(self.jobs_file):
            return

        logger.info("Loading jobs from scheduled_jobs.json...")
        try:
            with open(self.jobs_file, "r") as f:
                file_jobs = json.load(f)
        except Exception as e:
            file_jobs = []
            logger.error(f"Error reading scheduled_jobs.json: {e}")

        # Convert file job list to a dict for quick lookup
        file_jobs_dict = {j["job_id"]: j for j in file_jobs if "job_id" in j}

        # Remove any APScheduler jobs that aren't in the file
        all_current_jobs = self.scheduler.get_jobs()
        removed_jobs_count = 0
        for job in all_current_jobs:
            if job.id not in file_jobs_dict:
                try:
                    self.scheduler.remove_job(job.id)
                    removed_jobs_count += 1
                    logger.info(f"Removed job {job.id} from scheduler (not found in JSON).")
                except Exception:
                    logger.exception(f"Failed to remove job {job.id}.")

        # Re-schedule or add each job from file
        for job_data in file_jobs:
            self._schedule_job(job_data, persist=False)

        logger.info(f"File load complete. {removed_jobs_count} job(s) removed, {len(file_jobs)} job(s) processed.")

    def remove_scheduled_job(self, job_id):
        """
        Remove a job from both the scheduler and JSON file.
        Also cleans up any attachments associated with the job.
        """
        logger.info(f"Removing scheduled job {job_id}.")

        # Get job data before removing it from JSON
        job_data = self._get_job_from_file(job_id)
        self._cleanup_json_file(job_id)

        # Clean up any attachments if this was an email job
        if job_data and "email_params" in job_data:
            self._cleanup_attachments(job_data)

        # Remove from scheduler
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed from scheduler.")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id} from scheduler: {e}")

    def shutdown(self):
        """
        Shut down the APScheduler instance.
        """
        if self.scheduler is not None and self.scheduler.running:
            logger.info("Shutting down scheduler.")
            self.scheduler.shutdown(wait=False)
        else:
            logger.info("Scheduler is not running, skipping shutdown.")
