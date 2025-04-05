import os
import plistlib
import subprocess
import sys

# Windows
if sys.platform == 'win32':
    import winreg

    # Registry key for current user startup
    RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME_REG = "AutoMateDaemon"  # Name for the registry entry

# macOS
elif sys.platform == 'darwin':
    LAUNCH_AGENTS_DIR = os.path.expanduser("~/Library/LaunchAgents")
    PLIST_FILENAME = "com.automateapp.daemon.plist"  # Use a reverse domain name style
    PLIST_PATH = os.path.join(LAUNCH_AGENTS_DIR, PLIST_FILENAME)

# Linux
else:
    AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
    DESKTOP_FILENAME = "automate-daemon.desktop"
    DESKTOP_FILE_PATH = os.path.join(AUTOSTART_DIR, DESKTOP_FILENAME)


def get_daemon_command():
    """
    Determines the command needed to launch the daemon.
    Crucially uses sys.executable which points to the *packaged* application.
    """
    # sys.executable should point to AutoMate.exe (Win), AutoMate.app/.../AutoMate (macOS) etc.
    executable_path = sys.executable
    return [executable_path, "--daemon"]


def enable_startup():
    """Enables the daemon to start on login for the current platform."""
    command_parts = get_daemon_command()
    command_str = subprocess.list2cmdline(command_parts)  # For registry/desktop file

    try:
        if sys.platform == 'win32':
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, APP_NAME_REG, 0, winreg.REG_SZ, command_str)
            winreg.CloseKey(key)
            print(f"Windows startup registry entry added: {APP_NAME_REG}")
            return True

        elif sys.platform == 'darwin':
            os.makedirs(LAUNCH_AGENTS_DIR, exist_ok=True)
            plist_data = {
                "Label": os.path.splitext(PLIST_FILENAME)[0],
                "ProgramArguments": command_parts,
                "RunAtLoad": True,
                "KeepAlive": False,  # Don't automatically restart if it exits
                "StandardOutPath": os.path.join(os.path.expanduser("~"), ".automate_daemon_stdout.log"),
                "StandardErrorPath": os.path.join(os.path.expanduser("~"), ".automate_daemon_stderr.log"),
            }
            with open(PLIST_PATH, "wb") as fp:
                plistlib.dump(plist_data, fp)
            print(f"macOS LaunchAgent file created: {PLIST_PATH}")
            return True

        else:  # Linux (XDG Autostart)
            os.makedirs(AUTOSTART_DIR, exist_ok=True)
            desktop_entry = f"""
                            [Desktop Entry]
                            Type=Application
                            Name=AutoMate Daemon
                            Exec={command_str}
                            Icon=automate # Optional: assumes an icon 'automate' is installed system-wide or locally
                            Comment=Starts the AutoMate background scheduler
                            X-GNOME-Autostart-enabled=true
                            """

            with open(DESKTOP_FILE_PATH, "w") as f:
                f.write(desktop_entry)
            print(f"Linux autostart file created: {DESKTOP_FILE_PATH}")
            return True

    except Exception as e:
        print(f"Error enabling startup on {sys.platform}: {e}", file=sys.stderr)
        return False


def disable_startup():
    """Disables the daemon from starting on login for the current platform."""
    try:
        if sys.platform == 'win32':
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, APP_NAME_REG)
            winreg.CloseKey(key)
            print(f"Windows startup registry entry removed: {APP_NAME_REG}")
            return True

        elif sys.platform == 'darwin':
            if os.path.exists(PLIST_PATH):
                os.remove(PLIST_PATH)
                print(f"macOS LaunchAgent file removed: {PLIST_PATH}")
                return True
            return False  # Already disabled

        else:  # Linux
            if os.path.exists(DESKTOP_FILE_PATH):
                os.remove(DESKTOP_FILE_PATH)
                print(f"Linux autostart file removed: {DESKTOP_FILE_PATH}")
                return True
            return False  # Already disabled

    except FileNotFoundError:
        # Entry/file doesn't exist, so it's already disabled or wasn't set correctly
        print(f"Startup entry not found on {sys.platform}, considered disabled.")
        return True  # Return True as the state is "disabled"
    except Exception as e:
        print(f"Error disabling startup on {sys.platform}: {e}", file=sys.stderr)
        return False


def is_startup_enabled():
    """Checks if the startup entry currently exists."""
    try:
        if sys.platform == 'win32':
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME_REG)
            winreg.CloseKey(key)
            return True
        elif sys.platform == 'darwin':
            return os.path.exists(PLIST_PATH)
        else:  # Linux
            return os.path.exists(DESKTOP_FILE_PATH)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error checking startup status on {sys.platform}: {e}", file=sys.stderr)
        return False
