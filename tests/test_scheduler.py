import json
import sys
import time

from PyQt5.QtCore import QCoreApplication
from apscheduler.schedulers.base import SchedulerNotRunningError
import pytest

from src.automation.scheduler import scheduler_manager as scheduler_module
from src.automation.scheduler.scheduler_manager import SchedulerManager


@pytest.fixture(scope="function", autouse=True)
def ensure_qapp():
    """Ensure a QCoreApplication instance exists for QStandardPaths."""
    app = QCoreApplication.instance()
    if app is None:
        QCoreApplication(sys.argv if hasattr(sys, 'argv') else [''])
    if not QCoreApplication.organizationName():
        QCoreApplication.setOrganizationName("AutoMateTestOrg")
    if not QCoreApplication.applicationName():
        QCoreApplication.setApplicationName("AutoMateTestApp")

@pytest.fixture
def mock_scheduler_paths(tmp_path, monkeypatch):
    """Creates temporary files/dirs and patches scheduler module paths."""
    temp_jobs_file = tmp_path / "test_scheduled_jobs.json"
    temp_attachments_dir = tmp_path / "test_attachments"
    temp_attachments_dir.mkdir()

    # Initialize jobs file
    temp_jobs_file.write_text("[]", encoding="utf-8")

    # Patch the module-level defaults
    monkeypatch.setattr(scheduler_module, "DEFAULT_JOBS_FILE", str(temp_jobs_file))
    monkeypatch.setattr(scheduler_module, "ATTACHMENTS_BASE_DIR", str(temp_attachments_dir))

    yield {
        "jobs_file": temp_jobs_file,
        "attachments_dir": temp_attachments_dir
    }

@pytest.fixture
def manager(mock_scheduler_paths):
    """
    A fixture that instantiates the SchedulerManager using the mocked paths.
    It will shut it down at the end of the test.
    """

    # Ensure the scheduler is not running before starting a new one
    m = SchedulerManager(jobs_file=str(mock_scheduler_paths["jobs_file"]), start_scheduler=True)
    yield m

    # Teardown
    try:
        if m.scheduler and m.scheduler.running:
            m.shutdown()
            # Add a small delay to allow threads to potentially close
            time.sleep(0.1)
    except SchedulerNotRunningError:
        pass # Ignore if it's already shut down
    except Exception as e:
        print(f"Error during scheduler teardown: {e}")


