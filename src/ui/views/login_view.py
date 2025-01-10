from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QLabel, QLineEdit, QVBoxLayout, QWidget

from src.ui.components.auth_utils import generate_remember_me_token, register_user, verify_user
from src.ui.components.components import create_button
from src.ui.components.toast_notification import ToastNotification
from src.ui.style import BLUE_BUTTON_STYLE, MAIN_WINDOW_STYLE


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
        self.setFixedSize(400, 300)  # tweak as needed

        # Implemented two layouts: login_layout, register_layout
        self.init_login_ui()
        self.init_register_ui()

        # By default, show login layout
        self.current_mode = "login"
        self.setup_login_mode()

    def init_login_ui(self):
        """
        Creates all widgets for the login form.
        """
        self.login_widget = QWidget(self)
        self.login_widget.setGeometry(0, 0, 400, 300)

        layout = QVBoxLayout(self.login_widget)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title / Welcome
        welcome_label = QLabel("Welcome! Please log in.")
        welcome_label.setStyleSheet("color: white; font-size: 16px;")
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)

        # Email field
        self.email_input_login = QLineEdit()
        self.email_input_login.setPlaceholderText("Email")
        self.email_input_login.setStyleSheet(self.custom_input_style())
        layout.addWidget(self.email_input_login)

        # Password field
        self.password_input_login = QLineEdit()
        self.password_input_login.setEchoMode(QLineEdit.Password)
        self.password_input_login.setPlaceholderText("Password")
        self.password_input_login.setStyleSheet(self.custom_input_style())
        layout.addWidget(self.password_input_login)

        # "Remember Me" checkbox
        self.remember_me_checkbox = QCheckBox("Remember me")
        self.remember_me_checkbox.setStyleSheet("color: white;")
        layout.addWidget(self.remember_me_checkbox)

        # "Or Register" link
        self.register_link = QLabel("<a href='#'> or Register</a>")
        self.register_link.setStyleSheet("color: #0096FF;")
        self.register_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.register_link.setOpenExternalLinks(False)
        self.register_link.linkActivated.connect(self.show_register_mode)
        layout.addWidget(self.register_link, alignment=Qt.AlignCenter)

        # Login button
        login_btn = create_button("Login", BLUE_BUTTON_STYLE, size=(80, 30))
        login_btn.clicked.connect(self.on_login_clicked)
        layout.addWidget(login_btn, alignment=Qt.AlignRight)

    def init_register_ui(self):
        """
        Creates all widgets for the registration form.
        """
        self.register_widget = QWidget(self)
        self.register_widget.setGeometry(0, 0, 400, 300)

        layout = QVBoxLayout(self.register_widget)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Register a New Account")
        title_label.setStyleSheet("color: white; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Email
        self.email_input_register = QLineEdit()
        self.email_input_register.setPlaceholderText("Email")
        self.email_input_register.setStyleSheet(self.custom_input_style())
        layout.addWidget(self.email_input_register)

        # Password
        self.password_input_register = QLineEdit()
        self.password_input_register.setPlaceholderText("Password")
        self.password_input_register.setEchoMode(QLineEdit.Password)
        self.password_input_register.setStyleSheet(self.custom_input_style())
        layout.addWidget(self.password_input_register)

        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setStyleSheet(self.custom_input_style())
        layout.addWidget(self.confirm_password_input)

        # "Already have an account? Login"
        self.login_link = QLabel("<a href='#'>Already have an account? Login</a>")
        self.login_link.setStyleSheet("color: #0096FF;")
        self.login_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.login_link.setOpenExternalLinks(False)
        self.login_link.linkActivated.connect(self.show_login_mode)
        layout.addWidget(self.login_link, alignment=Qt.AlignCenter)

        # Register button
        register_btn = create_button("Register", BLUE_BUTTON_STYLE, size=(80, 30))
        register_btn.clicked.connect(self.on_register_clicked)
        layout.addWidget(register_btn, alignment=Qt.AlignRight)

    def show_login_mode(self):
        '''
        Switch to the login mode
        '''
        self.current_mode = "login"
        self.setup_login_mode()

    def show_register_mode(self):
        '''
        Switch to the register mode
        '''
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
        '''
        Login button clicked. Validate and attempt login
        '''
        email = self.email_input_login.text().strip()
        password = self.password_input_login.text().strip()
        if not email or not password:
            self.toast.show_message("Please fill all fields.", "error")
            return

        # Verify user
        if verify_user(email, password):
            # If "Remember Me" is checked, generate a token in the JSON
            if self.remember_me_checkbox.isChecked():
                generate_remember_me_token(email)

            # Emit success signal
            self.login_success.emit(email)

        else:
            self.toast.show_message("Invalid email or password.", "error")

    def on_register_clicked(self):
        '''
        Register button clicked. Validate and attempt registration
        '''
        email = self.email_input_register.text().strip()
        password = self.password_input_register.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not email or not password or not confirm_password:
            self.toast.show_message("Please fill all fields.", "error")
            return

        if password != confirm_password:
            self.toast.show_message("Passwords do not match!", "error")
            return

        # Attempt registration
        success = register_user(email, password)
        if not success:
            self.toast.show_message("User already exists!", "error")
        else:
            self.toast.show_message("Registration successful! Please log in.", "info")
            # Switch automatically back to login
            self.show_login_mode()

    def custom_input_style(self):
        """
        Custom style for input fields
        """
        # Base style
        custom = """
            QLineEdit {
                background-color: #4B5D5C;
                color: white;
                border-radius: 10px;
                padding: 8px;
                margin: 5px 0;
            }
        """
        return custom
