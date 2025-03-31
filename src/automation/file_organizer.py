from datetime import datetime
import hashlib
import json
import os
import shutil
import sys
import zipfile

from src.utils import undo_manager


def _write_log(log_data, function_name):
    """Internal helper to write log data, ensuring path is used."""
    log_file_path = undo_manager.LOG_FILE
    if not log_file_path:
        print(f"ERROR: LOG_FILE path not configured in undo_manager for {function_name}", file=sys.stderr)
        raise RuntimeError(f"Operation log path not configured for {function_name}.")
    try:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, "w") as log_file:
            json.dump(log_data, log_file)
        print(f"[DEBUG {function_name}] Successfully wrote log to {log_file_path}")
    except Exception as e:
        print(f"Error writing operation log to {log_file_path} in {function_name}: {e}", file=sys.stderr)
        raise  # Re-raise the exception


def sort_by_type(source_directory, **kwargs):
    """
    Organizes files in the specified directory by type into subdirectories and logs changes for undo.
    """
    kwargs.get('task_type', None)

    type_directories = {
        "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"],
        "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
        "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac"],
        "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
        "archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
    }

    # Check if the specified directory exists
    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    operation_log = []  # Log file movements
    folders_created = set()  # Track folders to be created

    # Traverse the directory to locate and categorize files
    for root, _, files in os.walk(source_directory, topdown=True):
        for file in files:
            if file.startswith("."):  # Skip hidden files
                continue

            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()

            for dir_name, extensions in type_directories.items():
                if file_ext in extensions:
                    target_dir = os.path.join(source_directory, dir_name)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                        folders_created.add(target_dir)

                    new_path = os.path.join(target_dir, file)
                    shutil.move(file_path, new_path)

                    # Log the operation for undo functionality
                    operation_log.append({"original": file_path, "new": new_path})
                    break

    if operation_log:
        log_data = {"operations": operation_log, "folders": list(folders_created)}
        _write_log(log_data, "sort_by_type")
    else:
        # Raise error only if nothing was moved/logged
        raise ValueError("Nothing to undo")


def sort_by_date(source_directory, **kwargs):
    """
    Organizes files in the specified directory by last modification date into subdirectories and logs changes for undo.
    """
    kwargs.get('task_type', None)

    # Check if the specified directory exists
    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    operation_log = []  # Log file movements
    folders_to_create = set()  # Track folders to be created

    for root, dirs, files in os.walk(source_directory, topdown=True):
        # Exclude hidden directories from traversal
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.startswith('.'):
                continue  # Skip hidden files

            file_path = os.path.join(root, file)

            # Get the modification date of the file
            mod_time = os.path.getmtime(file_path)
            mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")  # Format as YYYY-MM-DD

            # Determine the target directory based on the modification date
            target_dir = os.path.join(source_directory, mod_date)

            # Check if the file needs to be moved
            source_abs_path = os.path.abspath(file_path)
            target_abs_path = os.path.abspath(os.path.join(target_dir, file))

            if source_abs_path != target_abs_path:
                # Create the directory if not already created
                if target_dir not in folders_to_create and not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    folders_to_create.add(target_dir)

                new_path = os.path.join(target_dir, file)
                shutil.move(file_path, new_path)

                # Log the operation
                operation_log.append({"original": file_path, "new": new_path})

    if operation_log:
        log_data = {"operations": operation_log, "folders": list(folders_to_create)}
        _write_log(log_data, "sort_by_date")
    else:
        raise ValueError("Nothing to undo")


def sort_by_size(source_directory, **kwargs):
    """
    Organizes files in the specified directory by size into subdirectories and logs changes for undo.
    """
    kwargs.get('task_type', None)

    # Check if the specified directory exists
    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    # Define size categories (in bytes)
    size_categories = {
        "small": 1 * 1024 * 1024,  # Files <= 1 MB
        "medium": 10 * 1024 * 1024,  # Files > 1 MB and <= 10 MB
        "large": float("inf"),  # Files > 10 MB
    }

    operation_log = []  # Log file movements
    folders_to_create = set()  # Track folders to be created

    # Traverse the directory to locate and categorize files
    for root, _, files in os.walk(source_directory, topdown=True):
        for file in files:
            if file.startswith("."):  # Skip hidden files
                continue

            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)  # Get file size in bytes

            # Determine the target category based on size
            target_category = None
            if file_size <= size_categories["small"]:
                target_category = "small"
            elif file_size <= size_categories["medium"]:
                target_category = "medium"
            else:
                target_category = "large"

            # Target directory based on size category
            target_dir = os.path.join(source_directory, target_category)
            new_path = os.path.join(target_dir, file)

            # Only move the file if it's not already in the correct folder
            if file_path != new_path:
                # Create the directory if not already created
                if target_dir not in folders_to_create and not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    folders_to_create.add(target_dir)

                # Move the file to the target directory
                shutil.move(file_path, new_path)

                # Log the operation for Undo functionality
                operation_log.append({"original": file_path, "new": new_path})

    # Save the operation log to a JSON file
    if operation_log:
        log_data = {"operations": operation_log, "folders": list(folders_to_create)}
        _write_log(log_data, "sort_by_size")
    else:
        raise ValueError("Nothing to undo")


