from PyQt5.QtWidgets import QPushButton, QLineEdit
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import QSize, Qt
from .style import BLUE_BUTTON_STYLE, GRAY_BUTTON_STYLE, FOLDER_INPUT_STYLE


def create_blue_button(text):
    button = QPushButton(text)
    button.setFixedSize(69, 27)
    button.setStyleSheet(BLUE_BUTTON_STYLE)
    return button


def create_gray_button(text):
    button = QPushButton(text)
    button.setFixedSize(69, 27)
    button.setStyleSheet(GRAY_BUTTON_STYLE)
    return button


def create_folder_input():
    # Create folder input with styling and placeholder
    folder_input = QLineEdit()
    folder_input.setPlaceholderText("Select folder...")
    folder_input.setReadOnly(True)
    folder_input.setFixedWidth(275)
    folder_input.setStyleSheet(FOLDER_INPUT_STYLE)
    return folder_input


def create_folder_icon_button(icon_path="assets/folder(3).png"):
    # Create folder icon button with a specific icon and pointer cursor
    icon_btn = QPushButton()
    icon_btn.setIcon(QIcon(icon_path))
    icon_btn.setFixedSize(30, 30)
    icon_btn.setIconSize(QSize(30, 30))
    icon_btn.setCursor(QCursor(Qt.PointingHandCursor))
    icon_btn.setStyleSheet("border: none;")
    return icon_btn
