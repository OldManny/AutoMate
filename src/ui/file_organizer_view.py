from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QCheckBox,
    QLabel,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QHBoxLayout,
)


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
        self.folder_label = QLabel("Folder:")  # Label for folder path
        folder_layout.addWidget(self.folder_label)

        self.folder_input = QLineEdit(self)  # Input field to display folder path
        self.folder_input.setReadOnly(True)  # Make folder input field read-only
        folder_layout.addWidget(self.folder_input)

        self.folder_btn = QPushButton(
            "Select Folder", self
        )  # Button to open folder dialog
        self.folder_btn.clicked.connect(
            self.select_folder
        )  # Connect button to folder selection
        folder_layout.addWidget(self.folder_btn)

        layout.addLayout(folder_layout)  # Add folder selection layout to main layout

        # Step 2: Checkboxes for different organization rules
        self.sort_by_type = QCheckBox("Sort by Type")
        layout.addWidget(self.sort_by_type)

        self.sort_by_date = QCheckBox("Sort by Date")
        layout.addWidget(self.sort_by_date)

        self.sort_by_size = QCheckBox("Sort by Size")
        layout.addWidget(self.sort_by_size)

        self.detect_duplicates = QCheckBox("Detect Duplicates")
        layout.addWidget(self.detect_duplicates)

        self.rename_files = QCheckBox("Rename Files")
        layout.addWidget(self.rename_files)

        self.compress_files = QCheckBox("Compress Files")
        layout.addWidget(self.compress_files)

        self.backup_files = QCheckBox("Backup Files")
        layout.addWidget(self.backup_files)

        # Step 3: Button to initiate file organization automation
        self.run_btn = QPushButton("Run Automation", self)
        layout.addWidget(self.run_btn)

        # Button to undo the last automation action
        self.undo_btn = QPushButton("Undo Last Action", self)
        layout.addWidget(self.undo_btn)

        self.setLayout(layout)  # Set the layout of the dialog

    def select_folder(self):
        """Opens a folder dialog to select a directory, displaying the selected path in the input field."""
        options = QFileDialog.Options()  # Dialog options
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", options=options
        )  # Get selected folder path
        if folder:
            self.folder_input.setText(folder)  # Display selected folder path

    def center(self):
        """Centers the dialog on the screen relative to the parent window."""
        qr = self.frameGeometry()  # Get the geometry of the dialog
        cp = (
            self.parent().frameGeometry().center()
        )  # Get the center point of the parent window
        qr.moveCenter(cp)  # Move dialog geometry to center point
        self.move(qr.topLeft())  # Set dialog position