def detect_duplicates(source_directory, **kwargs):
    """
    Identifies and moves duplicate files in the specified directory into a 'duplicates' folder.
    Logs changes for undo functionality.
    """
    kwargs.get('task_type', None)

    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    # Dictionary to track files by hash
    file_hashes = {}
    operation_log = []  # Log of moved files
    duplicates_folder = os.path.join(source_directory, "duplicates")
    duplicates_folder_created = False

    for root, _, files in os.walk(source_directory, topdown=True):
        # Skip hidden files
        for file in files:
            if file.startswith("."):  # Skip hidden files
                continue

            file_path = os.path.join(root, file)

            # Compute the hash of the file
            file_hash = hash_file(file_path)

            if file_hash in file_hashes:
                # If duplicate is found, move it to the duplicates folder
                if not os.path.exists(duplicates_folder):
                    os.makedirs(duplicates_folder)
                new_path = os.path.join(duplicates_folder, file)
                shutil.move(file_path, new_path)

                # Log the operation for Undo functionality
                operation_log.append({"original": file_path, "new": new_path})
            else:
                # Add the file to the hash dictionary
                file_hashes[file_hash] = file_path

    # Write the operation log to a JSON file
    if operation_log:
        # Pass folder only if created *by this operation* for undo cleanup
        log_data = {"operations": operation_log, "folders": [duplicates_folder] if duplicates_folder_created else []}
        _write_log(log_data, "detect_duplicates")
    else:
        raise ValueError("Nothing to undo")


def hash_file(file_path, **kwargs):
    """
    Computes the SHA256 hash of a file's content.
    """

    kwargs.get('task_type', None)

    BUF_SIZE = 65536  # Read in chunks of 64KB
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(BUF_SIZE):
            sha256.update(chunk)

    return sha256.hexdigest()


def rename_files(source_directory, **kwargs):
    """
    Renames files in the specified directory by appending a timestamp
    to their names, ensuring uniqueness and logging changes for Undo.
    """

    kwargs.get('task_type', None)

    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    operation_log = []  # List to store renaming operations

    for root, dirs, files in os.walk(source_directory, topdown=True):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.startswith('.'):
                continue  # Skip hidden files

            file_path = os.path.join(root, file)
            file_name, file_ext = os.path.splitext(file)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M")
            new_name = f"{file_name}_{timestamp}{file_ext}"
            new_path = os.path.join(root, new_name)

            os.rename(file_path, new_path)  # Rename the file

            # Log the operation for Undo
            operation_log.append({"original": file_path, "new": new_path})

    # Write the operation log to a JSON file
    if operation_log:
        log_data = {"operations": operation_log}  # No folders created here
        _write_log(log_data, "rename_files")
    else:
        raise ValueError("Nothing to undo")


def compress_files(source_directory, **kwargs):
    """
    Compresses all files in the specified directory into a single ZIP archive,
    removes the original files after compression, and logs changes for Undo.
    """

    kwargs.get('task_type', None)

    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    archive_name = os.path.join(source_directory, "compressed_files.zip")

    # Store file timestamps to preserve them
    file_timestamps = {}

    # Gather files and their timestamps
    for root, _, files in os.walk(source_directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path != archive_name:  # Avoid compressing the archive itself
                stat_info = os.stat(file_path)
                file_timestamps[file_path] = (stat_info.st_atime, stat_info.st_mtime)

    with zipfile.ZipFile(archive_name, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zipf:
        for file_path in file_timestamps.keys():
            arcname = os.path.relpath(file_path, source_directory)  # Relative path for archive
            zipf.write(file_path, arcname)

    # Delete original files after compression
    for file_path in file_timestamps.keys():
        os.remove(file_path)

    # Log the operation
    log_data = {
        "compressed_archive": archive_name,
        "file_timestamps": file_timestamps,
    }
    _write_log(log_data, "compress_files")


def backup_files(source_directory, **kwargs):
    """
    Creates a backup of all files in the specified directory by copying them into
    a timestamped backup folder. Logs the operation for undo functionality.
    """

    kwargs.get('task_type', None)

    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    # Ensure the source directory is not empty
    if not any(file for file in os.listdir(source_directory) if not file.startswith(".")):
        raise ValueError("Nothing to back up")

    # Create a timestamped backup folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_folder = os.path.join(source_directory, f"backup_{timestamp}")

    # Ensure the backup folder itself is not included in the operation
    if os.path.exists(backup_folder):
        raise ValueError(
            "A backup operation has already been performed. Please remove the previous backup folder or choose another directory."
        )

    os.makedirs(backup_folder, exist_ok=True)

    operation_log = []  # Log individual file backups
    backup_folder_created = True  # Track creation

    # Traverse and copy files to the backup folder
    for root, dirs, files in os.walk(source_directory):
        # Skip the backup folder itself during traversal
        dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != os.path.abspath(backup_folder)]

        for file in files:
            if file.startswith("."):  # Skip hidden files
                continue

            source_file = os.path.join(root, file)
            relative_path = os.path.relpath(root, source_directory)
            target_dir = os.path.join(backup_folder, relative_path)
            os.makedirs(target_dir, exist_ok=True)

            target_file = os.path.join(target_dir, file)
            shutil.copy2(source_file, target_file)

            # Log the backup operation
            operation_log.append({"original": source_file, "new": target_file})

    if operation_log:
        log_data = {"operations": operation_log, "created_folder": backup_folder if backup_folder_created else None}
        _write_log(log_data, "backup_files")
    else:
        raise ValueError("Nothing to undo")
