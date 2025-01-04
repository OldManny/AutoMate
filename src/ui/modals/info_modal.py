from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel

from src.ui.components.components import create_button, create_separator
from src.ui.modals.base_modal import BaseModalWindow
from src.ui.style import BLUE_BUTTON_STYLE, INFO_WINDOW_STYLE


class InfoWindow(BaseModalWindow):
    """
    Pop-up window to display informational text.
    """

    def __init__(self, info_text, parent=None):
        super().__init__(width=370, height=215, style_sheet=INFO_WINDOW_STYLE, parent=parent)

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
