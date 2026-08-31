from datetime import datetime
import shutil
import time

import pytest

from src.automation.file_organizer import (
    backup_files,
    compress_files,
    detect_duplicates,
    rename_files,
    sort_by_date,
    sort_by_size,
    sort_by_type,
)
from src.utils import undo_manager


def undo_file_operation_local():
    """Local wrapper to ensure LOG_FILE is set before calling."""
    if not undo_manager.LOG_FILE:
         raise ValueError("LOG_FILE not set for undo_file_operation")

    # Dynamically import or call the original function now that LOG_FILE is set
    from src.utils.undo_manager import undo_file_operation
    undo_file_operation()

@pytest.fixture
def mock_undo_log(tmp_path, monkeypatch):
    """Patches the undo_manager.LOG_FILE path."""
    temp_log_file = tmp_path / "test_operation_log.json"

    # Ensure the file does not exist initially for some tests
    if temp_log_file.exists():
        temp_log_file.unlink()
    monkeypatch.setattr(undo_manager, "LOG_FILE", str(temp_log_file))

    # Ensure the log file is set in the undo_manager
    try:
         from src.automation import file_organizer
         monkeypatch.setattr(file_organizer.undo_manager, "LOG_FILE", str(temp_log_file), raising=False)
    except (ImportError, AttributeError):
         pass

    yield temp_log_file

    # Clean up the log file if it exists after test
    if temp_log_file.exists():
        try:
            temp_log_file.unlink()
        except OSError:
            pass

@pytest.fixture
def test_directory(tmp_path, mock_undo_log):
    """
    Setup a temporary test directory and ensure undo log is mocked.
    """
    temp_dir = tmp_path / "test_dir"
    temp_dir.mkdir()
    (temp_dir / "image1.jpg").write_text("Image content")
    (temp_dir / "doc1.pdf").write_text("Document content")
    (temp_dir / "audio1.mp3").write_text("Audio content")
    (temp_dir / "small_file.txt").write_text("Small content")
    yield temp_dir

    # Cleanup after the test ends
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_sort_by_type(test_directory):
    """
    Test the sort_by_type function.
    """
    sort_by_type(str(test_directory))
    images_dir = test_directory / "images"
    documents_dir = test_directory / "documents"
    assert images_dir.exists()
    assert documents_dir.exists()
    assert (images_dir / "image1.jpg").exists()
    assert (documents_dir / "doc1.pdf").exists()


def test_sort_by_date(test_directory):
    """
    Test the sort_by_date function.
    """
    time.sleep(0.01)
    (test_directory / "image1.jpg").touch()

    sort_by_date(str(test_directory))
    today = datetime.now().strftime("%Y-%m-%d")
    date_dir = test_directory / today
    assert date_dir.exists(), f"Directory for date {today} not found."

    # Check if at least one file moved
    moved_files = list(date_dir.glob('*'))
    assert len(moved_files) > 0, "No files were moved to the date directory."


def test_sort_by_size(test_directory):
    """
    Test the sort_by_size function.
    """
    sort_by_size(str(test_directory))
    small_dir = test_directory / "small"
    assert small_dir.exists()
    assert (small_dir / "small_file.txt").exists()


def test_detect_duplicates(test_directory):
    """
    Test the detect_duplicates function with known duplicates.
    """
    duplicate_content = b"This is a duplicate file."
    file_1 = test_directory / "file1.jpg"
    file_2 = test_directory / "duplicate.jpg"

    file_1.write_bytes(duplicate_content)
    file_2.write_bytes(duplicate_content)

    detect_duplicates(str(test_directory))

    # Verify folder structure
    duplicates_folder = test_directory / "duplicates"
    assert duplicates_folder.exists(), "Duplicates folder was not created."

    # Check which file was moved
    file1_exists = file_1.exists()
    file2_exists = file_2.exists()

    assert file1_exists != file2_exists, "Exactly one of the duplicate files should remain in the original location."

    # Verify the duplicate was moved
    moved_file_name = file_1.name if not file1_exists else file_2.name
    original_file_name = file_1.name if file1_exists else file_2.name

    assert (duplicates_folder / moved_file_name).exists(), f"Moved file {moved_file_name} not found in duplicates folder."
    assert not (duplicates_folder / original_file_name).exists(), f"Original file {original_file_name} should not be in duplicates folder."


def test_rename_files(test_directory):
    """
    Test the rename_files function.
    """
    original_files = {f.name for f in test_directory.iterdir() if f.is_file()}
    rename_files(str(test_directory))
    found_renamed = False
    timestamp_part = datetime.now().strftime("%Y-%m-%d_")

    for file in test_directory.iterdir():
        if file.is_file():
            assert file.name not in original_files  # Ensure original file names are not present
            assert timestamp_part in file.name  # Ensure timestamp format part is present
            found_renamed = True
    assert found_renamed, "No files were renamed."


def test_compress_files(test_directory):
    """
    Test the compress_files function.
    """

    # Create test files
    original_files = {"file0.txt", "file1.txt", "file2.txt"}
    for fname in original_files:
        (test_directory / fname).write_text(f"Content of {fname}")

    # Add the initial files from the fixture as well
    original_files.update({"image1.jpg", "doc1.pdf", "audio1.mp3", "small_file.txt"})

    compress_files(str(test_directory))
    archive_path = test_directory / "compressed_files.zip"
    assert archive_path.exists(), "Compressed archive was not created."

    # Check if original files were removed
    remaining_files = {f.name for f in test_directory.iterdir() if f.is_file() and f != archive_path}
    assert not remaining_files, f"Original files were not removed after compression: {remaining_files}"


def test_backup_files(test_directory):
    """
    Test the backup_files function.
    """
    backup_files(str(test_directory))

   # Find the backup folder (name includes timestamp)
    backup_folders = [folder for folder in test_directory.iterdir() if folder.is_dir() and "backup_" in folder.name]
    assert len(backup_folders) == 1, "Expected exactly one backup folder."
    backup_folder = backup_folders[0]

    assert (backup_folder / "image1.jpg").exists()
    assert (backup_folder / "doc1.pdf").exists()


def test_undo_file_operation(test_directory):
    """
    Test the undo_file_operation function after a sort_by_type operation.
    """

    # Perform an operation
    sort_by_type(str(test_directory))
    images_dir = test_directory / "images"
    assert images_dir.exists() # Verify state before undo
    assert (images_dir / "image1.jpg").exists()
    assert not (test_directory / "image1.jpg").exists()

    # Undo the operation
    undo_file_operation_local()

    # Check state after undo
    assert (test_directory / "image1.jpg").exists(), "image1.jpg not restored to original location."
    assert (test_directory / "doc1.pdf").exists()
    assert not images_dir.exists(), "Images directory created by sort should have been removed by undo."

    # Check other created dirs if applicable
    assert not (test_directory / "documents").exists()
    assert not (test_directory / "audio").exists()
