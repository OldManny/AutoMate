from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QFrame, QLineEdit, QPushButton, QVBoxLayout, QWidget

from src.ui.style import CARD_STYLE, DAY_BUTTON_STYLE, FOLDER_INPUT_STYLE, SEPARATOR_STYLE


def create_button(text, style_sheet, size=(80, 30)):
    """
    Creates a styled QPushButton with specified text, stylesheet, and size.
    """
    button = QPushButton(text)
    button.setFixedSize(*size)
    button.setStyleSheet(style_sheet)
    button.setCursor(Qt.PointingHandCursor)  # Changes cursor to a pointer when hovering
    return button


def create_folder_input():
    """
    Creates a QLineEdit for folder input, styled and set to read-only.
    """
    folder_input = QLineEdit()
    folder_input.setPlaceholderText("Select folder...")  # Placeholder text for guidance
    folder_input.setReadOnly(True)  # Prevent manual editing
    folder_input.setFixedWidth(333)  # Fixed width for consistency
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
    Creates a QPushButton styled as an icon-only button.

    Parameters:
    - icon_path: Path to the icon image.
    - icon_size: Size of the icon inside the button.
    - button_size: Overall button dimensions.
    - tooltip: Tooltip text for the button.
    - cursor: Cursor style when hovering over the button.
    - style_sheet: Additional styles for the button.
    """
    icon_btn = QPushButton()
    icon_btn.setIcon(QIcon(icon_path))
    icon_btn.setFixedSize(*button_size)
    icon_btn.setIconSize(QSize(*icon_size))
    icon_btn.setCursor(cursor)
    icon_btn.setStyleSheet(style_sheet)
    if tooltip:
        icon_btn.setToolTip(tooltip)  # Display tooltip if provided
    return icon_btn


def create_separator():
    """
    Creates a styled separator line with padding above and below.
    """
    separator_widget = QWidget()
    separator_widget.setFixedHeight(10)  # Space for the separator
    separator_layout = QVBoxLayout(separator_widget)
    separator_layout.setContentsMargins(0, 0, 0, 0)
    separator_layout.setSpacing(0)

    separator_layout.addSpacing(5)  # Top padding

    # Add the actual line
    separator_line = QFrame()
    separator_line.setFixedHeight(1)  # Thickness of the line
    separator_line.setStyleSheet(SEPARATOR_STYLE)
    separator_layout.addWidget(separator_line)

    separator_layout.addSpacing(5)  # Bottom padding

    return separator_widget


def create_card(content_widgets, class_name="card", margins=(10, 10, 10, 10), spacing=5):
    """
    Creates a styled card container for grouping widgets.

    Parameters:
    - content_widgets: List of widgets to include in the card.
    - class_name: Class name for styling purposes.
    - margins: Tuple defining the margins for the layout (left, top, right, bottom).
    - spacing: Spacing between child widgets.
    """
    card = QWidget()
    card.setProperty("class", class_name)  # Assigns a class name for styling
    card.setStyleSheet(CARD_STYLE)
    layout = QVBoxLayout(card)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    for widget in content_widgets:
        layout.addWidget(widget)  # Add each widget to the card
    return card


def create_day_button(letter):
    """
    Creates a QPushButton styled as a day selection button.

    Parameters:
    - letter: Single character representing the day (e.g., 'M' for Monday).
    """
    button = QPushButton(letter)
    button.setFixedSize(40, 40)  # Uniform button size for all days
    button.setCheckable(True)  # Allows toggling on/off
    button.setStyleSheet(DAY_BUTTON_STYLE)
    button.setCursor(QCursor(Qt.PointingHandCursor))  # Pointer cursor for better UX
    return button
