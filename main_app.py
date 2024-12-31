import os
import sys

from PyQt5.QtCore import QCoreApplication, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.automation.scheduler_manager import SchedulerManager
from src.ui.file_organizer_view import FileOrganizerCustomizationDialog
from src.ui.running_jobs import RunningJobsModal
from src.ui.style import MAIN_WINDOW_STYLE, NAV_BUTTON_STYLE, SIDEBAR_STYLE


class MainApp(QMainWindow):
    """
    Main application window for AutoMate with a sidebar and multiple pages.
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(588, 600)  # Fixed window size
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)  # Disable maximize button
        self.setStyleSheet(MAIN_WINDOW_STYLE)  # Apply main window style
        self.scheduler_manager = SchedulerManager()
        self.initUI()

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

        # Create
        self.sidebar = self.create_sidebar()

        # Add shadow effect to the sidebar
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 250))
        self.sidebar.setGraphicsEffect(shadow)
        main_layout.addWidget(self.sidebar)

        # Create content area
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Stack for switching between pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.create_file_organizer_page())
        self.stacked_widget.addWidget(self.create_email_page())
        self.stacked_widget.addWidget(self.create_data_entry_page())

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
        sidebar.setFixedWidth(150)  # Fixed width for the sidebar
        sidebar.setStyleSheet(SIDEBAR_STYLE)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 30, 0, 30)
        layout.setSpacing(0)

        # Button group for navigation
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        # Navigation buttons
        nav_buttons = [
            ("Files", 0, "assets/photos/file.png"),
            ("Email", 1, "assets/photos/email.png"),
            ("Data", 2, "assets/photos/data.png"),
        ]

        for text, index, icon_path in nav_buttons:
            btn = self.create_nav_button(text, icon_path)
            btn.setCheckable(True)
            self.nav_button_group.addButton(btn)
            btn.clicked.connect(lambda checked, idx=index: self.on_nav_button_clicked(idx))
            layout.addWidget(btn)

        # Set the first button as initially checked
        first_button = self.nav_button_group.buttons()[0]
        first_button.setChecked(True)

        # Add a spacer and additional buttons
        layout.addStretch()
        auto_btn = self.create_nav_button("Schedule", "assets/photos/schedule.png")
        auto_btn.clicked.connect(self.open_schedule_modal)
        layout.addWidget(auto_btn)

        running_btn = self.create_nav_button("Running", "assets/photos/running.png")
        running_btn.clicked.connect(self.open_running_modal)  # Add this line
        layout.addWidget(running_btn)

        return sidebar

    def create_nav_button(self, text, icon_path):
        """
        Creates a styled navigation button with an optional icon.
        """
        button = QPushButton(text)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            # Set the icon size
            button.setIconSize(QSize(27, 27))  # Icon size
            button.setFixedHeight(50)
            button.setText("  " + text)  # Add space for text alignment
        button.setStyleSheet(NAV_BUTTON_STYLE)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def on_nav_button_clicked(self, index):
        """
        Switches to the selected page in the stacked widget.
        """
        self.stacked_widget.setCurrentIndex(index)

    def open_schedule_modal(self):
        """
        Opens the scheduling modal for automation.
        """
        current_widget = self.stacked_widget.currentWidget()
        if isinstance(current_widget, QWidget):
            file_organizer = current_widget.findChild(QWidget, "FileOrganizerWidget")
            if file_organizer:
                file_organizer.open_schedule_modal()

    def open_running_modal(self):
        running_modal = RunningJobsModal(scheduler_manager=self.scheduler_manager, parent=self)
        running_modal.exec_()

    def create_file_organizer_page(self):
        """
        Creates the file organizer page.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Pass the shared scheduler_manager to FileOrganizerCustomizationDialog
        file_organizer = FileOrganizerCustomizationDialog(parent=self, scheduler_manager=self.scheduler_manager)
        file_organizer.setObjectName("FileOrganizerWidget")
        layout.addWidget(file_organizer)

        return container

    def closeEvent(self, event):
        # Gracefully shut down the scheduler on app exit
        self.scheduler_manager.shutdown()
        super().closeEvent(event)

    def create_email_page(self):
        """
        Creates a placeholder page for the email module.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("Email Sender Module")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

    def create_data_entry_page(self):
        """
        Creates a placeholder page for the data entry module.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("Data Entry Module")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

    def center(self):
        """
        Centers the main application window on the screen.
        """
        qr = self.frameGeometry()
        cp = QCoreApplication.instance().desktop().screenGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set a custom global font for the application
    font_path = os.path.abspath("assets/fonts/Poppins-Medium.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        print(f"Failed to load Poppins font from {font_path}. Falling back to default.")
    else:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 13))

    # Run the main application
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())
