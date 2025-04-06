from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from src.ui.components.components import create_button, create_separator
from src.ui.components.toast_notification import ToastNotification
from src.ui.modals.base_modal import BaseModalWindow
from src.ui.style import (
    BLUE_BUTTON_STYLE,
    GRAY_BUTTON_STYLE,
    GREEN_BUTTON_STYLE,
    INFO_WINDOW_STYLE,
    INPUT_FIELDS_STYLE_MAILGUN,
)
from src.utils import startup_manager
from src.utils.auth import get_startup_setting, save_mailgun_credentials, set_startup_setting


class MailgunCredentialsModal(BaseModalWindow):
    """
    Modal window for entering Mailgun API Key and Domain,
    and configuring startup behavior.
    """

    logout_requested = pyqtSignal()

    def __init__(self, parent=None, current_key="", current_domain="", current_user_email=""):
        super().__init__(width=400, height=390, style_sheet=INFO_WINDOW_STYLE, parent=parent)

        # Center the modal relative to the parent
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2,
            )

        # Store the email for updating settings
        self.current_user_email = current_user_email

        self.logout_was_requested = False

        self.init_ui(current_key, current_domain)

        # Toast notification instance
        self.toast = ToastNotification(self)

    def init_ui(self, current_key, current_domain):
        """Sets up the UI elements for the modal."""

        # Title
        title_label = QLabel("Mailgun Credentials")
        title_label.setStyleSheet("color: #C9D3D5; font-size: 14px;")  # Keep font size if desired
        title_label.setAlignment(Qt.AlignCenter)
        self.add_widget(title_label)

        # Input Fields container
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(15)
        fields_layout.setAlignment(Qt.AlignCenter)

        # API Key field (masked)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Mailgun API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setStyleSheet(INPUT_FIELDS_STYLE_MAILGUN)
        self.api_key_input.setMaximumWidth(350)
        self.api_key_input.setText(current_key)
        fields_layout.addWidget(self.api_key_input)

        # Domain field
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("Mailgun Domain (e.g., sandbox....mailgun.org)")
        self.domain_input.setStyleSheet(INPUT_FIELDS_STYLE_MAILGUN)
        self.domain_input.setMaximumWidth(350)
        self.domain_input.setText(current_domain)
        fields_layout.addWidget(self.domain_input)

        self.add_layout(fields_layout)

        # Startup Checkbox Section
        self.main_layout.addSpacing(15)
        startup_layout = QHBoxLayout()
        startup_layout.setAlignment(Qt.AlignCenter)

        self.startup_checkbox = QCheckBox("Launch at Login")
        self.startup_checkbox.setStyleSheet("color: #C9D3D5; font-size: 13px")

        # Load initial state based on current user's setting
        if self.current_user_email:
            initial_startup_state = get_startup_setting(self.current_user_email)
            self.startup_checkbox.setChecked(initial_startup_state)
        else:
            self.startup_checkbox.setEnabled(False)

        # Connect checkbox state change to the handler
        self.startup_checkbox.stateChanged.connect(self.handle_startup_change_request)

        startup_layout.addWidget(self.startup_checkbox)
        self.add_layout(startup_layout)

        # Spacer
        self.main_layout.addSpacing(15)

        # Logout button
        logout_button = create_button("Sign Out", GREEN_BUTTON_STYLE, size=(170, 28))
        logout_button.clicked.connect(self.handle_logout_request)

        self.add_widget(logout_button, alignment=Qt.AlignHCenter)

        # Spacer
        self.main_layout.addSpacing(15)

        # Separator
        self.add_widget(create_separator())

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        cancel_button = create_button("Cancel", GRAY_BUTTON_STYLE, size=(80, 30))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = create_button("Save", BLUE_BUTTON_STYLE, size=(80, 30))
        save_button.clicked.connect(self.save_settings)  # Connect to save_settings
        button_layout.addWidget(save_button)

        self.add_layout(button_layout, alignment=Qt.AlignRight)

    def get_credentials(self):
        """Returns the entered credentials directly from the input fields."""
        # Reading directly from input fields
        return self.api_key_input.text().strip(), self.domain_input.text().strip()

    def handle_startup_change_request(self, state):
        """
        Intermediate handler for startup checkbox.
        """
        pass

    def handle_logout_request(self):
        """Handles the logout button click within the modal."""
        self.logout_was_requested = True
        self.logout_requested.emit()
        self.reject()

    def save_settings(self):
        """
        Validates credentials, saves them, updates startup setting, and accepts the dialog.
        """

        # Credential Validation
        key = self.api_key_input.text().strip()
        domain = self.domain_input.text().strip()

        if key or domain:
            if not key or not domain:
                self.toast.show_message("Both API Key & Domain are required", "info")
                return

        # Startup Setting Handling
        startup_requested = self.startup_checkbox.isChecked()
        startup_change_success = True

        if self.current_user_email:
            current_os_setting = startup_manager.is_startup_enabled()
            os_op_needed = startup_requested != current_os_setting

            if os_op_needed:
                if startup_requested:
                    startup_change_success = startup_manager.enable_startup()
                    if not startup_change_success:
                        self.toast.show_message("Failed to enable startup", "error")
                        self.startup_checkbox.setChecked(False)
                else:
                    startup_change_success = startup_manager.disable_startup()
                    if not startup_change_success:
                        self.toast.show_message("Failed to disable startup", "error")
                        self.startup_checkbox.setChecked(True)
                        return

            # Update stored JSON setting only if OS operation was needed and successful
            if startup_change_success and os_op_needed:
                setting_saved = set_startup_setting(self.current_user_email, startup_requested)
                if not setting_saved:
                    print(f"Warning: Failed to save startup setting for user {self.current_user_email}")

        # Save Credentials
        credentials_saved_ok = True
        if startup_change_success:
            if key and domain:
                if not save_mailgun_credentials(self.current_user_email, key, domain):
                    self.toast.show_message("Failed to save credentials securely", "error")
                    credentials_saved_ok = False
                    return

        # Close Dialog
        if startup_change_success and credentials_saved_ok:
            self.accept()  # Signal success to caller
        else:
            print("Modal not closing due to internal error.")
