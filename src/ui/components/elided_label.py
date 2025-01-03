from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QLabel

from src.ui.components.tooltip import CustomTooltip


class ElidedLabel(QLabel):
    """
    Custom QLabel that truncates text with ellipsis if it exceeds the max width.
    Displays the full text using a custom tooltip only if the text is truncated.
    """

    tooltip = None  # Shared tooltip instance

    def __init__(self, text, max_width=None, font_size=None):
        super().__init__(text)
        self.full_text = text
        self.max_width = max_width

        if max_width:
            self.setMaximumWidth(max_width)
        if font_size:
            self.setStyleSheet(f"font-size: {font_size}pt;")

        # Create a shared tooltip instance if not already created
        if not ElidedLabel.tooltip:
            ElidedLabel.tooltip = CustomTooltip()

    def paintEvent(self, event):
        """Override to render elided text."""
        if self.max_width:
            metrics = self.fontMetrics()
            if metrics.horizontalAdvance(self.full_text) > self.max_width:
                elided_text = metrics.elidedText(self.full_text, Qt.ElideMiddle, self.max_width)
                self.setText(elided_text)
            else:
                self.setText(self.full_text)
        super().paintEvent(event)

    def enterEvent(self, event):
        """Show tooltip when hovering over truncated text."""
        if self.max_width:
            metrics = QFontMetrics(self.font())
            if metrics.horizontalAdvance(self.full_text) > self.max_width:
                global_position = self.mapToGlobal(self.rect().bottomLeft())
                ElidedLabel.tooltip.show_tooltip(self.full_text, global_position)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide tooltip when leaving the label."""
        ElidedLabel.tooltip.hide_tooltip()
        super().leaveEvent(event)
