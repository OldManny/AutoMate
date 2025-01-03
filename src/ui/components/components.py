from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QFrame, QLineEdit, QPushButton, QVBoxLayout, QWidget

from src.ui.style import CARD_STYLE, DAY_BUTTON_STYLE, FOLDER_INPUT_STYLE, SEPARATOR_STYLE


def create_button(text, style_sheet, size=(80, 30)):
    button = QPushButton(text)
    button.setFixedSize(*size)
    button.setStyleSheet(style_sheet)
    button.setCursor(Qt.PointingHandCursor)
    return button


def create_folder_input():
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
    separator_widget = QWidget()
    separator_widget.setFixedHeight(10)
    separator_layout = QVBoxLayout(separator_widget)
    separator_layout.setContentsMargins(0, 0, 0, 0)
    separator_layout.setSpacing(0)

    separator_layout.addSpacing(5)  # Top padding

    separator_line = QFrame()
    separator_line.setFixedHeight(1)
    separator_line.setStyleSheet(SEPARATOR_STYLE)
    separator_layout.addWidget(separator_line)

    separator_layout.addSpacing(5)  # Bottom padding

    return separator_widget


def create_card(content_widgets, class_name="card", margins=(10, 10, 10, 10), spacing=5):
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
    button = QPushButton(letter)
    button.setFixedSize(40, 40)
    button.setCheckable(True)
    button.setStyleSheet(DAY_BUTTON_STYLE)
    button.setCursor(QCursor(Qt.PointingHandCursor))
    return button
