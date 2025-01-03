from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.ui.style import TOOLTIP_STYLE


class CustomTooltip(QWidget):
    """
    A custom tooltip widget to show full text for truncated elements.
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(TOOLTIP_STYLE)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignLeft)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(5, 5, 5, 5)

    def show_tooltip(self, text, position):
        """Display the tooltip with the given text and position."""
        self.label.setText(text)
        self.adjustSize()
        self.move(position)
        self.show()

    def hide_tooltip(self):
        """Hide the tooltip."""
        self.hide()
