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
            import subprocess

            # Using tasklist to check if the process exists (Windows-specific)
            try:
                output = subprocess.check_output(f'tasklist /FI "PID eq {pid}" /NH', shell=True)
                if str(pid) in str(output):
                    return True
                # Process doesn't exist
                os.remove(lock_file_path)
                return False
            except subprocess.SubprocessError:
                # Fall back to kernel32 method with proper access rights
                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if process:
                    kernel32.CloseHandle(process)
                    return True
                # Process doesn't exist or can't be accessed
                os.remove(lock_file_path)
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
