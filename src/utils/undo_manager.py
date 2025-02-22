import json
import os
import shutil
import zipfile

# Define a log file for storing information about data operations
LOG_FILE = "operation_log.json"


def log_operation(operation, master_file, backup_info):
    """
    Logs the operation performed.
    - For `merge_data`, `backup_info` is a single backup file path (string).
    - For `mirror_data`, `backup_info` is a dictionary mapping target_file -> backup_file.
    """
    log_data = {
        "operation": operation,
        "master_file": master_file,
        "backup_file": backup_info if operation == "merge_data" else None,
        "backups": backup_info if operation == "mirror_data" else None,
    }
    with open(LOG_FILE, "w") as log_f:
        json.dump(log_data, log_f)


def undo_file_operation():
    """
    Reverts the last file organization operation using the stored operation log.
    - Moves files back to their original locations.
    - Deletes any folders or archives created during the process.
    """
    if not os.path.exists(LOG_FILE):
        raise ValueError("Nothing to undo")

    with open(LOG_FILE, "r") as log_file:
        log_data = json.load(log_file)

    # Retrieve stored operation details
    operations = log_data.get("operations", [])
    compressed_archive = log_data.get("compressed_archive", None)
    file_timestamps = log_data.get("file_timestamps", {})
    created_folder = log_data.get("created_folder", None)

    if compressed_archive:
        # Undo compression by extracting the archive
        with zipfile.ZipFile(compressed_archive, 'r') as zipf:
            zipf.extractall(os.path.dirname(compressed_archive))

        # Restore original file timestamps
        for file_path, (atime, mtime) in file_timestamps.items():
            if os.path.exists(file_path):
                os.utime(file_path, (atime, mtime))

        # Remove the compressed archive
        if os.path.exists(compressed_archive):
            os.remove(compressed_archive)

    elif created_folder:
        # Undo backup by removing the created folder
        if os.path.exists(created_folder):
            shutil.rmtree(created_folder)

    elif operations:
        # Handle undo for sorting or other file operations
        folders_to_check = set()

        for entry in reversed(operations):
            original_path = entry["original"]
            new_path = entry.get("new", None)

            if new_path and os.path.exists(new_path):
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                shutil.move(new_path, original_path)
                folders_to_check.add(os.path.dirname(new_path))

        # Remove any empty folders created during the process
        for folder in folders_to_check:
            if os.path.exists(folder) and not os.listdir(folder):
                os.rmdir(folder)

    # Delete the log file after a successful undo
    os.remove(LOG_FILE)


def undo_data_operation():
    """
    Reverts the last merge or mirror operation using the backup files.
    - For `merge_data`, restores the master file from its backup.
    - For `mirror_data`, restores each target file from its respective backup.
    """
    if not os.path.exists(LOG_FILE):
        raise ValueError("Nothing to undo")

    with open(LOG_FILE, "r") as log_f:
        log_data = json.load(log_f)

    operation = log_data.get("operation")
    master_file = log_data.get("master_file")

    if operation == "merge_data":
        # Restore master file from its backup
        backup = log_data.get("backup_file") or log_data.get("backups")
        if master_file and backup and os.path.exists(backup):
            shutil.copy(backup, master_file)
            os.remove(backup)
        else:
            raise ValueError("No valid backup found for merge operation.")

    elif operation == "mirror_data":
        # Restore each mirrored file from its respective backup
        backups = log_data.get("backups")
        if backups and isinstance(backups, dict):
            for target, backup in backups.items():
                if os.path.exists(backup):
                    shutil.copy(backup, target)
                    os.remove(backup)
        else:
            raise ValueError("No valid backups found for mirror operation.")

    else:
        raise ValueError("Unrecognized operation type.")

    # Remove the log file after successful restoration
    os.remove(LOG_FILE)


def clear_previous_log():
    """
    Removes the previous operation log and associated backup files.
    - If an old backup exists, it gets deleted to prevent unnecessary storage.
    """
    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, "r") as log_f:
        old_log_data = json.load(log_f)

    old_op = old_log_data.get("operation")

    if old_op == "merge_data":
        # Remove backup for merge_data operation
        old_backup = old_log_data.get("backup_file") or old_log_data.get("backups")
        if old_backup and os.path.exists(old_backup):
            os.remove(old_backup)

    elif old_op == "mirror_data":
        # Remove backups for mirror_data operation
        old_backups = old_log_data.get("backups")
        if old_backups and isinstance(old_backups, dict):
            for _, backup_path in old_backups.items():
                if os.path.exists(backup_path):
                    os.remove(backup_path)

    # Delete the log file
    os.remove(LOG_FILE)
