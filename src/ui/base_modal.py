from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget


class BaseModalWindow(QDialog):
    """
    Base class for modal windows with rounded corners and customizable layouts.
    """

    def __init__(self, width, height, style_sheet, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setFixedSize(width, height)

        # Remove title bar and window buttons
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Enable translucent background for rounded corners
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Central widget with styling
        central_widget = QWidget(self)
        central_widget.setObjectName("central_widget")
        central_widget.setStyleSheet(style_sheet)

        # Main layout for the central widget
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Set layout for the dialog
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(central_widget)

    def add_widget(self, widget, alignment=None):
        """
        Adds a widget to the main layout with optional alignment.
        """
        if alignment:
            self.main_layout.addWidget(widget, alignment=alignment)
        else:
            self.main_layout.addWidget(widget)

    def add_layout(self, layout, alignment=None):
        """
        Adds a layout to the main layout with optional alignment.
        """
        container = QWidget()
        container.setLayout(layout)
        if alignment:
            self.main_layout.addWidget(container, alignment=alignment)
        else:
            self.main_layout.addWidget(container)
