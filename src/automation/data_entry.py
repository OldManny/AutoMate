import ctypes
import os
import platform
import shutil

import pandas as pd

from src.utils.column_mappings import SYNONYMS
from src.utils.undo_manager import clear_previous_log, log_operation

# Define a log file for data operations
LOG_FILE = "operation_log.json"


def make_file_hidden_windows(filepath):
    """
    Sets the 'hidden' attribute on Windows for a given file path.
    No effect on non-Windows platforms.
    """
    if platform.system().lower().startswith("win") and os.path.exists(filepath):
        FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            # Convert to a wide string (W) for SetFileAttributesW
            ctypes.windll.kernel32.SetFileAttributesW(str(filepath), FILE_ATTRIBUTE_HIDDEN)
        except Exception as e:
            print(f"Could not hide file {filepath}. Error: {e}")


def combine_first_last_into_full(df: pd.DataFrame, create_if_missing: bool = True):
    """Combines first and last name columns into a full name column if needed."""
    first_name_col = None
    last_name_col = None

    # Check for all possible first/last name columns
    for col in df.columns:
        if unify_column_name(col) == "first_name":
            first_name_col = col
        elif unify_column_name(col) == "last_name":
            last_name_col = col

    if first_name_col or last_name_col:
        # Look for or create full name column
        full_name_col = None
        for col in df.columns:
            if unify_column_name(col) == "full_name":
                full_name_col = col
                break

        if full_name_col is None and create_if_missing:
            full_name_col = "Full Name"
            df[full_name_col] = ""
        elif full_name_col is None:
            return

        for i in df.index:
            # Skip if full name already exists
            if pd.notna(df.at[i, full_name_col]) and str(df.at[i, full_name_col]).strip():
                continue

            # Get first/last name values
            f_val = (
                str(df.at[i, first_name_col]).strip() if first_name_col and pd.notna(df.at[i, first_name_col]) else ""
            )
            l_val = str(df.at[i, last_name_col]).strip() if last_name_col and pd.notna(df.at[i, last_name_col]) else ""

            # Combine parts
            parts = []
            if f_val:
                parts.append(f_val)
            if l_val:
                parts.append(l_val)
            df.at[i, full_name_col] = " ".join(parts)


def split_full_into_first_last(df: pd.DataFrame, create_if_missing: bool = True):
    """Splits a full name column into separate first and last name columns if applicable."""

    # Find full name column if it exists
    full_name_col = None
    for col in df.columns:
        if unify_column_name(col) == "full_name":
            full_name_col = col
            break

    if full_name_col:
        # Find or create first/last name columns
        first_name_col = None
        last_name_col = None

        for col in df.columns:
            if unify_column_name(col) == "first_name":
                first_name_col = col
            elif unify_column_name(col) == "last_name":
                last_name_col = col

        if create_if_missing:
            if not first_name_col:
                first_name_col = "First Name"
                df[first_name_col] = ""
            if not last_name_col:
                last_name_col = "Last Name"
                df[last_name_col] = ""
        elif not first_name_col or not last_name_col:
            return

        for i in df.index:
            # Skip if first/last names already filled
            if (pd.notna(df.at[i, first_name_col]) and str(df.at[i, first_name_col]).strip()) or (
                pd.notna(df.at[i, last_name_col]) and str(df.at[i, last_name_col]).strip()
            ):
                continue

            # Split full name
            if pd.notna(df.at[i, full_name_col]):
                val = str(df.at[i, full_name_col]).strip()
                parts = val.split(maxsplit=1)
                if len(parts) == 2:
                    df.at[i, first_name_col] = parts[0]
                    df.at[i, last_name_col] = parts[1]
                elif len(parts) == 1 and parts[0]:  # Single word
                    df.at[i, last_name_col] = parts[0]  # Treat as Last Name
                    df.at[i, first_name_col] = ""


