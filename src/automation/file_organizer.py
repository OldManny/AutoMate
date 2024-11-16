import os
import shutil


def sort_by_type(source_directory):
    """
    Organizes files in the specified directory by type into subdirectories.

    Parameters:
        source_directory (str): Path to the directory to organize.

    """
    # Define the file type categories and their respective extensions
    type_directories = {
        "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"],
        "documents": [
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".rtf",
            ".odt",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
        ],
        "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac"],
        "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
        "archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
        "others": [],  # Catch-all category for unrecognized file types
    }

    # Check if the source directory exists
    if not os.path.exists(source_directory):
        raise ValueError(f"Source directory '{source_directory}' does not exist")

    # Traverse the directory tree
    for root, _, files in os.walk(source_directory):
        for file in files:
            file_path = os.path.join(root, file)  # Full path of the file
            file_ext = os.path.splitext(file)[
                1
            ].lower()  # Extract and lowercase the file extension
            moved = False  # Flag to track if the file has been moved

            # Check and move file to the appropriate type subdirectory
            for dir_name, extensions in type_directories.items():
                if file_ext in extensions:
                    target_dir = os.path.join(
                        source_directory, dir_name
                    )  # Target subdirectory
                    os.makedirs(
                        target_dir, exist_ok=True
                    )  # Create directory if it doesn't exist
                    shutil.move(
                        file_path, os.path.join(target_dir, file)
                    )  # Move the file
                    moved = True
                    break

            # If file type does not match any category, move to "others"
            if not moved:
                target_dir = os.path.join(source_directory, "others")
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(file_path, os.path.join(target_dir, file))  # Move the file
