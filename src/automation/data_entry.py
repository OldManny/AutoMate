import os

import pandas as pd

# Dictionary of column synonyms to standardize naming conventions.
SYNONYMS = {
    "first_name": ["first name", "given name", "fname"],
    "last_name": ["last name", "surname", "family name", "lname"],
    "full_name": ["full name", "complete name", "name"],
    "age": ["age", "years old", "dob (year)"],
    "email": ["email", "email address", "e-mail", "user email"],
    "phone": ["phone number", "phone", "mobile", "cell", "contact number"],
    "address": ["address", "street address", "mailing address", "residence"],
    "city": ["city", "town", "location"],
    "state": ["state", "province", "region"],
    "postal_code": ["postal code", "zip code", "zip", "postcode"],
    "gender": ["gender", "sex", "identity"],
    "company": ["company", "employer", "business name", "organization"],
    "country": ["country", "nation", "nationality"],
    "dob": ["dob", "birthdate", "birthday", "date of birth"],
    "department": ["department", "dept", "division"],
    "job_title": ["job title", "position", "occupation", "role"],
    "marital_status": ["marital status", "family status", "relationship status"],
    "username": ["username", "login name", "user id", "userid"],
    "id": ["id", "identifier", "record id"],
}

# Mappings for display names when presenting standardized column names.
DISPLAY_NAMES = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "full_name": "Full Name",
    "age": "Age",
    "email": "Email",
    "phone": "Phone",
    "address": "Address",
    "city": "City",
    "state": "State",
    "postal_code": "Postal Code",
    "gender": "Gender",
    "company": "Company",
    "country": "Country",
    "dob": "DOB",
    "department": "Department",
    "job_title": "Job Title",
    "marital_status": "Marital Status",
    "username": "Username",
    "id": "ID",
}


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
    if not data_params:
        return

    # Extract parameters
    master_file = data_params.get("master_file")
    other_files = data_params.get("other_files", [])
    column_map = data_params.get("column_map")
    force_single = data_params.get("force_single_name_col", False)

    if not master_file or not os.path.isfile(master_file):
        return

    # Read master file
    master_df = read_csv_or_excel(master_file)

    # Determine name handling strategy based on master file
    has_full_name = any(unify_column_name(col) == "full_name" for col in master_df.columns)
    has_split_names = any(unify_column_name(col) == "first_name" for col in master_df.columns) or any(
        unify_column_name(col) == "last_name" for col in master_df.columns
    )

    # Build master column mapping
    master_mapping = {}
    for col in master_df.columns:
        unified = unify_column_name(col)
        master_mapping[unified] = col

    for f in other_files:
        if not os.path.isfile(f):
            continue

        incoming_df = read_csv_or_excel(f)
        if incoming_df.empty:
            continue

        # Apply explicit column mapping
        if column_map and f in column_map:
            incoming_df.rename(columns=column_map[f], inplace=True)

        # Pre-process name columns to match master file's structure
        if force_single or has_full_name:
            combine_first_last_into_full(incoming_df)
            if force_single:
                # Remove first/last name columns after combining
                for col in list(incoming_df.columns):
                    if unify_column_name(col) in ["first_name", "last_name"]:
                        incoming_df.drop(columns=[col], inplace=True)
        elif has_split_names:
            split_full_into_first_last(incoming_df)

        # Map incoming columns to master columns based on unified names
        col_mapping = {}
        for col in incoming_df.columns:
            unified = unify_column_name(col)
            if unified in master_mapping:
                col_mapping[col] = master_mapping[unified]

        if col_mapping:
            incoming_df.rename(columns=col_mapping, inplace=True)

        # Add any new columns to master
        for col in incoming_df.columns:
            if col not in master_df.columns:
                master_df[col] = ""

        # Append rows while preserving master structure
        new_rows = []
        for _, row in incoming_df.iterrows():
            row_dict = {}
            for col in master_df.columns:
                if col in incoming_df.columns:
                    row_dict[col] = row[col]
                else:
                    row_dict[col] = ""
            new_rows.append(row_dict)

        if new_rows:
            add_df = pd.DataFrame(new_rows, columns=master_df.columns)
            master_df = pd.concat([master_df, add_df], ignore_index=True)

    # Final processing for name columns
    if force_single:
        combine_first_last_into_full(master_df)
        # Remove first/last name columns after combining
        for col in list(master_df.columns):
            if unify_column_name(col) in ["first_name", "last_name"]:
                master_df.drop(columns=[col], inplace=True)

    master_df.drop_duplicates(inplace=True)
    write_csv_or_excel(master_df, master_file)


def mirror_data(source_directory, data_params=None):
    """
    Mirror master file data to targets, properly handling name columns and edge cases.
    """
    if not data_params:
        return

    master_file = data_params.get("master_file")
    other_files = data_params.get("other_files", [])
    column_map = data_params.get("column_map")
    force_single = data_params.get("force_single_name_col", False)

    if not master_file or not os.path.isfile(master_file):
        return

    # Read and unify master file columns
    master_df = read_csv_or_excel(master_file)

    # Check if master has name columns
    master_has_full = any(unify_column_name(col) == "full_name" for col in master_df.columns)
    master_has_first = any(unify_column_name(col) == "first_name" for col in master_df.columns)
    master_has_last = any(unify_column_name(col) == "last_name" for col in master_df.columns)

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

    # Process each target file
    for target_file in other_files:
        if not os.path.isfile(target_file):
            continue

        # Read target file
        target_df = read_csv_or_excel(target_file)

        # Handle empty target file - simply copy master structure and data
        if target_df.empty and target_df.columns.size == 0:
            write_csv_or_excel(master_df.copy(), target_file)
            continue

        # Check target name columns
        target_has_full = any(unify_column_name(col) == "full_name" for col in target_df.columns)
        target_has_first = any(unify_column_name(col) == "first_name" for col in target_df.columns)
        target_has_last = any(unify_column_name(col) == "last_name" for col in target_df.columns)

        # Prepare master data copy for this target
        master_copy = master_df.copy()

        # Apply column mapping if specified
        if column_map and target_file in column_map:
            # Invert the mapping for mirror operation
            invert_map = {v: k for k, v in column_map[target_file].items()}
            master_copy = master_copy.rename(columns=invert_map)

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
