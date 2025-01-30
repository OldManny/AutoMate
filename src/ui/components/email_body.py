import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from src.ui.style import DELETE_BUTTON_STYLE


class CustomTextEdit(QTextEdit):
    """
    A QTextEdit subclass that prevents file drops while still allowing text input.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(False)  # Disable direct file drops into the text area


class BodyWidget(QWidget):
    """
    Widget that displays email attachments (as clickable filenames with delete buttons)
    and provides a text area for composing the email body.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.attachments = []  # Store file paths of attachments

        # Main layout setup
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Container for displaying attachments
        self.attachments_container = QWidget()
        self.attachments_layout = QVBoxLayout(self.attachments_container)
        self.attachments_layout.setSpacing(5)
        self.attachments_layout.setContentsMargins(10, 0, 0, 0)
        self.main_layout.addWidget(self.attachments_container)

        # Email body text input
        self.body_edit = CustomTextEdit()
        self.body_edit.setPlaceholderText("Write your email here...")
        self.main_layout.addWidget(self.body_edit)

    def dragEnterEvent(self, event):
        """Accept drag event if it contains files."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Allow moving dragged files over the widget."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle dropped files and add them as attachments."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if os.path.isfile(filepath):
                    self.add_attachment(filepath)
            event.accept()
        else:
            event.ignore()

    def add_attachment(self, filepath):
        """Add an attachment to the UI and prevent duplicates."""
        if filepath in self.attachments:
            return  # Avoid duplicate file entries

        self.attachments.append(filepath)

        # Create a row for each attachment (filename + delete button)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        # Clickable filename
        link_label = QLabel()
        filename = os.path.basename(filepath)
        link_label.setProperty("filepath", filepath)
        link_label.setText(f'<a href="#">{filename}</a>')
        link_label.setStyleSheet("color: #60A5FA; font-size: 12px;")
        link_label.setOpenExternalLinks(False)
        link_label.setTextFormat(Qt.RichText)
        link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link_label.linkActivated.connect(lambda: self.open_file(link_label.property("filepath")))
        row_layout.addWidget(link_label)

        # Delete button for removing attachments
        delete_button = QPushButton("×")
        delete_button.setFixedSize(16, 16)
        delete_button.setStyleSheet(DELETE_BUTTON_STYLE)
        delete_button.clicked.connect(lambda: self.remove_attachment(row_widget, filepath))
        row_layout.addWidget(delete_button)

        row_layout.addStretch()  # Push elements to the left
        self.attachments_layout.addWidget(row_widget)

    def remove_attachment(self, row_widget, filepath):
        """Remove the attachment from the UI and list."""
        if filepath in self.attachments:
            self.attachments.remove(filepath)
        row_widget.deleteLater()

    def open_file(self, filepath):
        """Open an attached file using the system's default application."""
        if os.path.exists(filepath):
            QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))

    def get_body_text(self):
        """Return the text entered in the body field."""
        return self.body_edit.toPlainText().strip()

    def clear_body(self):
        """Clear the body text and remove all attachment widgets."""
        self.body_edit.clear()
        while self.attachments_layout.count():
            item = self.attachments_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self.attachments.clear()
