from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QFrame, QLineEdit, QPushButton, QVBoxLayout, QWidget

from .style import BLUE_BUTTON_STYLE, CARD_STYLE, FOLDER_INPUT_STYLE, GRAY_BUTTON_STYLE, SEPARATOR_STYLE


def create_blue_button(text):
    """
    Creates a QPushButton styled as a blue button with a fixed size.
    """
    button = QPushButton(text)
    button.setFixedSize(79, 27)
    button.setStyleSheet(BLUE_BUTTON_STYLE)
    button.setCursor(Qt.PointingHandCursor)
    return button


def create_gray_button(text):
    """
    Creates a QPushButton styled as a gray button with a fixed size.
    """
    button = QPushButton(text)
    button.setFixedSize(79, 27)
    button.setStyleSheet(GRAY_BUTTON_STYLE)
    button.setCursor(Qt.PointingHandCursor)
    return button


def create_folder_input():
    """
    Creates a QLineEdit styled for folder input with a placeholder text.
    """
    folder_input = QLineEdit()
    folder_input.setPlaceholderText("Select folder...")
    folder_input.setReadOnly(True)
    folder_input.setFixedWidth(291)
    folder_input.setStyleSheet(FOLDER_INPUT_STYLE)
    return folder_input


def create_folder_icon_button(
    icon_path="assets/photos/folder.png",
):  # Folder icon sourced from Freepik - Flaticon
    """
    Creates a QPushButton with an icon, styled as an icon-only button for folder selection.
    """
    icon_btn = QPushButton()
    icon_btn.setIcon(QIcon(icon_path))
    icon_btn.setFixedSize(30, 30)
    icon_btn.setIconSize(QSize(25, 25))
    icon_btn.setCursor(QCursor(Qt.PointingHandCursor))
    icon_btn.setStyleSheet("border: none;")
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


def create_card(content_widgets, class_name='card', margins=(10, 10, 10, 10), spacing=5):
    """
    Creates a styled card widget containing the given content widgets.
    """
    card = QWidget()
    card.setProperty('class', class_name)
    card.setStyleSheet(CARD_STYLE)
    layout = QVBoxLayout(card)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    for widget in content_widgets:
        layout.addWidget(widget)
    return card
