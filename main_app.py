import os
import sys

from PyQt5.QtCore import QCoreApplication, QSize, Qt
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

from daemon import SchedulerManager
from src.ui.modals.running_modal import RunningJobsModal
from src.ui.style import MAIN_WINDOW_STYLE, NAV_BUTTON_STYLE, SIDEBAR_STYLE
from src.ui.views.data_view import DataView
from src.ui.views.email_view import EmailView
from src.ui.views.file_view import FileView
from src.ui.views.login_view import LoginView
from src.utils.auth import get_user_by_token, load_user_data, save_user_data


class MainApp(QMainWindow):
    """
    Main application window for AutoMate with a sidebar and multiple pages.
    Includes a login page (index 0) and then the normal content pages (1,2,3).
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(588, 600)  # Fixed window size
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)  # Disable maximize button
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        self.scheduler_manager = SchedulerManager(start_scheduler=False)

        # Track the login state
        self.logged_in = False  # Will set to True once user logs in successfully

        # Build the UI
        self.initUI()

        # Create the login page and insert it at index 0
        self.login_view = LoginView()
        self.stacked_widget.insertWidget(0, self.login_view)

        # Listen for successful login
        self.login_view.login_success.connect(self.on_login_success)

        # Check if user is remembered
        self.check_remembered_user()

    def initUI(self):
        """
        Sets up the main interface layout with a sidebar and content area.
        """
        self.setWindowTitle("")
        self.center()

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create the sidebar
        self.sidebar = self.create_sidebar()

        # Add shadow effect to the sidebar
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 250))
        self.sidebar.setGraphicsEffect(shadow)

        # By default, hide the sidebar if not logged in
        self.sidebar.setVisible(False)  # << HIDE on startup

        main_layout.addWidget(self.sidebar)

        # Create content area
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Stack for switching between pages
        self.stacked_widget = QStackedWidget()

        # Insert placeholders for the main pages at indices 1, 2, 3
        self.stacked_widget.addWidget(self.create_file_organizer_page())  # index 1
        self.stacked_widget.addWidget(self.create_email_page())  # index 2
        self.stacked_widget.addWidget(self.create_data_entry_page())  # index 3

        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(self.content_area)

        # Adjust stretch to allocate space between sidebar and content
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        self.setCentralWidget(main_widget)

    def create_sidebar(self):
        """
        Creates the sidebar with navigation buttons and additional options.
        """
        sidebar = QWidget()
        sidebar.setFixedWidth(151)
        sidebar.setStyleSheet(SIDEBAR_STYLE)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 30, 0, 30)
        layout.setSpacing(0)

        # Button group for navigation
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        # Navigation buttons
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

        # Mark the first button (Files) as initially checked
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
        """
        Creates a styled navigation button with an optional icon.
        """
        button = QPushButton(text)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(29, 29))  # Icon size
            button.setFixedHeight(50)
            button.setText("  " + text)  # Add space for text alignment
        button.setStyleSheet(NAV_BUTTON_STYLE)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def on_nav_button_clicked(self, index):
        """
        Switches to the selected page if user is logged in; otherwise do nothing.
        """
        # Restrict the user’s access to the main pages if not logged in
        if not self.logged_in:
            self.stacked_widget.setCurrentIndex(0)  # Force back to login
            return

        self.stacked_widget.setCurrentIndex(index)

    def open_schedule_modal(self):
        """
        Opens the scheduling modal for dialog views.
        """
        if not self.logged_in:
            self.stacked_widget.setCurrentIndex(0)
            return

        current_widget = self.stacked_widget.currentWidget()
        if isinstance(current_widget, QWidget):
            # Check if in the File View
            file_organizer = current_widget.findChild(QWidget, "FileOrganizerWidget")
            if file_organizer:
                file_organizer.open_schedule_modal()
                return

            # Check if in the Email View
            email_view = current_widget.findChild(QWidget, "EmailView")
            if email_view:
                email_view.open_schedule_modal()
                return

            # 3) Check if in the DataEntryView
            data_view = current_widget.findChild(QWidget, "DataView")
            if data_view:
                data_view.open_schedule_modal()
                return

    def open_running_modal(self):
        """
        Opens the RunningJobsModal, if logged in.
        """
        if not self.logged_in:
            self.stacked_widget.setCurrentIndex(0)
            return
        running_modal = RunningJobsModal(scheduler_manager=self.scheduler_manager, parent=self)
        running_modal.exec_()

    def create_file_organizer_page(self):
        """
        Creates the file organizer page.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Pass the shared scheduler_manager to FileView
        file_organizer = FileView(parent=self, scheduler_manager=self.scheduler_manager)
        file_organizer.setObjectName("FileOrganizerWidget")
        layout.addWidget(file_organizer)

        return container

    def closeEvent(self, event):
        # Gracefully shut down the scheduler on app exit
        self.scheduler_manager.shutdown()
        super().closeEvent(event)

    def create_email_page(self):
        """
        Creates the email page with the new EmailView widget.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Pass the shared scheduler_manager to EmailView
        email_view = EmailView(parent=self, scheduler_manager=self.scheduler_manager)
        email_view.setObjectName("EmailView")
        layout.addWidget(email_view)

        return container

    def create_data_entry_page(self):
        """
        Creates the Data Entry page using DataEntryView.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Instantiate your DataEntryView, passing the scheduler if needed
        data_view = DataView(parent=self, scheduler_manager=self.scheduler_manager)
        data_view.setObjectName("DataView")

        layout.addWidget(data_view)

        return container

    def center(self):
        """
        Centers the main application window on the screen.
        """
        qr = self.frameGeometry()
        cp = QCoreApplication.instance().desktop().screenGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def check_remembered_user(self):
        """
        If a 'remember me' token is found in local JSON, skip login and show main app (index 1).
        Otherwise, show login (index 0).
        """
        try:
            with open("last_token.txt", "r") as f:
                token = f.read().strip()
        except FileNotFoundError:
            token = ""

        if token:
            user_email = get_user_by_token(token)
            self.current_user = user_email
            if user_email:
                # Valid user => set self.logged_in and show the "Files" page
                self.logged_in = True
                self.sidebar.setVisible(True)  # Show sidebar
                self.stacked_widget.setCurrentIndex(1)
                return

        # Otherwise, show login
        self.logged_in = False
        self.sidebar.setVisible(False)
        self.stacked_widget.setCurrentIndex(0)
        self.current_user = ""  # no one is logged in yet

    def on_login_success(self, email):
        """
        Called when user logs in or registers successfully.
        """
        # Find the user's token in the JSON
        data = load_user_data()
        token = ""
        for user in data["users"]:
            if user["email"].lower() == email.lower():
                token = user["remember_me_token"]
                break

        if token:
            with open("last_token.txt", "w") as f:
                f.write(token)

        # Store this user as the current user
        self.current_user = email

        # Mark logged_in = True and show sidebar
        self.logged_in = True
        self.sidebar.setVisible(True)

        # Switch to the "Files" page
        self.stacked_widget.setCurrentIndex(1)

    def on_logout_clicked(self):
        """
        Logs the user out, clears any stored token, and shows the login page again.
        """

        # Clear the remember-me token file if it exists
        if os.path.exists("last_token.txt"):
            os.remove("last_token.txt")

        # Clear the token in user_data.json
        if hasattr(self, "current_user") and self.current_user:
            data = load_user_data()
            for user in data["users"]:
                if user["email"].lower() == self.current_user.lower():
                    user["remember_me_token"] = ""
                    break
            save_user_data(data)

        # Clear all login fields and checkboxes
        self.login_view.email_input_login.setText("")
        self.login_view.password_input_login.setText("")
        self.login_view.remember_me_checkbox.setChecked(False)

        # Mark as logged out
        self.logged_in = False
        self.sidebar.setVisible(False)

        # Reset current_user
        self.current_user = ""

        # Switch to login page
        self.stacked_widget.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set a custom global font for the application
    font_path = os.path.abspath("assets/fonts/Poppins-Medium.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        print(f"Failed to load Poppins font from {font_path}. Falling back to Arial.")
        app.setFont(QFont("Arial", 10 if sys.platform == "win32" else 13))
    else:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 10 if sys.platform == "win32" else 13))

    # Run the main application
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
