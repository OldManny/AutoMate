import argparse
import atexit
import multiprocessing
import os
import subprocess
import sys

from PyQt5.QtCore import QCoreApplication, QSize, QStandardPaths, Qt
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Set application and organization names
ORGANIZATION_NAME = "AutoMate"
APPLICATION_NAME = "AutoMate"
QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
QCoreApplication.setApplicationName(APPLICATION_NAME)

# Define standard directories and create them if needed
APP_DATA_DIR = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
TEMP_DIR = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
os.makedirs(APP_DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Define file and directory paths based on standard locations
LOCK_FILE_PATH = os.path.join(TEMP_DIR, "automate_daemon.lock")
USER_DATA_FILE_PATH = os.path.join(APP_DATA_DIR, "user_data.json")
LAST_TOKEN_FILE_PATH = os.path.join(APP_DATA_DIR, "last_token.txt")
SCHEDULED_JOBS_FILE_PATH = os.path.join(APP_DATA_DIR, "scheduled_jobs.json")
OPERATION_LOG_FILE_PATH = os.path.join(APP_DATA_DIR, "operation_log.json")
ATTACHMENTS_BASE_DIR_PATH = os.path.join(APP_DATA_DIR, "scheduled_attachments")
DAEMON_LOG_FILE_TEMPLATE = os.path.join(TEMP_DIR, "automate_daemon_temp_{timestamp}.log")

from src.automation.scheduler import logging_config, scheduler_manager  # noqa: E402
from src.automation.scheduler.scheduler_manager import SchedulerManager  # noqa: E402
from src.ui.modals.running_modal import RunningJobsModal  # noqa: E402
from src.ui.style import MAIN_WINDOW_STYLE, NAV_BUTTON_STYLE, SIDEBAR_STYLE  # noqa: E402
from src.ui.views.data_view import DataView  # noqa: E402
from src.ui.views.email_view import EmailView  # noqa: E402
from src.ui.views.file_view import FileView  # noqa: E402
from src.ui.views.login_view import LoginView  # noqa: E402
from src.utils import undo_manager  # noqa: E402
from src.utils.auth import clear_last_token_file  # noqa: E402
from src.utils.auth import clear_remember_me_token  # noqa: E402
from src.utils.auth import generate_remember_me_token  # noqa: E402
from src.utils.auth import get_user_by_token  # noqa: E402
from src.utils.auth import load_last_token  # noqa: E402
from src.utils.auth import load_user_data  # noqa: E402
from src.utils.auth import save_last_token  # noqa: E402; noqa: E402
from src.utils.resources import resource_path  # noqa: E402

# Global variable to track the daemon process launched by the GUI
daemon_process = None


def configure_paths():
    """Set module-level path variables for scheduler_manager, undo_manager, and logging_config."""
    scheduler_manager.DEFAULT_JOBS_FILE = SCHEDULED_JOBS_FILE_PATH
    scheduler_manager.ATTACHMENTS_BASE_DIR = ATTACHMENTS_BASE_DIR_PATH
    undo_manager.LOG_FILE = OPERATION_LOG_FILE_PATH
    logging_config.TEMP_DIR = TEMP_DIR


def cleanup_lock_file():
    """Remove the daemon lock file on exit if it exists."""
    try:
        if os.path.exists(LOCK_FILE_PATH):
            os.remove(LOCK_FILE_PATH)
    except OSError:
        pass
    except Exception:
        pass


class MainApp(QMainWindow):
    """Main application window for AutoMate with a sidebar and multiple pages."""

    def __init__(self, scheduler_manager):
        super().__init__()
        self.setFixedSize(588, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        self.scheduler_manager = scheduler_manager
        self.logged_in = False
        self.current_user = ""

        self.initUI()
        self.login_view = LoginView()
        self.stacked_widget.insertWidget(0, self.login_view)
        self.login_view.login_success.connect(self.on_login_success)
        self.launch_daemon_if_needed()
        self.check_remembered_user()

    def initUI(self):
        """Set up the main interface layout with a sidebar and content area."""
        self.setWindowTitle("")
        self.center()

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self.create_sidebar()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 250))
        self.sidebar.setGraphicsEffect(shadow)
        self.sidebar.setVisible(False)
        main_layout.addWidget(self.sidebar)

        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.create_file_organizer_page())
        self.stacked_widget.addWidget(self.create_email_page())
        self.stacked_widget.addWidget(self.create_data_entry_page())
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(self.content_area)

        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)
        self.setCentralWidget(main_widget)

    def launch_daemon_if_needed(self):
        """Launch the daemon subprocess without managing the lock file."""
        global daemon_process
        try:
            daemon_stdout_log = os.path.join(APP_DATA_DIR, "daemon_stdout.log")
            daemon_stderr_log = os.path.join(APP_DATA_DIR, "daemon_stderr.log")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            daemon_script_path = os.path.join(current_dir, "daemon.py")
            if not os.path.exists(daemon_script_path):
                return

            args = [sys.executable, daemon_script_path]
            kwargs = {}
            if sys.platform == "win32":
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            stdout_handle = open(daemon_stdout_log, 'w')
            stderr_handle = open(daemon_stderr_log, 'w')
            kwargs['stdout'] = stdout_handle
            kwargs['stderr'] = stderr_handle

            daemon_process = subprocess.Popen(args, **kwargs)
        except Exception:
            if 'stdout_handle' in locals() and not stdout_handle.closed:
                stdout_handle.close()
            if 'stderr_handle' in locals() and not stderr_handle.closed:
                stderr_handle.close()

    def create_sidebar(self):
        """Create the sidebar with navigation buttons and additional options."""
        sidebar = QWidget()
        sidebar.setFixedWidth(151)
        sidebar.setStyleSheet(SIDEBAR_STYLE)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 30, 0, 30)
        layout.setSpacing(0)

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        nav_buttons = [
            ("Files", 1, "assets/icons/file.png"),
            ("Email", 2, "assets/icons/email.png"),
            ("Data", 3, "assets/icons/data.png"),
        ]
        for text, index, icon_path in nav_buttons:
            btn = self.create_nav_button(text, icon_path)
            btn.setCheckable(True)
            self.nav_button_group.addButton(btn)
            btn.clicked.connect(lambda checked, idx=index: self.on_nav_button_clicked(idx))
            layout.addWidget(btn)

        first_button = self.nav_button_group.buttons()[0]
        first_button.setChecked(True)

        layout.addStretch()
        auto_btn = self.create_nav_button("Schedule", "assets/icons/schedule.png")
        auto_btn.clicked.connect(self.open_schedule_modal)
        layout.addWidget(auto_btn)

        running_btn = self.create_nav_button("Running", "assets/icons/running.png")
        running_btn.clicked.connect(self.open_running_modal)
        layout.addWidget(running_btn)

        logout_btn = self.create_nav_button("Logout", "assets/icons/logout.png")
        logout_btn.clicked.connect(self.on_logout_clicked)
        layout.addWidget(logout_btn)

        return sidebar

    def create_nav_button(self, text, icon_path):
        """Create a styled navigation button with an optional icon."""
        button = QPushButton(text)
        icon_path_absolute = resource_path(icon_path)
        if os.path.exists(icon_path_absolute):
            icon = QIcon(icon_path_absolute)
            button.setIcon(icon)
            button.setIconSize(QSize(29, 29))
            button.setFixedHeight(50)
            button.setText("  " + text)
        button.setStyleSheet(NAV_BUTTON_STYLE)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def on_nav_button_clicked(self, index):
        """Switch to the selected page if the user is logged in."""
        if not self.logged_in:
            self.stacked_widget.setCurrentIndex(0)
            return
        self.stacked_widget.setCurrentIndex(index)

    def open_schedule_modal(self):
        """Open the scheduling modal for dialog views."""
        if not self.logged_in:
            self.stacked_widget.setCurrentIndex(0)
            return

        current_widget = self.stacked_widget.currentWidget()
        if isinstance(current_widget, QWidget):
            file_organizer = current_widget.findChild(QWidget, "FileOrganizerWidget")
            if file_organizer:
                file_organizer.open_schedule_modal()
                return
            email_view = current_widget.findChild(QWidget, "EmailView")
            if email_view:
                email_view.open_schedule_modal()
                return
            data_view = current_widget.findChild(QWidget, "DataView")
            if data_view:
                data_view.open_schedule_modal()
                return

    def open_running_modal(self):
        """Open the RunningJobsModal if the user is logged in."""
        if not self.logged_in:
            self.stacked_widget.setCurrentIndex(0)
            return
        running_modal = RunningJobsModal(scheduler_manager=self.scheduler_manager, parent=self)
        running_modal.exec_()

    def create_file_organizer_page(self):
        """Create the file organizer page."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        file_organizer = FileView(parent=self, scheduler_manager=self.scheduler_manager)
        file_organizer.setObjectName("FileOrganizerWidget")
        layout.addWidget(file_organizer)
        return container

    def closeEvent(self, event):
        """Gracefully shut down the scheduler on application exit."""
        if self.scheduler_manager:
            try:
                self.scheduler_manager.shutdown()
            except Exception:
                pass
        super().closeEvent(event)

    def create_email_page(self):
        """Create the email page."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        email_view = EmailView(parent=self, scheduler_manager=self.scheduler_manager)
        email_view.setObjectName("EmailView")
        layout.addWidget(email_view)
        return container

    def create_data_entry_page(self):
        """Create the Data Entry page."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        data_view = DataView(parent=self, scheduler_manager=self.scheduler_manager)
        data_view.setObjectName("DataView")
        layout.addWidget(data_view)
        return container

    def center(self):
        """Center the main application window on the screen."""
        qr = self.frameGeometry()
        cp = QCoreApplication.instance().desktop().screenGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def check_remembered_user(self):
        """Check for a valid 'remember me' token to bypass login."""
        token = load_last_token()
        user_email = get_user_by_token(token) if token else None

        if user_email:
            self.current_user = user_email
            self.logged_in = True
            self.sidebar.setVisible(True)
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.logged_in = False
            self.sidebar.setVisible(False)
            self.stacked_widget.setCurrentIndex(0)
            self.current_user = ""
            clear_last_token_file()

    def on_login_success(self, email):
        """Handle successful login and token management."""
        data = load_user_data()
        token = ""
        should_remember = self.login_view.remember_me_checkbox.isChecked()

        for user in data["users"]:
            if user["email"].lower() == email.lower():
                if should_remember and not user.get("remember_me_token"):
                    token = generate_remember_me_token(email)
                elif should_remember:
                    token = user.get("remember_me_token", "")
                else:
                    clear_remember_me_token(email)
                    token = ""
                break

        if token and should_remember:
            save_last_token(token)
        else:
            clear_last_token_file()

        self.current_user = email
        self.logged_in = True
        self.sidebar.setVisible(True)
        self.launch_daemon_if_needed()
        self.stacked_widget.setCurrentIndex(1)

    def on_logout_clicked(self):
        """Log out the user, clear stored tokens, and reset the UI."""
        clear_last_token_file()
        if self.current_user:
            clear_remember_me_token(self.current_user)
        if hasattr(self, 'login_view'):
            self.login_view.email_input_login.setText("")
            self.login_view.password_input_login.setText("")
            self.login_view.remember_me_checkbox.setChecked(False)

        self.logged_in = False
        self.current_user = ""
        if hasattr(self, 'sidebar'):
            self.sidebar.setVisible(False)
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.setCurrentIndex(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoMate Application or Daemon.")
    parser.add_argument('--daemon', action='store_true', help='Run in background daemon mode.')
    args = parser.parse_args()

    # Define placeholders for path variables (to be set later)
    APP_DATA_DIR = None
    TEMP_DIR = None
    LOCK_FILE_PATH = None
    USER_DATA_FILE_PATH = None
    LAST_TOKEN_FILE_PATH = None
    SCHEDULED_JOBS_FILE_PATH = None
    OPERATION_LOG_FILE_PATH = None
    ATTACHMENTS_BASE_DIR_PATH = None

    if args.daemon:
        multiprocessing.freeze_support()
        daemon_app_instance = QCoreApplication(sys.argv if hasattr(sys, 'argv') else [''])
        QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
        QCoreApplication.setApplicationName(APPLICATION_NAME)

        APP_DATA_DIR = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        TEMP_DIR = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)

        LOCK_FILE_PATH = os.path.join(TEMP_DIR, "automate_daemon.lock")
        USER_DATA_FILE_PATH = os.path.join(APP_DATA_DIR, "user_data.json")
        LAST_TOKEN_FILE_PATH = os.path.join(APP_DATA_DIR, "last_token.txt")
        SCHEDULED_JOBS_FILE_PATH = os.path.join(APP_DATA_DIR, "scheduled_jobs.json")
        OPERATION_LOG_FILE_PATH = os.path.join(APP_DATA_DIR, "operation_log.json")
        ATTACHMENTS_BASE_DIR_PATH = os.path.join(APP_DATA_DIR, "scheduled_attachments")

        from daemon import run_daemon  # noqa: E402

        configure_paths()

        if os.path.exists(LOCK_FILE_PATH):
            sys.exit(1)

        try:
            with open(LOCK_FILE_PATH, "w") as f:
                f.write(str(os.getpid()))
            atexit.register(cleanup_lock_file)
            run_daemon()
        except Exception:
            cleanup_lock_file()
            sys.exit(1)
        finally:
            cleanup_lock_file()
        sys.exit(0)
    else:
        multiprocessing.freeze_support()
        app = QApplication(sys.argv)
        QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
        QCoreApplication.setApplicationName(APPLICATION_NAME)

        APP_DATA_DIR = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        TEMP_DIR = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)

        LOCK_FILE_PATH = os.path.join(TEMP_DIR, "automate_daemon.lock")
        USER_DATA_FILE_PATH = os.path.join(APP_DATA_DIR, "user_data.json")
        LAST_TOKEN_FILE_PATH = os.path.join(APP_DATA_DIR, "last_token.txt")
        SCHEDULED_JOBS_FILE_PATH = os.path.join(APP_DATA_DIR, "scheduled_jobs.json")
        OPERATION_LOG_FILE_PATH = os.path.join(APP_DATA_DIR, "operation_log.json")
        ATTACHMENTS_BASE_DIR_PATH = os.path.join(APP_DATA_DIR, "scheduled_attachments")

        configure_paths()

        font_path_relative = "assets/fonts/Poppins-Medium.ttf"
        font_path_absolute = resource_path(font_path_relative)
        font_id = QFontDatabase.addApplicationFont(font_path_absolute)
        if font_id == -1:
            app.setFont(QFont("Arial", 10 if sys.platform == "win32" else 13))
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app.setFont(QFont(font_family, 10 if sys.platform == "win32" else 13))

        try:
            gui_scheduler_manager = SchedulerManager(jobs_file=SCHEDULED_JOBS_FILE_PATH, start_scheduler=False)
        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)

        import inspect  # noqa: E402

        try:
            init_signature = inspect.signature(MainApp.__init__)
        except Exception:
            pass

        try:
            main_window = MainApp(scheduler_manager=gui_scheduler_manager)
            main_window.show()
            exit_code = app.exec_()
            sys.exit(exit_code)
        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)
