from datetime import datetime
import shutil

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
from src.utils.undo_manager import undo_file_operation


@pytest.fixture
def test_directory(tmp_path):
    """
    Setup a temporary test directory.
    """
    # Create sample files
    temp_dir = tmp_path / "test_dir"
    temp_dir.mkdir()
    (temp_dir / "image1.jpg").write_text("Image content")
    (temp_dir / "doc1.pdf").write_text("Document content")
    (temp_dir / "audio1.mp3").write_text("Audio content")
    (temp_dir / "small_file.txt").write_text("Small content")
    yield temp_dir   # Cleanup test leftovers from OS

    # Explicit cleanup after the test ends
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def test_sort_by_type(test_directory):
    """
    Test the sort_by_type function.
    """
    sort_by_type(str(test_directory))
    assert (test_directory / "images" / "image1.jpg").exists()
    assert (test_directory / "documents" / "doc1.pdf").exists()


def test_sort_by_date(test_directory):
    """
    Test the sort_by_date function.
    """
    sort_by_date(str(test_directory))
    today = datetime.now().strftime("%Y-%m-%d")
    assert (test_directory / today / "image1.jpg").exists()


def test_sort_by_size(test_directory):
    """
    Test the sort_by_size function.
    """
    sort_by_size(str(test_directory))
    assert (test_directory / "small" / "small_file.txt").exists()


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

    # Verify one file remains in the source directory
    assert file_1.exists() or file_2.exists()

    # Verify the duplicate was moved
    moved_file = file_1 if not file_1.exists() else file_2
    assert (duplicates_folder / moved_file.name).exists()


def test_rename_files(test_directory):
    """
    Test the rename_files function.
    """
    rename_files(str(test_directory))
    for file in test_directory.iterdir():
        if file.is_file():
            assert "_" in file.name  # Ensure timestamp is appended


def test_compress_files(test_directory):
    """
    Test the compress_files function.
    """
    # Create test files
    for i in range(3):
        (test_directory / f"file{i}.txt").write_text(f"Content of file {i}")

    compress_files(str(test_directory))
    assert (test_directory / "compressed_files.zip").exists()


def test_backup_files(test_directory):
    """
    Test the backup_files function.
    """
    backup_files(str(test_directory))
    backup_folder = [folder for folder in test_directory.iterdir() if "backup_" in folder.name][0]
    assert (backup_folder / "image1.jpg").exists()
    assert (backup_folder / "doc1.pdf").exists()


def test_undo_file_operation(test_directory):
    """
    Test the undo_file_operation function.
    """
    # Perform an operation
    sort_by_type(str(test_directory))
    undo_file_operation()
    assert (test_directory / "image1.jpg").exists()
    assert not (test_directory / "images").exists()
