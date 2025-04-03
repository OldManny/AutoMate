from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from src.ui.components.components import create_button, create_separator
from src.ui.components.toast_notification import ToastNotification
from src.ui.modals.base_modal import BaseModalWindow
from src.ui.style import BLUE_BUTTON_STYLE, GRAY_BUTTON_STYLE, INFO_WINDOW_STYLE, INPUT_FIELDS_STYLE


class MailgunCredentialsModal(BaseModalWindow):
    """
    Modal window for entering Mailgun API Key and Domain.
    """

    def __init__(self, parent=None, current_key="", current_domain=""):
        super().__init__(width=400, height=270, style_sheet=INFO_WINDOW_STYLE, parent=parent)
        self.api_key = ""
        self.domain = ""

        self.init_ui(current_key, current_domain)

        # Toast notification instance
        self.toast = ToastNotification(self)

    def init_ui(self, current_key, current_domain):
        """Sets up the UI elements for the modal."""

        # Title
        title_label = QLabel("Enter Mailgun Credentials")
        title_label.setStyleSheet("color: #C9D3D5; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        self.add_widget(title_label)

        # Input Fields container
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(15)
        fields_layout.setAlignment(Qt.AlignCenter)

        # API Key field (masked)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Mailgun API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)  # Mask the input
        self.api_key_input.setStyleSheet(INPUT_FIELDS_STYLE)
        self.api_key_input.setMaximumWidth(350)
        self.api_key_input.setText(current_key)
        fields_layout.addWidget(self.api_key_input)

        # Domain field
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("Mailgun Domain (e.g., sandbox....mailgun.org)")
        self.domain_input.setStyleSheet(INPUT_FIELDS_STYLE)
        self.domain_input.setMaximumWidth(350)
        self.domain_input.setText(current_domain)
        fields_layout.addWidget(self.domain_input)

        self.add_layout(fields_layout)

        # Spacer
        self.main_layout.addStretch()

        # Separator
        self.add_widget(create_separator())

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        cancel_button = create_button("Cancel", GRAY_BUTTON_STYLE, size=(80, 30))
        cancel_button.clicked.connect(self.reject)  # QDialog's reject
        button_layout.addWidget(cancel_button)

        ok_button = create_button("OK", BLUE_BUTTON_STYLE, size=(80, 30))
        ok_button.clicked.connect(self.save_credentials)
        button_layout.addWidget(ok_button)

        self.add_layout(button_layout, alignment=Qt.AlignRight)

    def save_credentials(self):
        """Validates input and accepts the dialog, storing the values."""
        key = self.api_key_input.text().strip()
        domain = self.domain_input.text().strip()

        if not key or not domain:
            # Optionally show a message within the modal or use a toast later
            self.toast.show_message("API & Domain cannot be empty", "info")
            return

        self.api_key = key
        self.domain = domain
        self.accept()  # QDialog's accept

    def get_credentials(self):
        """Returns the entered credentials after the modal is accepted."""
        return self.api_key, self.domain
