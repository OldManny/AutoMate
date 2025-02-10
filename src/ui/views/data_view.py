import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.components import (
    create_button,
    create_card,
    create_folder_input,
    create_icon_button,
    create_separator,
)
from src.ui.modals.info_modal import InfoWindow
from src.ui.style import BLUE_BUTTON_STYLE, GRAY_BUTTON_STYLE


class DataView(QWidget):
    """
    UI component for managing data files, allowing users to merge or mirror CSV/Excel files.
    """

    CARD_FIXED_HEIGHT = 260  # Fixed height for the multi-file selection card

    def __init__(self, parent=None, scheduler_manager=None):
        super().__init__(parent)
        self.scheduler_manager = scheduler_manager
        self.setObjectName("DataView")

        self.single_file_path = None
        self.multi_file_paths = []
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components, including file selection, drag-and-drop, and action buttons.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header Section
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Icon and description
        icon_label = QLabel()
        icon_pixmap = QPixmap("assets/icons/data.png").scaled(39, 39, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setContentsMargins(0, 10, 0, 1)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        desc_label = QLabel("Streamline your data flow:\nmerge or mirror files with ease.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        desc_label.setStyleSheet("color: #C9D3D5; font-size: 12px;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(desc_label)
        main_layout.addWidget(header_widget)
        main_layout.addWidget(create_separator())

        # Single File Selection
        file_layout = QHBoxLayout()
        self.file_input = create_folder_input()
        self.file_input.setPlaceholderText("Select a master CSV/Excel file...")
        file_layout.addWidget(self.file_input)

        self.file_icon_btn = create_icon_button(
            icon_path="assets/icons/folder.png",
            icon_size=(29, 29),
            button_size=(30, 30),
        )
        self.file_icon_btn.clicked.connect(self.select_single_file)
        file_layout.addWidget(self.file_icon_btn)

        main_layout.addLayout(file_layout)
        main_layout.addSpacing(15)

        # Multi-File Selection
        multi_files_card = create_card(content_widgets=[], margins=(0, 0, 0, 0), spacing=0)
        multi_files_card.setFixedHeight(self.CARD_FIXED_HEIGHT)
        multi_files_card.setAcceptDrops(False)

        card_content = QWidget()
        card_layout = QVBoxLayout(card_content)
        card_layout.setContentsMargins(12, 0, 12, 12)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignTop)

        # Info Card Section Header
        info_header = QWidget()
        info_header_layout = QHBoxLayout(info_header)
        info_header_layout.setContentsMargins(10, 10, 0, 0)
        info_header_layout.setSpacing(5)

        info_text = QLabel("Drag and drop multiple CSV/Excel files below:")
        info_text.setStyleSheet("color: #C9D3D5; font-size: 12px;")
        info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_header_layout.addWidget(info_text)

        # Info Card Section Button
        info_button = create_icon_button(
            icon_path="assets/icons/info.png",
            icon_size=(16, 16),
            button_size=(20, 20),
        )
        info_button.clicked.connect(
            lambda: self.show_info_window(
                "Merge combines data from multiple files into a single master, "
                "while Mirror copies the master’s contents to every other file."
                "\n\nThis workflow keeps everything synchronized and updated with minimal effort."
            )
        )
        info_header_layout.addWidget(info_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        card_layout.addWidget(info_header)

        # File Attachment Area
        self.multi_file_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.multi_file_area.file_added.connect(self.on_multi_file_added)
        self.multi_file_area.file_removed.connect(self.on_multi_file_removed)
        card_layout.addWidget(self.multi_file_area)

        multi_files_card.layout().addWidget(card_content)
        main_layout.addWidget(multi_files_card)

        # Merge / Mirror Radio Buttons
        radio_layout = QHBoxLayout()
        radio_layout.setAlignment(Qt.AlignCenter)

        self.merge_radio = QRadioButton("Merge")
        self.mirror_radio = QRadioButton("Mirror")
        self.merge_radio.setChecked(True)

        group = QButtonGroup(self)
        group.addButton(self.merge_radio)
        group.addButton(self.mirror_radio)

        radio_layout.addWidget(self.merge_radio)
        radio_layout.addSpacing(20)
        radio_layout.addWidget(self.mirror_radio)
        main_layout.addLayout(radio_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.undo_btn = create_button("Undo", GRAY_BUTTON_STYLE)
        self.undo_btn.clicked.connect(self.on_undo_clicked)
        btn_layout.addWidget(self.undo_btn)

        self.run_btn = create_button("Run", BLUE_BUTTON_STYLE)
        self.run_btn.clicked.connect(self.on_run_clicked)
        btn_layout.addWidget(self.run_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def show_info_window(self, info_text):
        """Displays an informational modal window."""
        self.info_window = InfoWindow(info_text, parent=self)
        main_window = self.window()
        # Center the modal window on the main window
        if main_window:
            main_window_center = main_window.geometry().center()
            window_geometry = self.info_window.frameGeometry()
            window_geometry.moveCenter(main_window_center)
            self.info_window.move(window_geometry.topLeft())
        self.info_window.show()

    def select_single_file(self):
        """Opens a file dialog for selecting a master file."""
        dlg = QFileDialog(self, "Select a single CSV/Excel File", os.getcwd())
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilters(["CSV Files (*.csv)", "Excel Files (*.xlsx *.xls)"])
        # Show the dialog and set the selected file path
        if dlg.exec_():
            selected = dlg.selectedFiles()[0]
            self.single_file_path = selected
            self.file_input.setText(selected)

    def on_multi_file_added(self, path):
        """Adds a selected file to the list of multi-files."""
        if path not in self.multi_file_paths:
            self.multi_file_paths.append(path)

    def on_multi_file_removed(self, path):
        """Removes a file from the multi-file selection list."""
        if path in self.multi_file_paths:
            self.multi_file_paths.remove(path)

    def on_undo_clicked(self):
        """Clears selected files and resets the UI to its initial state."""
        self.single_file_path = None
        self.file_input.clear()
        self.multi_file_paths.clear()
        self.multi_file_area.clear_attachments()
        self.merge_radio.setChecked(True)

    def on_run_clicked(self):
        """Prints the selected mode (Merge or Mirror) when the Run button is clicked."""
        mode = "Merge" if self.merge_radio.isChecked() else "Mirror"
        print("Mode:", mode)
