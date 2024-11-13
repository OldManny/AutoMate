import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTextEdit,
)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, QCoreApplication


# Main application class inheriting from QMainWindow
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()  # Initialize the user interface

    def initUI(self):
        """Sets up the main UI components and layout."""
        self.setWindowTitle("AutoMate")  # Set the window title
        self.resize(600, 600)  # Set the initial window size
        self.center()  # Center the window on the screen

        # Create the main layout and set margins
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header Image setup
        self.header_image = QLabel(self)
        pixmap = QPixmap("assets/Header.jpg")  # Load header image
        self.header_image.setPixmap(pixmap)  # Set the pixmap to QLabel
        self.header_image.setScaledContents(True)  # Scale image to fit QLabel
        main_layout.addWidget(self.header_image)

        # Add spacing after the header image
        main_layout.addSpacing(0)

        # Button layout for organizing feature buttons horizontally
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 0, 10, 0)  # Margins for button layout

        # Placeholder buttons for core application features
        self.file_organizer_btn = self.create_custom_button("Organize Files", 200, 50)
        button_layout.addWidget(self.file_organizer_btn)

        self.email_sender_btn = self.create_custom_button("Send Email", 200, 50)
        button_layout.addWidget(self.email_sender_btn)

        self.data_entry_btn = self.create_custom_button("Data Entry", 200, 50)
        button_layout.addWidget(self.data_entry_btn)

        # Add the button layout to the main layout
        main_layout.addLayout(button_layout)

        # Status area for displaying messages to the user
        self.status = QTextEdit(self)
        self.status.setReadOnly(True)  # Make status area read-only
        self.status.setFixedHeight(100)  # Fixed height for consistent layout
        main_layout.addWidget(self.status)

        # Set the main layout as the central widget for the window
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_custom_button(self, text, width, height):
        """Creates a styled button with specified text, width, and height."""
        button = QPushButton(text, self)  # Create button with label text
        button.setFixedSize(width, height)  # Set button dimensions
        button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )  # Custom button styling
        button.setCursor(Qt.PointingHandCursor)  # Change cursor on hover
        return button

    def center(self):
        """Centers the application window on the screen."""
        qr = self.frameGeometry()  # Get window geometry
        cp = (
            QCoreApplication.instance().desktop().screenGeometry().center()
        )  # Get center point of screen
        qr.moveCenter(cp)  # Move window geometry to center point
        self.move(qr.topLeft())  # Move the window to the new center position

    def update_status(self, message):
        """
        Updates the status area with a message.
        Highlights messages with "error" or "fail" in orange, others in cyan.
        """
        if "error" in message.lower() or "fail" in message.lower():
            self.status.setTextColor(QColor("orange"))  # Set error message color
        else:
            self.status.setTextColor(QColor("cyan"))  # Set regular message color
        self.status.append(message)  # Append the message to the status area


# Main application entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)  # Initialize the application
    main_app = MainApp()  # Create an instance of MainApp
    main_app.show()  # Show the main window
    sys.exit(app.exec_())  # Start the application event loop
