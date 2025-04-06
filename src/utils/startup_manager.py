import os
import plistlib
import subprocess
import sys

# Windows-specific imports and configuration
if sys.platform == 'win32':
    import winreg

    RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME_REG = "AutoMateDaemon"  # Registry entry name

# macOS-specific configuration
elif sys.platform == 'darwin':
    LAUNCH_AGENTS_DIR = os.path.expanduser("~/Library/LaunchAgents")
    PLIST_FILENAME = "com.automateapp.daemon.plist"
    PLIST_PATH = os.path.join(LAUNCH_AGENTS_DIR, PLIST_FILENAME)

# Linux or other UNIX-like systems
else:
    AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
    DESKTOP_FILENAME = "automate-daemon.desktop"
    DESKTOP_FILE_PATH = os.path.join(AUTOSTART_DIR, DESKTOP_FILENAME)


def get_daemon_command():
    """Returns the command to run the daemon depending on packaging."""
    if getattr(sys, 'frozen', False):
        # If the app is packaged, use the executable
        return [sys.executable, "--daemon"]
    else:
        # During development/testing, refer to the Python script
        script_path = os.path.abspath("C:/AutoMate/main_app.py")
        return [sys.executable, script_path, "--daemon"]


def enable_startup():
    """
    Sets up the daemon to run automatically at user login based on the platform.
    Creates a registry key (Windows), LaunchAgent plist (macOS), or .desktop autostart (Linux).
    """
    command_parts = get_daemon_command()
    command_str = subprocess.list2cmdline(command_parts)

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
                "KeepAlive": False,
                "StandardOutPath": os.path.join(os.path.expanduser("~"), ".automate_daemon_stdout.log"),
                "StandardErrorPath": os.path.join(os.path.expanduser("~"), ".automate_daemon_stderr.log"),
            }
            with open(PLIST_PATH, "wb") as fp:
                plistlib.dump(plist_data, fp)
            print(f"macOS LaunchAgent file created: {PLIST_PATH}")
            return True

        else:
            os.makedirs(AUTOSTART_DIR, exist_ok=True)
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name=AutoMate Daemon
Exec={command_str}
Icon=automate
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
    """
    Removes the daemon's startup registration from the system.
    Deletes the registry entry (Windows), plist file (macOS), or .desktop file (Linux).
    """
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
            return False

        else:
            if os.path.exists(DESKTOP_FILE_PATH):
                os.remove(DESKTOP_FILE_PATH)
                print(f"Linux autostart file removed: {DESKTOP_FILE_PATH}")
                return True
            return False

    except FileNotFoundError:
        print(f"Startup entry not found on {sys.platform}, considered disabled.")
        return True
    except Exception as e:
        print(f"Error disabling startup on {sys.platform}: {e}", file=sys.stderr)
        return False


def is_startup_enabled():
    """
    Returns True if a startup registration exists on the current platform.
    Checks registry/plist/.desktop presence depending on OS.
    """
    try:
        if sys.platform == 'win32':
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME_REG)
            winreg.CloseKey(key)
            return True
        elif sys.platform == 'darwin':
            return os.path.exists(PLIST_PATH)
        else:
            return os.path.exists(DESKTOP_FILE_PATH)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error checking startup status on {sys.platform}: {e}", file=sys.stderr)
        return False


# CLI usage for testing or debugging
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python startup_manager.py <enable|disable|status>")
        sys.exit(0)

    action = sys.argv[1].lower()
    if action == "enable":
        result = enable_startup()
        print(f"Enable startup returned: {result}")
    elif action == "disable":
        result = disable_startup()
        print(f"Disable startup returned: {result}")
    elif action == "status":
        result = is_startup_enabled()
        print(f"Startup enabled? {result}")
    else:
        print("Unknown action. Use enable, disable, or status.")