def test_add_one_time_job(manager, mock_scheduler_paths):
    """
    Add a one-time job (no recurring_days).
    Verify it's written to the JSON file and appears in manager.list_scheduled_jobs().
    """
    jobs_file = mock_scheduler_paths["jobs_file"]
    job_id = manager.add_scheduled_job(
        task_type="sort_by_date",
        folder_target="/test/folder",
        run_time="10:00",
        recurring_days=None,  # one-time
    )

    # Check that the job is in the manager's list
    time.sleep(0.1)
    jobs = manager.list_scheduled_jobs()
    assert len(jobs) >= 1, "Expected at least 1 job after adding."

    # Find the specific job
    job_found = next((job for job in jobs if job["job_id"] == job_id), None)
    assert job_found is not None, f"Job with ID {job_id} not found in list."
    assert job_found["task_type"] == "sort_by_date"
    assert job_found["folder_target"] == "/test/folder"

    # Check the JSON file
    data = json.loads(jobs_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["job_id"] == job_id
    assert data[0]["task_type"] == "sort_by_date"


def test_add_recurring_job(manager, mock_scheduler_paths):
    """
    Add a recurring job with recurring_days.
    Verify it shows up with the correct data.
    """
    jobs_file = mock_scheduler_paths["jobs_file"]
    job_id = manager.add_scheduled_job(
        task_type="sort_by_type",
        folder_target="/another/folder",
        run_time="14:30",
        recurring_days=["Monday", "Wednesday"]
    )

    # Check that the job is in the manager's list
    time.sleep(0.1)
    jobs = manager.list_scheduled_jobs()
    assert len(jobs) >= 1
    job_found = next((job for job in jobs if job["job_id"] == job_id), None)
    assert job_found is not None, f"Job with ID {job_id} not found in list."
    assert job_found["task_type"] == "sort_by_type"
    assert job_found["folder_target"] == "/another/folder"
    assert job_found["recurring_days"] == ["Monday", "Wednesday"]

    # Check the JSON file
    data = json.loads(jobs_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["job_id"] == job_id
    assert data[0]["recurring_days"] == ["Monday", "Wednesday"]


def test_remove_scheduled_job(manager, mock_scheduler_paths):
    """
    Add a job, then remove it.
    Confirm it's gone from both the scheduler and the JSON file.
    """
    jobs_file = mock_scheduler_paths["jobs_file"]
    job_id = manager.add_scheduled_job(
        task_type="backup_files",
        folder_target="/folder/backup",
        run_time="15:00"
    )

    # Sanity check it's there
    time.sleep(0.1)
    assert len(manager.list_scheduled_jobs()) >= 1

    # Remove
    manager.remove_scheduled_job(job_id)

    # Should be no jobs left in manager
    time.sleep(0.1)
    assert len(manager.list_scheduled_jobs()) == 0

    # Check JSON
    data = json.loads(jobs_file.read_text(encoding="utf-8"))
    assert len(data) == 0, "Job should be removed from JSON as well."


def test_load_jobs_from_file(mock_scheduler_paths, tmp_path): # Use mock_paths fixture here
    """
    Manually write a job into the JSON, then create a manager to ensure
    it loads that job on startup.
    """

    # Create a temporary jobs file with preloaded data
    jobs_file = mock_scheduler_paths["jobs_file"]

    job_data = [
        {
            "job_id": "preexisting_job",
            "task_type": "rename_files",
            "folder_target": "/preloaded/folder",
            "run_time": "17:00",
            "recurring_days": ["Tuesday"],
            "email_params": {},
            "data_params": {},
        }
    ]
    jobs_file.write_text(json.dumps(job_data), encoding="utf-8")

    # Create a new SchedulerManager instance
    m = SchedulerManager(jobs_file=str(jobs_file), start_scheduler=True)
    jobs = []
    try:
        time.sleep(0.1) # Give scheduler time to load
        jobs = m.list_scheduled_jobs()
        assert len(jobs) == 1
        assert jobs[0]["job_id"] == "preexisting_job"
        assert jobs[0]["task_type"] == "rename_files"
        assert jobs[0]["folder_target"] == "/preloaded/folder"
        assert jobs[0]["recurring_days"] == ["Tuesday"]
    finally:
        try:
            if m.scheduler and m.scheduler.running:
                 m.shutdown()
                 time.sleep(0.1)
        except SchedulerNotRunningError:
             pass
        except Exception as e:
             print(f"Error during load_jobs_from_file teardown: {e}")


def test_list_scheduled_jobs_empty(manager):
    """
    If no job was added, list_scheduled_jobs() should return an empty list.
    """
    time.sleep(0.1)
    jobs = manager.list_scheduled_jobs()
    assert isinstance(jobs, list)
    assert len(jobs) == 0


def test_list_scheduled_jobs_multiple(manager):
    """
    Add multiple jobs and check that listing returns them all.
    """
    manager.add_scheduled_job(
        task_type="compress_files",
        folder_target="/job1",
        run_time="09:00"
    )
    manager.add_scheduled_job(
        task_type="detect_duplicates",
        folder_target="/job2",
        run_time="09:30"
    )
    manager.add_scheduled_job(
        task_type="sort_by_size",
        folder_target="/job3",
        run_time="10:30"
    )

    # Check that the jobs are in the manager's list
    time.sleep(0.1)
    jobs = manager.list_scheduled_jobs()
    assert len(jobs) == 3
    tasks = set(j["task_type"] for j in jobs)
    assert tasks == {"compress_files", "detect_duplicates", "sort_by_size"}


def test_shutdown(manager):
    """
    Ensure that it can safely call .shutdown().
    (In practice, the fixture calls it, but here is done explicitly.)
    """
    manager.shutdown()

    # Check scheduler is not running
    assert not manager.scheduler.running
