from PyQt5.QtCore import QSize, Qt, QTime
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from .base_modal import BaseModalWindow
from .style import (
    BLUE_BUTTON_STYLE,
    CARD_STYLE,
    DAY_BUTTON_STYLE,
    FOLDER_INPUT_STYLE,
    GRAY_BUTTON_STYLE,
    INFO_WINDOW_STYLE,
    INSTRUCTION_LABEL_STYLE,
    SEPARATOR_STYLE,
    TIME_PICKER_STYLE,
)


def create_button(text, style_sheet, size=(80, 30)):
    """
    Creates a QPushButton with the given text, style sheet, and size.
    """
    button = QPushButton(text)
    button.setFixedSize(*size)
    button.setStyleSheet(style_sheet)
    button.setCursor(Qt.PointingHandCursor)
    return button


def create_folder_input():
    """
    Creates a QLineEdit styled for folder input with a placeholder text.
    """
    folder_input = QLineEdit()
    folder_input.setPlaceholderText("Select folder...")
    folder_input.setReadOnly(True)
    folder_input.setFixedWidth(333)
    folder_input.setStyleSheet(FOLDER_INPUT_STYLE)
    return folder_input


def create_icon_button(
    icon_path,
    icon_size=(24, 24),
    button_size=(30, 30),
    tooltip=None,
    cursor=Qt.PointingHandCursor,
    style_sheet="border: none;",
):
    """
    Creates a QPushButton with an icon, styled as an icon-only button.
    """
    icon_btn = QPushButton()
    icon_btn.setIcon(QIcon(icon_path))
    icon_btn.setFixedSize(*button_size)
    icon_btn.setIconSize(QSize(*icon_size))
    icon_btn.setCursor(cursor)
    icon_btn.setStyleSheet(style_sheet)
    if tooltip:
        icon_btn.setToolTip(tooltip)
    return icon_btn


def create_separator():
    """
    Creates a separator widget with padding above and below.
    """
    separator_widget = QWidget()
    separator_widget.setFixedHeight(10)
    separator_layout = QVBoxLayout(separator_widget)
    separator_layout.setContentsMargins(0, 0, 0, 0)
    separator_layout.setSpacing(0)

    # Add top padding
    separator_layout.addSpacing(5)

    # Create the separator line
    separator_line = QFrame()
    separator_line.setFixedHeight(1)
    separator_line.setStyleSheet(SEPARATOR_STYLE)
    separator_layout.addWidget(separator_line)

    # Add bottom padding
    separator_layout.addSpacing(5)

    return separator_widget


def create_card(content_widgets, class_name="card", margins=(10, 10, 10, 10), spacing=5):
    """
    Creates a styled card widget containing the given content widgets.
    """
    card = QWidget()
    card.setProperty("class", class_name)
    card.setStyleSheet(CARD_STYLE)
    layout = QVBoxLayout(card)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    for widget in content_widgets:
        layout.addWidget(widget)
    return card


def create_day_button(letter):
    """
    Creates a QPushButton styled as a day selection button with the given letter.
    """
    button = QPushButton(letter)
    button.setFixedSize(40, 40)
    button.setCheckable(True)
    button.setStyleSheet(DAY_BUTTON_STYLE)
    button.setCursor(QCursor(Qt.PointingHandCursor))
    return button


# -------------------- Modal Windows --------------------


class ScheduleModalWindow(BaseModalWindow):
    """
    Modal window for scheduling automation operations with time and day selection.
    """

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

        # Days Selection Section
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
        instruction_label = QLabel("Schedule an automation by setting the time \nand selecting the recurring days.")
        instruction_label.setStyleSheet(INSTRUCTION_LABEL_STYLE)
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.add_widget(instruction_label)

        # Spacer to Push Buttons to Bottom
        self.main_layout.addStretch()

        #  Separator
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
        if not selected_days:
            QMessageBox.warning(self, "No Days Selected", "Please select at least one day.")
            return
        confirmation_message = f"Scheduled at {selected_time} on: {', '.join(selected_days)}."
        QMessageBox.information(self, "Schedule Set", confirmation_message)
        self.accept()


class InfoWindow(BaseModalWindow):
    """
    Pop-up window to display informational text.
    """

    def __init__(self, info_text, parent=None):
        super().__init__(width=370, height=200, style_sheet=INFO_WINDOW_STYLE, parent=parent)

        # Info text label
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #C9D3D5; font-size: 12px;")
        self.add_widget(info_label)

        # Spacer to push elements to the bottom
        self.main_layout.addStretch()

        # Separator line above the button
        self.add_widget(create_separator())

        # 'Done' button aligned to the bottom right
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        done_button = create_button("Done", BLUE_BUTTON_STYLE)
        done_button.setStyleSheet(BLUE_BUTTON_STYLE)
        done_button.setFixedSize(77, 23)
        done_button.clicked.connect(self.accept)
        button_layout.addWidget(done_button)
        self.add_layout(button_layout, alignment=Qt.AlignRight)
