import re

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from src.ui.components.components import create_button
from src.ui.components.toast_notification import ToastNotification
from src.ui.style import BLUE_BUTTON_STYLE, INPUT_FIELDS_STYLE, MAIN_WINDOW_STYLE
from src.utils.auth import generate_remember_me_token, load_user_data, register_user, verify_user

EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'


def is_valid_email(email: str) -> bool:
    """
    Returns True if email is a valid email address, else False.
    """
    pattern = re.compile(EMAIL_REGEX)
    return bool(pattern.match(email))


class LoginView(QWidget):
    """
    A widget that shows either a Login screen or a Registration screen.
    On successful login or registration, it emits a signal so that the main app
    can switch to the main interface.
    """

    login_success = pyqtSignal(str)  # emits the email when login/registration is successful

    def __init__(self, parent=None):
        super().__init__(parent)
        self.toast = ToastNotification(self)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # Outer layout for the entire LoginView
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)

        # Create placeholders for login & register widgets
        self.login_widget = QWidget()
        self.register_widget = QWidget()

        # Build the two modes
        self.init_login_ui()
        self.init_register_ui()

        data = load_user_data()
        if len(data["users"]) >= 1:
            self.register_link.hide()  # Hide if already has an account

        # Add them to the outer layout (filling the space)
        self.outer_layout.addWidget(self.login_widget)
        self.outer_layout.addWidget(self.register_widget)

        # Default mode
        self.current_mode = "login"
        self.setup_login_mode()

    def init_login_ui(self):
        '''
        Initialize the login page UI
        '''
        layout = QVBoxLayout(self.login_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title top-center
        welcome_label = QLabel("Welcome to AutoMate")
        welcome_label.setStyleSheet("color: #C9D3D5; font-size: 25px;")
        welcome_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(welcome_label, 0, Qt.AlignTop)

        # Stretch to push fields to the vertical middle
        layout.addStretch()

        # Middle fields
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(15)
        fields_layout.setAlignment(Qt.AlignHCenter)

        # Email field
        self.email_input_login = QLineEdit()
        self.email_input_login.setPlaceholderText("Email")
        self.email_input_login.setStyleSheet(INPUT_FIELDS_STYLE)
        self.email_input_login.setMaximumWidth(300)  # limit width

        # Pressing Enter inside email field triggers login
        self.email_input_login.returnPressed.connect(self.on_login_clicked)
        fields_layout.addWidget(self.email_input_login)

        # Password field
        self.password_input_login = QLineEdit()
        self.password_input_login.setEchoMode(QLineEdit.Password)
        self.password_input_login.setPlaceholderText("Password")
        self.password_input_login.setStyleSheet(INPUT_FIELDS_STYLE)
        self.password_input_login.setMaximumWidth(300)

        # Pressing Enter inside password field triggers login
        self.password_input_login.returnPressed.connect(self.on_login_clicked)
        fields_layout.addWidget(self.password_input_login)

        # Remember me checkbox
        self.remember_me_checkbox = QCheckBox("Remember me")
        self.remember_me_checkbox.setStyleSheet("color: white;")
        fields_layout.addWidget(self.remember_me_checkbox, 0, Qt.AlignHCenter)

        # Register link
        self.register_link = QLabel()
        self.register_link.setTextFormat(Qt.RichText)
        self.register_link.setText("<a href='#' style='color: #27A6FF; text-decoration: none;'>or Register</a>")
        self.register_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.register_link.setOpenExternalLinks(False)
        self.register_link.linkActivated.connect(self.show_register_mode)
        fields_layout.addWidget(self.register_link, 0, Qt.AlignHCenter)

        layout.addLayout(fields_layout)
        layout.addStretch()

        # Bottom-right button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.login_btn = create_button("Login", BLUE_BUTTON_STYLE, size=(80, 30))
        self.login_btn.clicked.connect(self.on_login_clicked)
        button_layout.addWidget(self.login_btn, 0, Qt.AlignRight)
        layout.addLayout(button_layout)

    def init_register_ui(self):
        '''
        Initialize the register page UI
        '''
        reg_layout = QVBoxLayout(self.register_widget)
        reg_layout.setContentsMargins(20, 20, 20, 20)
        reg_layout.setSpacing(20)

        # Title top-center
        title_label = QLabel("Welcome to AutoMate")
        title_label.setStyleSheet("color: #C9D3D5; font-size: 25px;")
        title_label.setAlignment(Qt.AlignHCenter)
        reg_layout.addWidget(title_label, 0, Qt.AlignTop)

        # Stretch to push fields to the vertical middle
        reg_layout.addStretch()

        # Middle fields
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(15)
        fields_layout.setAlignment(Qt.AlignHCenter)

        # Email field
        self.email_input_register = QLineEdit()
        self.email_input_register.setPlaceholderText("Email")
        self.email_input_register.setStyleSheet(INPUT_FIELDS_STYLE)
        self.email_input_register.setMaximumWidth(300)

        # Pressing Enter triggers register
        self.email_input_register.returnPressed.connect(self.on_register_clicked)
        fields_layout.addWidget(self.email_input_register)

        # Password field
        self.password_input_register = QLineEdit()
        self.password_input_register.setPlaceholderText("Password")
        self.password_input_register.setEchoMode(QLineEdit.Password)
        self.password_input_register.setStyleSheet(INPUT_FIELDS_STYLE)
        self.password_input_register.setMaximumWidth(300)
        self.password_input_register.returnPressed.connect(self.on_register_clicked)
        fields_layout.addWidget(self.password_input_register)

        # Confirm password field
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setStyleSheet(INPUT_FIELDS_STYLE)
        self.confirm_password_input.setMaximumWidth(300)
        self.confirm_password_input.returnPressed.connect(self.on_register_clicked)
        fields_layout.addWidget(self.confirm_password_input)

        # Login link
        self.login_link = QLabel()
        self.register_link.setTextFormat(Qt.RichText)
        self.login_link.setText(
            "<a href='#' style='color: #27A6FF; text-decoration: none;'>Already have an account? Login</a>"
        )
        self.login_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.login_link.setOpenExternalLinks(False)
        self.login_link.linkActivated.connect(self.show_login_mode)
        fields_layout.addWidget(self.login_link, 0, Qt.AlignHCenter)

        reg_layout.addLayout(fields_layout)

        # Stretch to push button to the bottom
        reg_layout.addStretch()

        # Bottom-right button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.register_btn = create_button("Register", BLUE_BUTTON_STYLE, size=(80, 30))
        self.register_btn.clicked.connect(self.on_register_clicked)
        button_layout.addWidget(self.register_btn, 0, Qt.AlignRight)
        reg_layout.addLayout(button_layout)

    def show_login_mode(self):
        '''
        Load the login mode
        '''
        self.current_mode = "login"
        self.setup_login_mode()

    def show_register_mode(self):
        '''
        Load the register mode
        '''
        data = load_user_data()
        if len(data["users"]) >= 1:
            self.toast.show_message("An account already exists on this machine", "error")
            return
        self.current_mode = "register"
        self.setup_login_mode()

    def setup_login_mode(self):
        """
        Hides one widget, shows the other based on current_mode.
        """
        if self.current_mode == "login":
            self.login_widget.show()
            self.register_widget.hide()
        else:
            self.login_widget.hide()
            self.register_widget.show()

    def on_login_clicked(self):
        """
        Login button clicked. Validate and attempt login
        """
        email = self.email_input_login.text().strip()
        password = self.password_input_login.text().strip()
        if not email or not password:
            self.toast.show_message("Please fill all fields", "error")
            return

        # Verify user
        if verify_user(email, password):
            # If "Remember Me" is checked, generate a token in the JSON
            if self.remember_me_checkbox.isChecked():
                generate_remember_me_token(email)

            # Emit success signal
            self.login_success.emit(email)
        else:
            self.toast.show_message("Invalid email or password", "error")

    def on_register_clicked(self):
        """
        Register button clicked. Validate and attempt registration
        """
        email = self.email_input_register.text().strip()
        password = self.password_input_register.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not email or not password or not confirm_password:
            self.toast.show_message("Please fill all fields", "error")
            return

        # Validate email format
        if not is_valid_email(email):
            self.toast.show_message("Invalid email format", "error")
            return

        if password != confirm_password:
            self.toast.show_message("Passwords do not match", "error")
            return

        # Attempt registration
        success = register_user(email, password)
        if success:
            self.toast.show_message("Registration successful! Please log in", "info")
            self.email_input_login.setText(email)
            self.password_input_login.setText("")
            self.show_login_mode()  # Switch to login mode
