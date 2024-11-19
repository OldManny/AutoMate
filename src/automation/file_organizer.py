import json
import os
import shutil

LOG_FILE = "operation_log.json"


def sort_by_type(source_directory):
    """
    Organizes files in the specified directory by type into subdirectories and logs changes for undo.
    Logs all changes for undo functionality.

    Parameters:
        source_directory (str): Path to the directory to organize.
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

    # Initialize a log list to store operation details
    operation_log = []

    # Traverse the directory to locate and categorize files
    for root, _, files in os.walk(source_directory, topdown=True):
        for file in files:
            file_path = os.path.join(root, file)  # Full path of the file
            file_ext = os.path.splitext(file)[1].lower()  # Extract and lowercase the file extension

            for dir_name, extensions in type_directories.items():
                if file_ext in extensions:  # Check if the file matches the current category
                    target_dir = os.path.join(source_directory, dir_name)  # Target directory for the file
                    os.makedirs(target_dir, exist_ok=True)  # Create the directory if it doesn't exist
                    new_path = os.path.join(target_dir, file)  # Full target path for the file
                    shutil.move(file_path, new_path)  # Move the file to the target directory

                    # Log the operation for undo functionality
                    operation_log.append({"original": file_path, "new": new_path})
                    break

    # Save the operation log to a JSON file
    if operation_log:
        with open(LOG_FILE, "w") as log_file:
            json.dump(operation_log, log_file)
    else:
        raise ValueError("No files were moved. Nothing to undo.")


def undo_last_operation():
    """Reverts the last file organization operation by using the operation log.
    Ensures files are moved back to their original locations and removes empty folders."""

    # Check if the log file exists
    if not os.path.exists(LOG_FILE):
        raise ValueError("No operation log found. Nothing to undo.")

    # Load the operation log from the JSON file
    with open(LOG_FILE, "r") as log_file:
        operation_log = json.load(log_file)

    # Set to track folders to check for cleanup
    folders_to_check = set()

    # Undo each operation by moving files back to their original locations
    for entry in reversed(operation_log):  # Reverse the log to undo the last operations first
        original_path = entry["original"]
        new_path = entry["new"]

        # Check if the moved file still exists
        if os.path.exists(new_path):  # Ensure the moved file exists
            os.makedirs(os.path.dirname(original_path), exist_ok=True)  # Create the original directory if needed
            shutil.move(new_path, original_path)  # Move the file back to its original location

            # Track the folder that contained the file
            folders_to_check.add(os.path.dirname(new_path))

    # Remove empty directories that were created during the organization
    for folder in folders_to_check:
        if os.path.exists(folder) and not os.listdir(folder):  # Ensure folder is empty before removal
            os.rmdir(folder)  # Remove the folder

    # Remove the log file after successful undo
    os.remove(LOG_FILE)
