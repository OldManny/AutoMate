from datetime import datetime
import hashlib
import json
import os
import shutil
import zipfile

LOG_FILE = "operation_log.json"


def sort_by_type(source_directory):
    """
    Organizes files in the specified directory by type into subdirectories and logs changes for undo.
    """
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

    # Save the operation log to a JSON file
    if operation_log:
        with open(LOG_FILE, "w") as log_file:
            json.dump({"operations": operation_log, "folders": list(folders_created)}, log_file)
    else:
        raise ValueError("Nothing to undo")


def sort_by_date(source_directory):
    """
    Organizes files in the specified directory by last modification date into subdirectories and logs changes for undo.
    """

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

    # Write the operation log to a JSON file
    if operation_log:
        with open(LOG_FILE, "w") as log_file:
            json.dump({"operations": operation_log, "folders": list(folders_to_create)}, log_file)
    else:
        raise ValueError("Nothing to undo")


def sort_by_size(source_directory):
    """
    Organizes files in the specified directory by size into subdirectories and logs changes for undo.
    """

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

    # Write the operation log to a JSON file
    if operation_log:
        with open(LOG_FILE, "w") as log_file:
            json.dump({"operations": operation_log, "folders": list(folders_to_create)}, log_file)
    else:
        raise ValueError("Nothing to undo")


def detect_duplicates(source_directory):
    """
    Identifies and moves duplicate files in the specified directory into a 'duplicates' folder.
    Logs changes for undo functionality.
    """
    if not os.path.exists(source_directory):
        raise ValueError(f"The directory '{source_directory}' does not exist.")

    # Dictionary to track files by hash
    file_hashes = {}
    operation_log = []  # Log of moved files
    duplicates_folder = os.path.join(source_directory, "duplicates")

    for root, _, files in os.walk(source_directory, topdown=True):
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
        with open(LOG_FILE, "w") as log_file:
            json.dump({"operations": operation_log, "folders": [duplicates_folder]}, log_file)
    else:
        raise ValueError("Nothing to undo")


def hash_file(file_path):
    """
    Computes the SHA256 hash of a file's content.
    """
    BUF_SIZE = 65536  # Read in chunks of 64KB
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(BUF_SIZE):
            sha256.update(chunk)

    return sha256.hexdigest()


def rename_files(source_directory):
    """
    Renames files in the specified directory by appending a timestamp
    to their names, ensuring uniqueness and logging changes for Undo.
    """
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
        with open(LOG_FILE, "w") as log_file:
            json.dump({"operations": operation_log}, log_file)
    else:
        raise ValueError("Nothing to undo")


def compress_files(source_directory):
    """
    Compresses all files in the specified directory into a single ZIP archive,
    removes the original files after compression, and logs changes for Undo.
    """
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
        "file_timestamps": file_timestamps,  # Log timestamps for restoration
    }
    with open(LOG_FILE, "w") as log_file:
        json.dump(log_data, log_file)


def backup_files(source_directory):
    """
    Creates a backup of all files in the specified directory by copying them into
    a timestamped backup folder. Logs the operation for undo functionality.
    """
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

    # Save the operation log
    if operation_log:
        with open(LOG_FILE, "w") as log_file:
            json.dump({"operations": operation_log, "created_folder": backup_folder}, log_file)
    else:
        raise ValueError("Nothing to undo")


def undo_last_operation():
    """
    Reverts the last file organization operation by using the operation log.
    Ensures files are moved back to their original locations and removes
    any created folders or archives.
    """
    # Check if the log file exists
    if not os.path.exists(LOG_FILE):
        raise ValueError("Nothing to undo")

    # Load the operation log from the JSON file
    with open(LOG_FILE, "r") as log_file:
        log_data = json.load(log_file)

    # Check the type of operation logged
    operations = log_data.get("operations", [])
    compressed_archive = log_data.get("compressed_archive", None)
    file_timestamps = log_data.get("file_timestamps", {})
    created_folder = log_data.get("created_folder", None)

    if compressed_archive:  # Undo Compression
        with zipfile.ZipFile(compressed_archive, 'r') as zipf:
            zipf.extractall(os.path.dirname(compressed_archive))

        # Restore original timestamps
        for file_path, (atime, mtime) in file_timestamps.items():
            if os.path.exists(file_path):
                os.utime(file_path, (atime, mtime))  # Restore access and modification times

        # Remove the compressed archive
        if os.path.exists(compressed_archive):
            os.remove(compressed_archive)

    elif created_folder:  # Undo Backup
        if os.path.exists(created_folder):
            shutil.rmtree(created_folder)  # Remove the entire backup folder

    elif operations:  # Handle Undo for Sorting or Other Operations
        folders_to_check = set()  # Track folders to clean up

        for entry in reversed(operations):  # Undo each operation
            original_path = entry["original"]
            new_path = entry.get("new", None)

            if new_path and os.path.exists(new_path):
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                shutil.move(new_path, original_path)
                folders_to_check.add(os.path.dirname(new_path))

        # Remove empty folders that were created
        for folder in folders_to_check:
            if os.path.exists(folder) and not os.listdir(folder):
                os.rmdir(folder)

    # Remove the log file after successful Undo
    os.remove(LOG_FILE)
