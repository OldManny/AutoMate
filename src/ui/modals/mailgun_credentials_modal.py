from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from src.ui.components.components import create_button, create_separator
from src.ui.components.toast_notification import ToastNotification
from src.ui.modals.base_modal import BaseModalWindow
from src.ui.style import BLUE_BUTTON_STYLE, GRAY_BUTTON_STYLE, INFO_WINDOW_STYLE, INPUT_FIELDS_STYLE_MAILGUN
from src.utils import startup_manager
from src.utils.auth import get_startup_setting, save_mailgun_credentials, set_startup_setting


class MailgunCredentialsModal(BaseModalWindow):
    """
    Modal window for entering Mailgun API Key and Domain,
    and configuring startup behavior.
    """

    def __init__(self, parent=None, current_key="", current_domain="", current_user_email=""):
        super().__init__(width=400, height=310, style_sheet=INFO_WINDOW_STYLE, parent=parent)

        # Store the email for updating settings
        self.current_user_email = current_user_email

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
            self.startup_checkbox.setToolTip("Login required to manage startup setting.")

        # Connect checkbox state change to the handler
        self.startup_checkbox.stateChanged.connect(self.handle_startup_change_request)

        startup_layout.addWidget(self.startup_checkbox)
        self.add_layout(startup_layout)

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
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # Rename button and connect to the correct function
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

    def save_settings(self):
        """
        Validates credentials, saves them, updates startup setting, and accepts the dialog.
        """
        print(f"--- save_settings called for user: {self.current_user_email} ---")  # Keep debug print

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
            print(f"Checkbox state: {startup_requested}, Current OS setting: {current_os_setting}")  # Debug

            if startup_requested and not current_os_setting:
                print("Attempting to enable startup...")
                startup_change_success = startup_manager.enable_startup()
                print(f"enable_startup returned: {startup_change_success}")
                if not startup_change_success:
                    self.toast.show_message("Failed to enable startup", "error")
                    self.startup_checkbox.setChecked(False)  # Revert UI

            elif not startup_requested and current_os_setting:
                print("Attempting to disable startup...")
                startup_change_success = startup_manager.disable_startup()
                print(f"disable_startup returned: {startup_change_success}")
                if not startup_change_success:
                    self.toast.show_message("Failed to disable startup", "error")
                    self.startup_checkbox.setChecked(True)  # Revert UI

            # Update stored JSON setting *only if* OS change succeeded
            if startup_change_success:
                print(f"OS change successful ({startup_change_success}), attempting to save setting to JSON...")
                setting_saved = set_startup_setting(self.current_user_email, startup_requested)
                if not setting_saved:
                    print(f"Warning: Failed to save setting for user {self.current_user_email}")
                else:
                    print(
                        f"Successfully saved startup setting ({startup_requested}) to JSON for {self.current_user_email}"
                    )

            else:
                print(f"OS change failed ({startup_change_success}), *NOT* saving setting to JSON.")

        else:
            print("Warning: Cannot save startup setting, user email missing.")
            startup_change_success = False

        # Proceed only if OS startup change didn't fail
        if startup_change_success:
            credentials_saved_ok = True
            # Only save credentials if they were actually provided
            if key and domain:
                print(f"Attempting to save credentials for {self.current_user_email}...")
                if not save_mailgun_credentials(self.current_user_email, key, domain):
                    self.toast.show_message("Failed to save credentials securely", "error")
                    credentials_saved_ok = False
                else:
                    print("Credentials saved successfully.")

            # Close the dialog if OS startup was ok AND credentials were saved ok
            if credentials_saved_ok:
                print("Accepting dialog.")
                self.accept()
            else:
                print("Dialog not accepted due to credential saving failure.")

        else:
            print("Dialog not accepted due to startup setting failure.")
