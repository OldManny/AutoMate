from datetime import datetime
import json
import os
import shutil

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
        raise ValueError("No files were moved. Nothing to undo.")


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
        raise ValueError("No files were moved. Nothing to undo.")


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
        raise ValueError("No files were moved. Nothing to undo.")


def undo_last_operation():
    """
    Reverts the last file organization operation by using the operation log.
    Ensures files are moved back to their original locations and removes empty folders.
    """
    if not os.path.exists(LOG_FILE):
        raise ValueError("No operation log found. Nothing to undo.")

    # Load the operation log
    with open(LOG_FILE, "r") as log_file:
        log_data = json.load(log_file)

    # Retrieve operations and folders from the log
    operation_log = log_data.get("operations", [])
    folders_to_remove = log_data.get("folders", [])

    # Undo each operation by moving files back to their original locations
    for entry in reversed(operation_log):
        original_path = entry["original"]
        new_path = entry["new"]

        # Move file back to original location if it exists
        if os.path.exists(new_path):
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(new_path, original_path)

    # Clean up empty folders
    for folder in folders_to_remove:
        if os.path.exists(folder) and not os.listdir(folder):  # Check if folder is empty
            os.rmdir(folder)

    # Remove the log file after successful undo
    os.remove(LOG_FILE)
