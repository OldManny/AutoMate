from datetime import datetime
import os

from PyQt5.QtWidgets import QCheckBox, QDialog, QFileDialog, QHBoxLayout, QVBoxLayout, QWidget

from src.automation.file_organizer import sort_by_type, undo_last_operation
from src.ui.components import create_blue_button, create_folder_icon_button, create_folder_input, create_gray_button
from src.ui.style import CARD_STYLE


# Dialog class for configuring file organization options
class FileOrganizerCustomizationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organize Files")  # Set dialog window title
        self.resize(400, 400)  # Set initial size of the dialog
        self.center()  # Center the dialog on the screen

        layout = QVBoxLayout()  # Main layout for the dialog

        # Step 1: Folder selection section
        folder_layout = QHBoxLayout()  # Horizontal layout for folder selection

        # Folder input field and folder icon button using reusable components
        self.folder_input = create_folder_input()
        folder_layout.addWidget(self.folder_input)

        self.folder_icon_btn = create_folder_icon_button()  # Reusable icon button
        self.folder_icon_btn.clicked.connect(self.select_folder)  # Connect icon button to folder selection
        folder_layout.addWidget(self.folder_icon_btn)

        layout.addLayout(folder_layout)  # Add folder selection layout to main layout

        # Step 2: Checkbox area with rounded card style
        checkbox_card = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_card)
        checkbox_card.setStyleSheet(CARD_STYLE)  # Apply centralized card style

        # Checkboxes for different automations
        self.checkboxes = []  # List to store all checkboxes for single-selection logic
        self.sort_by_type = QCheckBox("Sort by Type")
        self.sort_by_type.stateChanged.connect(lambda: self.single_selection(self.sort_by_type))
        checkbox_layout.addWidget(self.sort_by_type)
        self.checkboxes.append(self.sort_by_type)

        self.sort_by_date = QCheckBox("Sort by Date")
        self.sort_by_date.stateChanged.connect(lambda: self.single_selection(self.sort_by_date))
        checkbox_layout.addWidget(self.sort_by_date)
        self.checkboxes.append(self.sort_by_date)

        self.sort_by_size = QCheckBox("Sort by Size")
        self.sort_by_size.stateChanged.connect(lambda: self.single_selection(self.sort_by_size))
        checkbox_layout.addWidget(self.sort_by_size)
        self.checkboxes.append(self.sort_by_size)

        self.detect_duplicates = QCheckBox("Detect Duplicates")
        self.detect_duplicates.stateChanged.connect(lambda: self.single_selection(self.detect_duplicates))
        checkbox_layout.addWidget(self.detect_duplicates)
        self.checkboxes.append(self.detect_duplicates)

        self.rename_files = QCheckBox("Rename Files")
        self.rename_files.stateChanged.connect(lambda: self.single_selection(self.rename_files))
        checkbox_layout.addWidget(self.rename_files)
        self.checkboxes.append(self.rename_files)

        self.compress_files = QCheckBox("Compress Files")
        self.compress_files.stateChanged.connect(lambda: self.single_selection(self.compress_files))
        checkbox_layout.addWidget(self.compress_files)
        self.checkboxes.append(self.compress_files)

        self.backup_files = QCheckBox("Backup Files")
        self.backup_files.stateChanged.connect(lambda: self.single_selection(self.backup_files))
        checkbox_layout.addWidget(self.backup_files)
        self.checkboxes.append(self.backup_files)

        layout.addWidget(checkbox_card)  # Add the card-styled widget to the main layout

        # Run and Undo Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Undo button using reusable component
        self.undo_btn = create_gray_button("Undo")
        button_layout.addWidget(self.undo_btn)
        self.undo_btn.clicked.connect(self.on_undo_clicked)

        # Run button using reusable component
        self.run_btn = create_blue_button("Run")
        self.run_btn.clicked.connect(self.on_run_clicked)  # Connect Run button to on_run_clicked method
        button_layout.addWidget(self.run_btn)

        layout.addLayout(button_layout)  # Add button layout to main layout
        self.setLayout(layout)

    def on_run_clicked(self):
        """Executes the selected organization operation."""
        folder_path = self.folder_input.text()  # Get the selected folder path
        if not folder_path:
            self.parent().update_status("Please select a folder to organize.")
            return

        # Check if any operation is selected
        if not any(checkbox.isChecked() for checkbox in self.checkboxes):
            self.parent().update_status("Please select an operation to perform.")
            return

        if self.sort_by_type.isChecked():
            try:
                sort_by_type(folder_path)  # Call sort_by_type with the selected folder path
                folder_name = os.path.basename(folder_path)
                timestamp = datetime.now().strftime("%H:%M on %Y-%m-%d")
                self.parent().update_status(f"{folder_name} folder was sorted by type at {timestamp}.")
            except Exception as e:
                self.parent().update_status(str(e))

    def select_folder(self):
        """Opens a folder dialog to select a directory, displaying the selected path in the input field."""
        options = QFileDialog.Options()  # Dialog options
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)  # Get selected folder path
        if folder:
            self.folder_input.setText(folder)  # Display selected folder path

    def single_selection(self, current_checkbox):
        """Ensures only one checkbox is selected at a time."""
        if current_checkbox.isChecked():
            for checkbox in self.checkboxes:
                if checkbox != current_checkbox:
                    checkbox.setChecked(False)

    def center(self):
        """Centers the dialog on the screen relative to the parent window."""
        qr = self.frameGeometry()  # Get the geometry of the dialog
        cp = self.parent().frameGeometry().center()  # Get the center point of the parent window
        qr.moveCenter(cp)  # Move dialog geometry to center point
        self.move(qr.topLeft())  # Set dialog position


def on_undo_clicked(self):
    """Handles the Undo button click to revert the last file organization operation."""
    try:
        undo_last_operation()  # Attempt to undo the last operation
        self.parent().update_status("The last operation was successfully undone.")  # Success message
    except ValueError as e:
        self.parent().update_status(str(e))  # Display user-friendly error message
    except Exception as e:
        self.parent().update_status(f"An unexpected error occurred: {str(e)}")  # Handle unexpected errors
