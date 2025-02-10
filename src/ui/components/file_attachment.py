from PyQt5.QtCore import Qt, pyqtSignal

from src.ui.components.email_body import BodyWidget


class FileAttachmentWidget(BodyWidget):
    """Modified version of BodyWidget for handling file attachments only."""

    file_added = pyqtSignal(str)
    file_removed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Remove the email body component, as this widget is only for attachments
        self.body_edit.deleteLater()
        self.body_edit = None

        # Align attachments at the top for better organization
        self.attachments_layout.setAlignment(Qt.AlignTop)

    def add_attachment(self, filepath):
        """Overrides parent method to emit a signal when a file is added."""
        super().add_attachment(filepath)
        self.file_added.emit(filepath)

    def remove_attachment(self, row_widget, filepath):
        """Overrides parent method to emit a signal when a file is removed."""
        super().remove_attachment(row_widget, filepath)
        self.file_removed.emit(filepath)

    def clear_attachments(self):
        """Removes all attachments from the list and UI."""
        while self.attachments_layout.count():
            item = self.attachments_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self.attachments.clear()
