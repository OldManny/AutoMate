import pandas as pd
import pytest

from src.automation.data_entry import (
    combine_first_last_into_full,
    merge_data,
    mirror_data,
    split_full_into_first_last,
    unify_column_name,
)
from src.utils import undo_manager


def undo_data_operation_local():
    """Local wrapper to ensure LOG_FILE is set before calling."""
    if not undo_manager.LOG_FILE:
         raise ValueError("LOG_FILE not set for undo_data_operation")

    # Dynamically import or call the original function
    from src.utils.undo_manager import undo_data_operation
    undo_data_operation()


@pytest.fixture
def mock_undo_log(tmp_path, monkeypatch):
    """Patches the undo_manager.LOG_FILE path."""
    temp_log_file = tmp_path / "test_operation_log.json"
    monkeypatch.setattr(undo_manager, "LOG_FILE", str(temp_log_file))
    yield temp_log_file # Return the path if needed

    # Clean up the log file if it exists after test
    if temp_log_file.exists():
        temp_log_file.unlink()

@pytest.fixture
def sample_df():
    """
    Returns a simple DataFrame to test the combine/split functions.
    """
    return pd.DataFrame({
        "First Name": ["Alice", "Bob"],
        "Last Name": ["Smith", "Johnson"],
        "Email": ["alice@example.com", "bob@example.com"]
    })


def test_unify_column_name():
    """
    Verifies that synonyms map to the expected standard names.
    """
    assert unify_column_name("First Name") == "first_name"
    assert unify_column_name("last name") == "last_name"
    assert unify_column_name("full name") == "full_name"
    assert unify_column_name("DOB") == "dob"
    assert unify_column_name("random_column") == "random_column"  # No change if unknown


def test_combine_first_last_into_full(sample_df):
    """
    Ensures combine_first_last_into_full creates a 'Full Name' column from 'First Name' and 'Last Name'.
    """
    combine_first_last_into_full(sample_df)
    assert "Full Name" in sample_df.columns
    assert sample_df.loc[0, "Full Name"] == "Alice Smith"
    assert sample_df.loc[1, "Full Name"] == "Bob Johnson"


def test_split_full_into_first_last():
    """
    Tests splitting a 'Full Name' into 'First Name' / 'Last Name' columns.
    """
    df = pd.DataFrame({"Full Name": ["Alice Smith", "Bob"]})
    split_full_into_first_last(df)
    assert "First Name" in df.columns
    assert "Last Name" in df.columns
    assert df.loc[0, "First Name"] == "Alice"
    assert df.loc[0, "Last Name"] == "Smith"

    # Single-word Full Name => goes to Last Name
    assert df.loc[1, "First Name"] == ""
    assert df.loc[1, "Last Name"] == "Bob"


@pytest.fixture
def data_temp_dir(tmp_path):
    """
    A temporary directory for testing merge_data and mirror_data with actual files.
    """
    return tmp_path


def test_merge_data(data_temp_dir, mock_undo_log):
    """
    Creates a master file and one or more 'other files' in the temp dir,
    then calls merge_data, and checks the results.
    """
    master_file = data_temp_dir / "master.csv"
    master_df = pd.DataFrame({
        "First Name": ["Carol"],
        "Last Name": ["Adams"]
    })
    master_df.to_csv(master_file, index=False)

    other_file = data_temp_dir / "other.csv"
    other_df = pd.DataFrame({
        "first_name": ["Dan"],
        "last_name": ["Williams"]
    })
    other_df.to_csv(other_file, index=False)

    merge_data(
        source_directory=str(data_temp_dir),
        data_params={
            "master_file": str(master_file),
            "other_files": [str(other_file)],
            "force_single_name_col": True,
        }
    )

    # Verify the master file was updated
    merged_df = pd.read_csv(master_file)

    # Should now contain Carol + Dan in a single 'Full Name' column if force_single_name_col is True
    assert len(merged_df) == 2
    assert "Full Name" in merged_df.columns
    assert "First Name" not in merged_df.columns  # Because was a forced single name col

    # Checking final values
    all_full_names = set(merged_df["Full Name"].tolist())
    assert "Carol Adams" in all_full_names
    assert "Dan Williams" in all_full_names


def test_mirror_data(data_temp_dir, mock_undo_log):
    """
    Tests mirroring the master file to target files, verifying that name columns are handled properly.
    """
    master_file = data_temp_dir / "master.xlsx"
    master_df = pd.DataFrame({
        "Full Name": ["Eve Brown"],
        "Email": ["eve@example.com"]
    })
    master_df.to_excel(master_file, index=False)

    target_file = data_temp_dir / "target.xlsx"

    # Start target with defined columns but no data
    target_df = pd.DataFrame({
        "First Name": pd.Series(dtype='object'), # Ensure correct types
        "Last Name": pd.Series(dtype='object'),
        "Email": pd.Series(dtype='object')
    })
    target_df.to_excel(target_file, index=False)

    mirror_data(
        source_directory=str(data_temp_dir),
        data_params={
            "master_file": str(master_file),
            "other_files": [str(target_file)],
            "force_single_name_col": False,  # keep both Full + split columns if they exist
        }
    )

    # Read back the target
    updated_target_df = pd.read_excel(target_file)

    # Should have appended the row from master
    assert len(updated_target_df) == 1

    # Should be "Full Name" in master, and "First/Last" in target => expect to see "Eve" / "Brown" in the target
    assert updated_target_df.loc[0, "First Name"] == "Eve"
    assert updated_target_df.loc[0, "Last Name"] == "Brown"
    assert updated_target_df.loc[0, "Email"] == "eve@example.com"


def test_undo_data_operation(data_temp_dir, mock_undo_log):
    """
    Demonstrates an undo test for data operations if you have a log + backup.
    """
    master_file = data_temp_dir / "master.csv"
    original_master_content = pd.DataFrame({"First Name": ["Alice"], "Last Name": ["Smith"]})
    original_master_content.to_csv(master_file, index=False)

    other_file = data_temp_dir / "other.csv"
    other_df = pd.DataFrame({"First Name": ["Bob"], "Last Name": ["Johnson"]})
    other_df.to_csv(other_file, index=False)

    # Perform merge
    merge_data(
        source_directory=str(data_temp_dir),
        data_params={
            "master_file": str(master_file),
            "other_files": [str(other_file)],
        }
    )

    # Master file should have Bob as well
    merged_df = pd.read_csv(master_file)
    assert len(merged_df) == 2

    # Undo the merge using the local wrapper that ensures LOG_FILE is set
    undo_data_operation_local()

    # After undo, the master should be back to original
    undone_df = pd.read_csv(master_file)

    # Use pandas comparison which handles NaNs etc. better
    pd.testing.assert_frame_equal(undone_df, original_master_content)
