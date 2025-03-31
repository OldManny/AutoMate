import os
import sys


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        # Fallback:
        if not os.path.isdir(base_path):
            base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