def unify_column_name(col_name: str) -> str:
    """Normalizes column names by converting known variations to a standard format."""
    if not col_name or not isinstance(col_name, str):
        return col_name

    norm = col_name.strip().replace("_", "").replace("-", "").replace(" ", "").lower()
    for mk, syns in SYNONYMS.items():
        mk_norm = mk.replace("_", "").replace("-", "").replace(" ", "").lower()
        if norm == mk_norm:
            return mk
        for s in syns:
            s_norm = s.replace("_", "").replace("-", "").replace(" ", "").lower()
            if norm == s_norm:
                return mk
    return col_name


def read_csv_or_excel(path: str) -> pd.DataFrame:
    """Reads a CSV or Excel file and returns a DataFrame."""
    _, ext = os.path.splitext(path.lower())
    if ext == ".csv":
        try:
            return pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    else:
        try:
            return pd.read_excel(path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()


def write_csv_or_excel(df: pd.DataFrame, path: str):
    """Writes a DataFrame to a CSV or Excel file."""
    _, ext = os.path.splitext(path.lower())
    if ext == ".csv":
        df.to_csv(path, index=False)
    else:
        df.to_excel(path, index=False)


def merge_data(source_directory, data_params=None):
    """Merges multiple data files while ensuring consistent name handling."""
    # Remove leftover backups from any previous operation
    clear_previous_log()

    if not data_params:
        return

    # Extract parameters
    master_file = data_params.get("master_file")
    other_files = data_params.get("other_files", [])
    column_map = data_params.get("column_map")
    force_single = data_params.get("force_single_name_col", False)

    # Backup the master file before overwiting it
    if master_file and os.path.isfile(master_file):
        dir_name = os.path.dirname(master_file)
        base_name = os.path.basename(master_file)
        backup_file = os.path.join(dir_name, "." + base_name + ".bak")
        shutil.copy(master_file, backup_file)
        make_file_hidden_windows(backup_file)
        log_operation("merge_data", master_file, backup_file)

    # Read master file
    master_df = read_csv_or_excel(master_file)

    if force_single:
        # Combine master’s first + last into full name
        combine_first_last_into_full(master_df, create_if_missing=True)

        # Remove "First Name" and "Last Name" columns from the master
        to_remove = [col for col in master_df.columns if unify_column_name(col) in ["first_name", "last_name"]]
        if to_remove:
            master_df.drop(columns=to_remove, inplace=True)

    # Determine initial name handling strategy based on master file
    master_has_full = any(unify_column_name(col) == "full_name" for col in master_df.columns)
    master_has_split = any(unify_column_name(col) == "first_name" for col in master_df.columns) or any(
        unify_column_name(col) == "last_name" for col in master_df.columns
    )

    # Build master column mapping
    master_mapping = {}
    for col in master_df.columns:
        unified = unify_column_name(col)
        master_mapping[unified] = col

    # Process each additional file
    for f in other_files:
        if not os.path.isfile(f):
            continue

        incoming_df = read_csv_or_excel(f)
        if incoming_df.empty:
            continue

        # Apply explicit column mapping
        if column_map and f in column_map:
            incoming_df.rename(columns=column_map[f], inplace=True)

        # Handle name columns based on master structure
        if master_has_full and not master_has_split:
            # Master only has full name
            combine_first_last_into_full(incoming_df)
            if force_single:
                # Remove first/last name columns after combining
                for col in list(incoming_df.columns):
                    if unify_column_name(col) in ["first_name", "last_name"]:
                        incoming_df.drop(columns=[col], inplace=True)
        elif master_has_split and not master_has_full:
            # Master only has split names
            split_full_into_first_last(incoming_df)
            if force_single:
                # Remove full name column after splitting
                for col in list(incoming_df.columns):
                    if unify_column_name(col) == "full_name":
                        incoming_df.drop(columns=[col], inplace=True)
        elif master_has_full and master_has_split:
            # Master has both - maintain both formats
            if any(unify_column_name(col) == "full_name" for col in incoming_df.columns):
                split_full_into_first_last(incoming_df, create_if_missing=not force_single)
            if any(unify_column_name(col) in ["first_name", "last_name"] for col in incoming_df.columns):
                combine_first_last_into_full(incoming_df, create_if_missing=not force_single)

        # Map incoming columns to master columns based on unified names
        col_mapping = {}
        for col in incoming_df.columns:
            unified = unify_column_name(col)
            if unified in master_mapping:
                # Only map if names are different
                if col != master_mapping[unified]:
                    col_mapping[col] = master_mapping[unified]

        if col_mapping:
            incoming_df.rename(columns=col_mapping, inplace=True)

        # Add new columns from master if they don't exist in incoming
        for mcol in master_df.columns:
            if mcol not in incoming_df.columns:
                incoming_df[mcol] = ""

        # Reorder columns to match master
        incoming_df = incoming_df[master_df.columns]

        # Concatenate dataframes efficiently
        master_df = pd.concat([master_df, incoming_df], ignore_index=True)

    # Final processing
    master_df.drop_duplicates(inplace=True)

    # Ensure no NaN values
    master_df = master_df.fillna("")

    write_csv_or_excel(master_df, master_file)


def mirror_data(source_directory, data_params=None):
    """
    Mirror master file data to targets, properly handling name columns and edge cases.
    """
    # Remove leftover backups from any previous operation
    clear_previous_log()

    if not data_params:
        return

    master_file = data_params.get("master_file")
    other_files = data_params.get("other_files", [])
    column_map = data_params.get("column_map")
    force_single = data_params.get("force_single_name_col", False)
    target_files = data_params.get("other_files", [])

    if not master_file or not os.path.isfile(master_file):
        return

    # Dictionary to store backups for each target file
    backups = {}

    # Backup each target file that exists before overwriting it
    for target in target_files:
        if os.path.isfile(target):
            dir_name = os.path.dirname(target)
            base_name = os.path.basename(target)
            backup = os.path.join(dir_name, "." + base_name + ".bak")
            shutil.copy(target, backup)
            make_file_hidden_windows(backup)
            backups[target] = backup

    # Log the mirror operation with backups mapping
    log_operation("mirror_data", master_file, backups)

    # Use the columns names from master
    master_raw_df = read_csv_or_excel(master_file)

    # A working copy for name unification
    master_df = master_raw_df.copy()

    # Check if master has name columns
    master_has_full = any(unify_column_name(col) == "full_name" for col in master_df.columns)
    master_has_first = any(unify_column_name(col) == "first_name" for col in master_df.columns)
    master_has_last = any(unify_column_name(col) == "last_name" for col in master_df.columns)

    # Process each target file
    for target_file in other_files:
        if not os.path.isfile(target_file):
            continue

        # Read target file
        target_df = read_csv_or_excel(target_file)

        # Handle completely empty file (no columns) - make exact copy
        if target_df.empty and target_df.columns.size == 0:
            write_csv_or_excel(master_raw_df, target_file)
            continue

        # Pre-process master data for name columns if needed
        if master_has_full and (master_has_first or master_has_last) and not force_single:
            # Both name formats exist - ensure they're in sync
            for idx in master_df.index:
                # Find column names
                full_col = next((c for c in master_df.columns if unify_column_name(c) == "full_name"), None)
                first_col = next((c for c in master_df.columns if unify_column_name(c) == "first_name"), None)
                last_col = next((c for c in master_df.columns if unify_column_name(c) == "last_name"), None)

                if full_col and (first_col or last_col):
                    # Get existing values
                    full_val = str(master_df.at[idx, full_col]).strip() if pd.notna(master_df.at[idx, full_col]) else ""
                    f_val = (
                        str(master_df.at[idx, first_col]).strip()
                        if first_col and pd.notna(master_df.at[idx, first_col])
                        else ""
                    )
                    l_val = (
                        str(master_df.at[idx, last_col]).strip()
                        if last_col and pd.notna(master_df.at[idx, last_col])
                        else ""
                    )

                    # If full name is empty but there is first/last, construct it
                    if not full_val and (f_val or l_val):
                        master_df.at[idx, full_col] = " ".join([p for p in [f_val, l_val] if p])

                    # If there is full name but missing first/last, split it
                    elif full_val and not (f_val and l_val):
                        parts = full_val.split(maxsplit=1)
                        if len(parts) == 2 and first_col and last_col:
                            master_df.at[idx, first_col] = parts[0]
                            master_df.at[idx, last_col] = parts[1]
                        elif len(parts) == 1:
                            if last_col:  # Single word goes to last name
                                master_df.at[idx, last_col] = parts[0]
                            if first_col:
                                master_df.at[idx, first_col] = ""

        # Apply column mapping if specified
        master_copy = master_df.copy()
        if column_map and target_file in column_map:
            invert_map = {v: k for k, v in column_map[target_file].items()}
            master_copy.rename(columns=invert_map, inplace=True)

        # Check target name columns
        target_has_full = any(unify_column_name(col) == "full_name" for col in target_df.columns)
        target_has_first = any(unify_column_name(col) == "first_name" for col in target_df.columns)
        target_has_last = any(unify_column_name(col) == "last_name" for col in target_df.columns)

        # Handle name columns based on target structure
        if target_has_full and not (target_has_first or target_has_last):
            # Target only has full name - combine first/last in master if needed
            combine_first_last_into_full(master_copy)

            # Map to the exact full name column name used in target
            full_col_target = next(c for c in target_df.columns if unify_column_name(c) == "full_name")
            full_col_master = next((c for c in master_copy.columns if unify_column_name(c) == "full_name"), None)

            if full_col_master and full_col_master != full_col_target:
                master_copy[full_col_target] = master_copy[full_col_master]
                master_copy.drop(columns=[full_col_master], inplace=True)

            # Remove any first/last name columns if force_single is enabled
            if force_single:
                for col in list(master_copy.columns):
                    if unify_column_name(col) in ["first_name", "last_name"]:
                        master_copy.drop(columns=[col], inplace=True)

        elif (target_has_first or target_has_last) and not target_has_full:
            # Target only has separate name fields - split full name in master if needed
            split_full_into_first_last(master_copy)

            # Map to exact column names used in target
            if target_has_first:
                first_col_target = next(c for c in target_df.columns if unify_column_name(c) == "first_name")
                first_col_master = next((c for c in master_copy.columns if unify_column_name(c) == "first_name"), None)
                if first_col_master and first_col_master != first_col_target:
                    master_copy[first_col_target] = master_copy[first_col_master]
                    if first_col_master != "First Name":  # Don't drop standard column names
                        master_copy.drop(columns=[first_col_master], inplace=True)

            if target_has_last:
                last_col_target = next(c for c in target_df.columns if unify_column_name(c) == "last_name")
                last_col_master = next((c for c in master_copy.columns if unify_column_name(c) == "last_name"), None)
                if last_col_master and last_col_master != last_col_target:
                    master_copy[last_col_target] = master_copy[last_col_master]
                    if last_col_master != "Last Name":  # Don't drop standard column names
                        master_copy.drop(columns=[last_col_master], inplace=True)

            # Remove full name column if force_single is not enabled and target doesn't have it
            if not force_single:
                for col in list(master_copy.columns):
                    if unify_column_name(col) == "full_name":
                        master_copy.drop(columns=[col], inplace=True)

        # Prepare new rows that match target's column structure
        new_rows = []
        for _, row in master_copy.iterrows():
            new_row = {}
            for tcol in target_df.columns:
                # Find corresponding column in master by unified name
                mcol = next((c for c in master_copy.columns if unify_column_name(c) == unify_column_name(tcol)), None)
                if mcol:
                    new_row[tcol] = row[mcol]
                else:
                    new_row[tcol] = ""
            new_rows.append(new_row)

        # Create dataframe with new rows and append to target
        if new_rows:
            new_df = pd.DataFrame(new_rows, columns=target_df.columns)
            target_df = pd.concat([target_df, new_df], ignore_index=True)

        # Remove duplicates and write back to file
        target_df.drop_duplicates(inplace=True)
        write_csv_or_excel(target_df, target_file)
