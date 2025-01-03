from PyQt5.QtCore import Qt, QTime, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QTimeEdit

from src.ui.components.components import create_button, create_card, create_day_button, create_separator
from src.ui.modals.base_modal import BaseModalWindow
from src.ui.style import (
    BLUE_BUTTON_STYLE,
    GRAY_BUTTON_STYLE,
    INFO_WINDOW_STYLE,
    INSTRUCTION_LABEL_STYLE,
    TIME_PICKER_STYLE,
)


class ScheduleModalWindow(BaseModalWindow):
    schedule_saved = pyqtSignal(str, list)  # Signal to send time and days on save
    schedule_canceled = pyqtSignal()  # Signal to indicate cancellation

    def __init__(self, parent=None):
        super().__init__(width=400, height=400, style_sheet=INFO_WINDOW_STYLE, parent=parent)

        # Time Picker Section
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setFixedSize(145, 69)
        self.time_edit.setStyleSheet(TIME_PICKER_STYLE)
        self.time_edit.lineEdit().setAlignment(Qt.AlignCenter)
        self.time_edit.setFocusPolicy(Qt.ClickFocus)
        time_card = create_card([self.time_edit], margins=(0, 0, 0, 0), spacing=0)
        self.add_widget(time_card, alignment=Qt.AlignHCenter)

        self.main_layout.addSpacing(20)

        # Days Selection Section (Optional)
        days_layout = QHBoxLayout()
        days_layout.setSpacing(5)
        self.day_buttons = {}
        days = ["M", "T", "W", "T", "F", "S", "S"]
        full_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for abbr, full in zip(days, full_days):
            button = create_day_button(abbr)
            button.setToolTip(full)
            self.day_buttons[full] = button
            days_layout.addWidget(button)
        self.add_layout(days_layout)

        # Add Stretch Before Instruction Label
        self.main_layout.addStretch()

        # Instructional Label
        instruction_label = QLabel(
            "Schedule an automation by setting the time.\n" "You can optionally select recurring days."
        )
        instruction_label.setStyleSheet(INSTRUCTION_LABEL_STYLE)
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.add_widget(instruction_label)

        # Spacer to Push Buttons to Bottom
        self.main_layout.addStretch()

        # Separator
        self.add_widget(create_separator())

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        cancel_button = create_button("Cancel", GRAY_BUTTON_STYLE)
        cancel_button.setFixedSize(80, 30)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = create_button("Save", BLUE_BUTTON_STYLE)
        save_button.setFixedSize(80, 30)
        save_button.clicked.connect(self.save_schedule)
        button_layout.addWidget(save_button)

        self.add_layout(button_layout, alignment=Qt.AlignRight)

    def save_schedule(self):
        """Saves the selected time and days to set an automation schedule."""
        selected_time = self.time_edit.time().toString("HH:mm")
        selected_days = [day for day, btn in self.day_buttons.items() if btn.isChecked()]
        # Allow scheduling within the next 24 hours without recurring days
        self.schedule_saved.emit(selected_time, selected_days)
        self.accept()

    def reject(self):
        """Handles the Cancel button click."""
        self.schedule_canceled.emit()
        super().reject()
