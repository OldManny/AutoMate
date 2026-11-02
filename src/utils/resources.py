import os
import sys


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Check if we're in a Mac app bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
            if os.path.exists(os.path.join(base_path, 'Resources')):
                base_path = os.path.join(base_path, 'Resources')
        else:
            # Development mode
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            # Fallback:
            if not os.path.isdir(base_path):
                base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
