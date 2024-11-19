from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QLineEdit, QPushButton

from .style import BLUE_BUTTON_STYLE, FOLDER_INPUT_STYLE, GRAY_BUTTON_STYLE


def create_blue_button(text):
    """
    Creates a QPushButton styled as a blue button with a fixed size.

    Parameters:
        text (str): The text label to display on the button.

    """
    button = QPushButton(text)  # Initialize button with text
    button.setFixedSize(79, 27)  # Set fixed button size
    button.setStyleSheet(BLUE_BUTTON_STYLE)  # Apply blue button style
    return button


def create_gray_button(text):
    """
    Creates a QPushButton styled as a gray button with a fixed size.

    Parameters:
        text (str): The text label to display on the button.

    """
    button = QPushButton(text)  # Initialize button with text
    button.setFixedSize(79, 27)  # Set fixed button size
    button.setStyleSheet(GRAY_BUTTON_STYLE)  # Apply gray button style
    return button


def create_folder_input():
    """
    Creates a QLineEdit styled for folder input with a placeholder text.

    Returns:
        QLineEdit: A non-editable line input field with a placeholder for folder selection.
    """
    folder_input = QLineEdit()  # Initialize line edit for folder input
    folder_input.setPlaceholderText("Select folder...")  # Set placeholder text
    folder_input.setReadOnly(True)  # Make input read-only
    folder_input.setFixedWidth(275)  # Set fixed width
    folder_input.setStyleSheet(FOLDER_INPUT_STYLE)  # Apply folder input style
    return folder_input


def create_folder_icon_button(
    icon_path="assets/folder.png",
):  # Folder icon sourced from Freepik - Flaticon
    """
    Creates a QPushButton with an icon, styled as an icon-only button for folder selection.

    Parameters:
        icon_path (str): The file path to the icon image (default is "assets/folder.png").

    """
    icon_btn = QPushButton()  # Initialize button for folder icon
    icon_btn.setIcon(QIcon(icon_path))  # Set the icon for the button
    icon_btn.setFixedSize(30, 30)  # Set fixed button size
    icon_btn.setIconSize(QSize(30, 30))  # Set icon size
    icon_btn.setCursor(QCursor(Qt.PointingHandCursor))  # Set cursor to pointing hand on hover
    icon_btn.setStyleSheet("border: none;")  # Remove button border
    return icon_btn
