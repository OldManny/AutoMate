from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QVBoxLayout, QWidget

from src.automation.email_sender import send_email_via_mailgun
from src.ui.components.components import create_button, create_card, create_separator
from src.ui.components.email_body import BodyWidget
from src.ui.components.toast_notification import ToastNotification
from src.ui.modals.schedule_modal import ScheduleModalWindow
from src.ui.style import BLUE_BUTTON_STYLE, EMAIL_INPUT_STYLE


class EmailView(QWidget):
    """
    Email editor with To, Cc, Subject, From, plus a BodyWidget
    for text & attachments. The 'Send' button calls Mailgun.
    """

    def __init__(self, parent=None, scheduler_manager=None):
        super().__init__(parent)
        self.setObjectName("EmailView")
        self.scheduler_manager = scheduler_manager

        # Apply the global style for email fields
        self.setStyleSheet(EMAIL_INPUT_STYLE)

        # Toast notification instance
        self.toast = ToastNotification(self)

        # Main layout for the entire widget
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Email icon for the header
        icon_label = QLabel()
        icon_pixmap = QPixmap("assets/icons/email.png")
        icon_pixmap = icon_pixmap.scaled(39, 39, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setContentsMargins(0, 10, 0, 1)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        # Description text for the header
        desc_label = QLabel("Send emails right away,\nor schedule them to repeat as needed.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        desc_label.setStyleSheet("color: #C9D3D5; font-size: 12px;")

        # Add the icon and text
        header_layout.addWidget(icon_label)
        header_layout.addWidget(desc_label)
        main_layout.addWidget(header_widget)
        main_layout.addWidget(create_separator())

        # Store all field widgets in a list
        fields_card_widgets = []

        # Single-line fields
        self.to_input = self._create_line_edit("To")
        fields_card_widgets.append(self.to_input)
        fields_card_widgets.append(create_separator())

        self.cc_input = self._create_line_edit("Cc")
        fields_card_widgets.append(self.cc_input)
        fields_card_widgets.append(create_separator())

        self.subj_input = self._create_line_edit("Subject")
        fields_card_widgets.append(self.subj_input)
        fields_card_widgets.append(create_separator())

        self.from_input = self._create_line_edit("From")
        fields_card_widgets.append(self.from_input)
        fields_card_widgets.append(create_separator())

        # BodyWidget for text + attachments
        self.body_widget = BodyWidget()
        fields_card_widgets.append(self.body_widget)

        # Group all fields into a card
        fields_card = create_card(content_widgets=fields_card_widgets, margins=(8, 5, 8, 5), spacing=0)
        main_layout.addWidget(fields_card)

        # Send button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.send_btn = create_button("Send", BLUE_BUTTON_STYLE)
        self.send_btn.clicked.connect(self.on_send_clicked)
        btn_layout.addWidget(self.send_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _create_line_edit(self, placeholder):
        """Creates a single-line text input with a placeholder."""
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setFixedHeight(21)
        return line_edit

    def on_send_clicked(self):
        """Collect fields, send via mailgun, and clear on success."""
        to_text = self.to_input.text().strip()
        cc_text = self.cc_input.text().strip()
        subj_text = self.subj_input.text().strip()
        from_text = self.from_input.text().strip()

        body_text = self.body_widget.get_body_text()
        attachments = self.body_widget.attachments

        # Validate fields
        if not to_text or not from_text:
            self.toast.show_message("Specify 'To' and 'From'", "info")
            return

        # Split comma-separated emails into a list
        to_list = [x for x in to_text.split(',') if x.strip()]
        cc_list = [x for x in cc_text.split(',') if x.strip()]

        try:
            # Call the backend function
            send_email_via_mailgun(
                from_address=from_text,
                to_addresses=to_list,
                subject=subj_text,
                body_text=body_text,
                cc_addresses=cc_list,
                attachments=attachments,
            )
            # Show success & clear fields
            self.toast.show_message("Email sent", "success")
            self.to_input.clear()
            self.cc_input.clear()
            self.subj_input.clear()
            self.from_input.clear()
            self.body_widget.clear_body()

        except Exception as e:
            print("Failed to send email:", e)
            self.toast.show_message(f"Failed to send: {e}", "error")

    def open_schedule_modal(self):
        """Opens the Schedule Modal Window for setting email schedules."""
        schedule_modal = ScheduleModalWindow(self)
        schedule_modal.schedule_saved.connect(self.on_schedule_saved)
        schedule_modal.schedule_canceled.connect(self.on_schedule_canceled)

        # Center the modal relative to the main window
        self.center_modal(schedule_modal)
        schedule_modal.exec_()

    def on_schedule_saved(self, selected_time, selected_days):
        """Handles scheduling an email to be sent at the specified time."""
        to_text = self.to_input.text().strip()
        from_text = self.from_input.text().strip()

        # Validate required fields
        if not to_text or not from_text:
            self.toast.show_message("Specify 'To' and 'From'", "info")
            return

        # Store email parameters
        email_params = {
            "from_address": from_text,
            "to_addresses": [x.strip() for x in to_text.split(',') if x.strip()],
            "cc_addresses": [x.strip() for x in self.cc_input.text().split(',') if x.strip()],
            "subject": self.subj_input.text().strip(),
            "body_text": self.body_widget.get_body_text(),
            "attachments": self.body_widget.attachments,
        }

        if self.scheduler_manager:
            job_id = self.scheduler_manager.add_scheduled_job(
                task_type="send_email",
                folder_target=to_text,
                run_time=selected_time,
                recurring_days=selected_days,
                job_id=f"email_{datetime.now().timestamp()}",
                email_params=email_params,
            )

            # Store the email parameters in the job metadata
            self.scheduler_manager.job_metadata[job_id]["email_params"] = email_params

        if selected_days:
            days_list = ", ".join(selected_days)
            self.toast.show_message(f"Email scheduled for {selected_time}\non {days_list}", "success")
        else:
            self.toast.show_message(f"Email scheduled for {selected_time}", "success")

        # Clear fields after scheduling
        self.to_input.clear()
        self.cc_input.clear()
        self.subj_input.clear()
        self.from_input.clear()
        self.body_widget.clear_body()

    def on_schedule_canceled(self):
        """Handles the schedule canceled signal."""
        self.toast.show_message("Scheduling canceled", "info")

    def center_modal(self, modal):
        """Centers the modal relative to the main window."""
        main_window = self.window()
        if main_window:
            main_window_center = main_window.geometry().center()
            modal_geometry = modal.frameGeometry()
            modal_geometry.moveCenter(main_window_center)
            modal.move(modal_geometry.topLeft())
