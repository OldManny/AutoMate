import json

from apscheduler.schedulers.base import SchedulerNotRunningError
import pytest

from src.automation.scheduler.scheduler_manager import SchedulerManager


@pytest.fixture
def temp_jobs_file(tmp_path):
    """
    Creates a temporary JSON file for SchedulerManager to use
    instead of the real 'scheduled_jobs.json'.
    """
    file_path = tmp_path / "test_scheduled_jobs.json"
    file_path.write_text("[]", encoding="utf-8")  # Start with empty list
    return file_path


@pytest.fixture
def manager(temp_jobs_file):
    """
    A fixture that instantiates the SchedulerManager with a temporary jobs file.
    It will be shut it down at the end of the test to avoid background threads.
    """
    m = SchedulerManager(jobs_file=str(temp_jobs_file))
    yield m

    # Teardown
    try:
        m.shutdown()
    except SchedulerNotRunningError:
        pass  # Ignore if it's already shut down


def test_add_one_time_job(manager, temp_jobs_file):
    """
    Add a one-time job (no recurring_days).
    Verify it's written to the JSON file and appears in manager.list_scheduled_jobs().
    """
    job_id = manager.add_scheduled_job(
        task_type="sort_by_date",
        folder_target="/test/folder",
        run_time="10:00",
        recurring_days=None,  # one-time
    )

    # Check that the job is in the manager's list
    jobs = manager.list_scheduled_jobs()
    assert len(jobs) == 1, "Expected exactly 1 job after adding."
    assert jobs[0]["job_id"] == job_id
    assert jobs[0]["task_type"] == "sort_by_date"
    assert jobs[0]["folder_target"] == "/test/folder"

    # Check the JSON file
    data = json.loads(temp_jobs_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["job_id"] == job_id
    assert data[0]["task_type"] == "sort_by_date"


def test_add_recurring_job(manager, temp_jobs_file):
    """
    Add a recurring job with recurring_days.
    Verify it shows up with the correct data.
    """
    job_id = manager.add_scheduled_job(
        task_type="sort_by_type",
        folder_target="/another/folder",
        run_time="14:30",
        recurring_days=["Monday", "Wednesday"]
    )

    # Check that the job is in the manager's list
    jobs = manager.list_scheduled_jobs()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == job_id
    assert jobs[0]["task_type"] == "sort_by_type"
    assert jobs[0]["folder_target"] == "/another/folder"
    assert jobs[0]["recurring_days"] == ["Monday", "Wednesday"]

    # Check the JSON file
    data = json.loads(temp_jobs_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["job_id"] == job_id
    assert data[0]["recurring_days"] == ["Monday", "Wednesday"]


def test_remove_scheduled_job(manager, temp_jobs_file):
    """
    Add a job, then remove it.
    Confirm it's gone from both the scheduler and the JSON file.
    """
    job_id = manager.add_scheduled_job(
        task_type="backup_files",
        folder_target="/folder/backup",
        run_time="15:00"
    )

    # Sanity check it's there
    assert len(manager.list_scheduled_jobs()) == 1

    # Remove
    manager.remove_scheduled_job(job_id)

    # Should be no jobs left in manager
    assert len(manager.list_scheduled_jobs()) == 0

    # Check JSON
    data = json.loads(temp_jobs_file.read_text(encoding="utf-8"))
    assert len(data) == 0, "Job should be removed from JSON as well."


def test_load_jobs_from_file(tmp_path):
    """
    Manually write a job into the JSON, then create a manager to ensure
    it loads that job on startup.
    """
    file_path = tmp_path / "test_scheduled_jobs.json"
    job_data = [
        {
            "job_id": "preexisting_job",
            "task_type": "rename_files",
            "folder_target": "/preloaded/folder",
            "run_time": "17:00",
            "recurring_days": ["Tuesday"],
        }
    ]
    file_path.write_text(json.dumps(job_data), encoding="utf-8")

    # Create manager with that file => it should load the job
    m = SchedulerManager(jobs_file=str(file_path))
    jobs = m.list_scheduled_jobs()
    try:
        assert len(jobs) == 1
        assert jobs[0]["job_id"] == "preexisting_job"
        assert jobs[0]["task_type"] == "rename_files"
        assert jobs[0]["folder_target"] == "/preloaded/folder"
        assert jobs[0]["recurring_days"] == ["Tuesday"]
    finally:
        m.shutdown()


def test_list_scheduled_jobs_empty(manager):
    """
    If no job was added, list_scheduled_jobs() should return an empty list.
    """
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
