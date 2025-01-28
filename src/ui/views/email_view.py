from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QTextEdit, QVBoxLayout, QWidget

from src.automation.email_sender import send_email_via_mailgun
from src.ui.components.components import create_button, create_card, create_separator
from src.ui.components.toast_notification import ToastNotification
from src.ui.style import BLUE_BUTTON_STYLE, EMAIL_INPUT_STYLE


class EmailView(QWidget):
    """
    A UI component for composing and sending emails,
    with fields for 'To', 'Cc', 'Subject', 'From', and a message body.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Apply the global style for email fields
        self.setStyleSheet(EMAIL_INPUT_STYLE)

        # Create the toast notification instance here:
        self.toast = ToastNotification(self)

        # Main layout configuration
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ========== Header Section ==========
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Email icon for the header
        icon_label = QLabel()
        icon_pixmap = QPixmap("assets/icons/email.png")
        icon_pixmap = icon_pixmap.scaled(39, 39, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Scale smoothly
        icon_label.setContentsMargins(0, 10, 0, 1)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        # Description text for the header
        desc_label = QLabel("Send emails right away,\nor schedule them to repeat as needed.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        desc_label.setStyleSheet("color: #C9D3D5; font-size: 12px;")

        # Add the icon and text to the header
        header_layout.addWidget(icon_label)
        header_layout.addWidget(desc_label)

        main_layout.addWidget(header_widget)
        main_layout.addWidget(create_separator())

        # ========== Input Fields Section ==========
        fields_card_widgets = []  # Store all field widgets

        # 'To' field
        self.to_input = self.create_small_line_edit("To")
        fields_card_widgets.append(self.to_input)
        fields_card_widgets.append(create_separator())  # Separator after each field

        # 'Cc' field
        self.cc_input = self.create_small_line_edit("Cc")
        fields_card_widgets.append(self.cc_input)
        fields_card_widgets.append(create_separator())

        # 'Subject' field
        self.subj_input = self.create_small_line_edit("Subject")
        fields_card_widgets.append(self.subj_input)
        fields_card_widgets.append(create_separator())

        # 'From' field
        self.from_input = self.create_small_line_edit("From")
        fields_card_widgets.append(self.from_input)
        fields_card_widgets.append(create_separator())

        # Email body (multiline input)
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Body")
        fields_card_widgets.append(self.body_edit)

        # Group all fields into a card
        fields_card = create_card(
            content_widgets=fields_card_widgets,
            margins=(8, 5, 8, 5),  # Margins for the card
            spacing=0,  # Minimal spacing between elements
        )
        main_layout.addWidget(fields_card)

        # ========== Bottom Send Button ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.send_btn = create_button("Send", BLUE_BUTTON_STYLE)
        self.send_btn.clicked.connect(self.on_send_clicked)
        button_layout.addWidget(self.send_btn)
        main_layout.addLayout(button_layout)

    def create_small_line_edit(self, placeholder_text):
        """
        Creates a single-line text input with a placeholder.

        Parameters:
        - placeholder_text: Text to guide the user inside the input field.
        """
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder_text)
        line_edit.setFixedHeight(21)  # Restrict height to avoid stretching
        return line_edit

    def on_send_clicked(self):
        """
        When user clicks Send, gather input fields,
        call our backend mail function, then show toast and clear on success.
        """
        to_field = self.to_input.text().strip()
        cc_field = self.cc_input.text().strip()
        subj_field = self.subj_input.text().strip()
        from_field = self.from_input.text().strip()
        body_text = self.body_edit.toPlainText().strip()

        # Quick check
        if not to_field or not from_field:
            self.toast.show_message("Please specify 'To' and 'From'", "info")
            return

        # Comma-separated -> list
        to_list = [addr for addr in to_field.split(',') if addr]
        cc_list = [addr for addr in cc_field.split(',') if addr]

        try:
            # Call the backend function
            send_email_via_mailgun(
                from_address=from_field,
                to_addresses=to_list,
                subject=subj_field,
                body_text=body_text,
                cc_addresses=cc_list,
            )
            # Show success & clear fields
            self.toast.show_message("Email sent", "success")
            self.to_input.clear()
            self.cc_input.clear()
            self.subj_input.clear()
            self.from_input.clear()
            self.body_edit.clear()

        except Exception as e:
            print(f"Failed to send email: {e}")
            self.toast.show_message("Failed to send email", "error")
