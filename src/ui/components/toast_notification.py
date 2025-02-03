from PyQt5.QtCore import QPoint, QPropertyAnimation, Qt, QTimer
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.ui.style import TOAST_NOTIFICATION_STYLE


class ToastNotification(QWidget):
    def __init__(self, parent=None, duration=3000):
        super().__init__(parent)

        # Setup window properties for the toast notification
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Setup layout and message label
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        self.label = QLabel()  # Label to display the notification message
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Initialize duration and animations
        self.duration = duration
        self.show_animation = QPropertyAnimation(self, b"pos")  # Show animation
        self.show_animation.setDuration(300)
        self.hide_animation = QPropertyAnimation(self, b"pos")  # Hide animation
        self.hide_animation.setDuration(300)
        self.hide_animation.finished.connect(self._on_hide_finished)

        # Timer to auto-hide after duration
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.start_hide_animation)

        # Set the default style for the notification
        self.setStyleSheet(TOAST_NOTIFICATION_STYLE)

    def paintEvent(self, event):
        """Custom paint event to draw a rounded rectangle background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create background color with opacity
        color = self.palette().color(self.backgroundRole())
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)

        # Border radius
        painter.drawRoundedRect(self.rect(), 5, 5)

    def show_message(self, message, message_type="info"):
        """Displays the toast notification with the specified message and type."""
        # Stop any existing animations or timers
        self.show_animation.stop()
        self.hide_animation.stop()
        self.hide_timer.stop()

        # Define colors for different message types
        colors = {
            "success": "#4ADE80",  # Bright green
            "error": "#F87171",  # Bright red
            "info": "#27A6FF",  # Bright blue
        }
        text_color = colors.get(message_type, colors["info"])

        # Apply styles and set the message
        self.label.setStyleSheet(
            f"""
            QLabel {{
                color: {text_color};
                font-size: 13px;
                font-weight: 500;
            }}
        """
        )
        self.label.setText(message)
        self.adjustSize()  # Resize the widget to fit the content

        # Calculate position relative to the parent window
        main_window = None
        parent = self.parent()
        while parent is not None:
            main_window = parent
            parent = parent.parent()

        if main_window:
            # Get the geometry of the main window
            main_geometry = main_window.geometry()
            x = main_geometry.x() + main_geometry.width() - self.width() - 20
            target_y = main_geometry.y() + 5

            # Position slightly above the target position for animation
            self.move(x, target_y - 5)

            # Setup show animation
            self.show_animation.setStartValue(self.pos())
            self.show_animation.setEndValue(QPoint(x, target_y))
            self.show()
            self.show_animation.start()

            # Start the timer to hide after the specified duration
            self.hide_timer.start(self.duration)

    def start_hide_animation(self):
        """Starts the hide animation to fade out the notification."""
        if self.isVisible():
            current_pos = self.pos()
            self.hide_animation.setStartValue(current_pos)
            self.hide_animation.setEndValue(QPoint(current_pos.x(), current_pos.y() - 5))
            self.hide_animation.start()

    def _on_hide_finished(self):
        """Called when hide animation finishes"""
        self.hide()
