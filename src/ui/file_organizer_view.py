from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QDesktopWidget, QDialog, QFileDialog, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from src.automation.file_organizer import sort_by_date, sort_by_size, sort_by_type, undo_last_operation
from src.ui.components import create_blue_button, create_card, create_folder_icon_button, create_folder_input, create_gray_button, create_separator
from src.ui.style import FILE_ORGANIZER_DIALOG_STYLE


# Dialog class for configuring file organization options
class FileOrganizerCustomizationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organize Files")
        self.setFixedSize(400, 620)

        # Initialize the checkbox dictionary
        self.checkbox_dict = {}

        # Set the style sheet
        self.setStyleSheet(FILE_ORGANIZER_DIALOG_STYLE)

        # Disable the window's resizing feature
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowMaximizeButtonHint)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header section
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 10, 0, 0)  # Adjust top margin to reduce space
        header_layout.setSpacing(5)
        header_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Icon
        icon_label = QLabel()
        icon_pixmap = QPixmap("assets/photos/file_management.png")  # Icon by Uniconlabs
        icon_pixmap = icon_pixmap.scaled(43, 43, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setContentsMargins(0, 0, 0, 5)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        # Description text
        short_description = QLabel("Manage your files efficiently with options to\nsort, detect duplicates, and more.")
        short_description.setAlignment(Qt.AlignCenter)
        short_description.setWordWrap(True)
        short_description.setStyleSheet("color: #C9D3D5; font-size: 12px;")
        short_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Add widgets to header layout
        header_layout.addWidget(icon_label)
        header_layout.addWidget(short_description)

        # Add the header to the main layout
        layout.addWidget(header_widget)

        # Add a separator line after the header
        separator_line = create_separator()
        layout.addWidget(separator_line)
        layout.addSpacing(15)

        # Folder selection section
        folder_layout = QHBoxLayout()
        self.folder_input = create_folder_input()
        folder_layout.addWidget(self.folder_input)

        self.folder_icon_btn = create_folder_icon_button()
        self.folder_icon_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_icon_btn)
        layout.addLayout(folder_layout)

        # Initialize checkboxes list
        self.checkboxes = []

        # Sorting Operations Card
        sorting_labels = ["Sort by Type", "Sort by Date", "Sort by Size"]
        sorting_card = self.build_checkbox_card(sorting_labels)
        layout.addWidget(sorting_card)

        # Detect Duplicates Card
        detect_duplicates_card = self.build_checkbox_card(["Detect Duplicates"])
        layout.addWidget(detect_duplicates_card)

        # Rename Files Card
        rename_files_card = self.build_checkbox_card(["Rename Files"])
        layout.addWidget(rename_files_card)

        # Compress and Backup Files Card
        management_labels = ["Compress Files", "Backup Files"]
        management_card = self.build_checkbox_card(management_labels)
        layout.addWidget(management_card)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Undo button using reusable component
        self.undo_btn = create_gray_button("Undo")
        self.undo_btn.clicked.connect(self.on_undo_clicked)
        button_layout.addWidget(self.undo_btn)

        # Run button using reusable component
        self.run_btn = create_blue_button("Run")
        self.run_btn.clicked.connect(self.on_run_clicked)
        button_layout.addWidget(self.run_btn)

        # Add buttons to main layout
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def build_checkbox_card(self, labels, margins=(10, 15, 10, 15), spacing=5):
        """
        Build a card widget containing checkboxes with the relevant labels.
        """
        checkboxes = []
        for label in labels:
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(lambda state, cb=checkbox: self.single_selection(cb))
            self.checkboxes.append(checkbox)
            checkboxes.append(checkbox)
            self.checkbox_dict[label] = checkbox  # Store in dictionary

        # Create content widgets with separators
        content_widgets = []
        for idx, checkbox in enumerate(checkboxes):
            content_widgets.append(checkbox)
            if idx < len(checkboxes) - 1:
                content_widgets.append(create_separator())

        # Create and return the card
        card = create_card(content_widgets, margins=margins, spacing=spacing)
        return card

    def on_run_clicked(self):
        """
        Executes the selected organization operation.
        """
        folder_path = self.folder_input.text()  # Get the selected folder path
        if not folder_path:
            self.parent().update_status("Please select a folder to organize.")
            return

        try:
            if any(checkbox.isChecked() for checkbox in self.checkboxes):
                if self.checkbox_dict["Sort by Type"].isChecked():
                    sort_by_type(folder_path)
                    self.parent().update_status("Files sorted by type successfully.")
                elif self.checkbox_dict["Sort by Date"].isChecked():
                    sort_by_date(folder_path)
                    self.parent().update_status("Files sorted by date successfully.")
                elif self.checkbox_dict["Sort by Size"].isChecked():
                    sort_by_size(folder_path)
                    self.parent().update_status("Files sorted by size successfully.")
                else:
                    self.parent().update_status("Please select an operation to run.")
            else:
                self.parent().update_status("Please select an operation to run.")
        except ValueError as e:
            self.parent().update_status(str(e))
        except Exception as e:
            self.parent().update_status(f"An unexpected error occurred: {str(e)}")

    def select_folder(self):
        """Opens a folder dialog to select a directory, displaying the selected path in the input field."""
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)  # Get selected folder path
        if folder:
            self.folder_input.setText(folder)  # Display selected folder path

    def single_selection(self, current_checkbox):
        """Ensures only one checkbox is selected at a time."""
        if current_checkbox.isChecked():
            for checkbox in self.checkboxes:
                if checkbox != current_checkbox:
                    checkbox.setChecked(False)

    def showEvent(self, event):
        """
        Overriding the showEvent, ensuring that the self center is called
        every time the dialog is shown.
        """
        super().showEvent(event)
        self.center()

    def center(self):
        """
        Centers the Organize Files window relative to its parent (main interface).
        """
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            parent_center = parent_geometry.center()
            dialog_geometry = self.frameGeometry()
            dialog_geometry.moveCenter(parent_center)
            self.move(dialog_geometry.topLeft())
        else:
            # Fallback to centering on the screen if no parent is set
            screen_center = QDesktopWidget().availableGeometry().center()
            dialog_geometry = self.frameGeometry()
            dialog_geometry.moveCenter(screen_center)
            self.move(dialog_geometry.topLeft())

    def on_undo_clicked(self):
        """
        Handles the Undo button click to revert the last file organization operation.
        """
        try:
            undo_last_operation()
            self.parent().update_status("The last operation was successfully undone.")
        except ValueError as e:
            self.parent().update_status(str(e))
        except Exception as e:
            self.parent().update_status(f"An unexpected error occurred: {str(e)}")
