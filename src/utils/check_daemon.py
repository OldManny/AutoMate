import os
import sys


def check_daemon_running(lock_file_path):
    """
    Check if the daemon is actually running by validating the process ID in the lock file.
    Returns True if a valid daemon process is running, False otherwise.
    """
    if not os.path.exists(lock_file_path):
        return False

    try:
        with open(lock_file_path, 'r') as f:
            pid = int(f.read().strip())

        # Check if the process with this PID exists
        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            process = kernel32.OpenProcess(1, False, pid)
            if process:
                kernel32.CloseHandle(process)
                return True
            return False
        else:
            # Unix-like systems
            os.kill(pid, 0)  # This doesn't actually kill the process, just checks if it exists
            return True
    except (ValueError, OSError):
        # Process doesn't exist or we can't read the file properly
        # Safe to remove the orphaned lock file
        try:
            os.remove(lock_file_path)
        except OSError:
            pass
        return False
