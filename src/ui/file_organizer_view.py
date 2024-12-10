from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QDesktopWidget,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.automation.file_organizer import (
    detect_duplicates,
    rename_files,
    sort_by_date,
    sort_by_size,
    sort_by_type,
    undo_last_operation,
)
from src.ui.components import (
    InfoWindow,
    ScheduleModalWindow,
    create_button,
    create_card,
    create_folder_input,
    create_icon_button,
    create_separator,
)
from src.ui.style import BLUE_BUTTON_STYLE, FILE_ORGANIZER_DIALOG_STYLE, GRAY_BUTTON_STYLE, GREEN_BUTTON_STYLE


# Dialog class for configuring file organization options
class FileOrganizerCustomizationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organize Files")
        self.setFixedSize(400, 600)

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
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Icon
        icon_label = QLabel()
        icon_pixmap = QPixmap("assets/photos/file_management.png")  # Icon by Uniconlabs
        icon_pixmap = icon_pixmap.scaled(39, 39, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setContentsMargins(0, 10, 0, 1)
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
        layout.addSpacing(5)

        # Folder selection section
        folder_layout = QHBoxLayout()
        self.folder_input = create_folder_input()
        folder_layout.addWidget(self.folder_input)

        self.folder_icon_btn = create_icon_button(
            icon_path="assets/photos/folder.png",
            icon_size=(25, 25),
            button_size=(30, 30),
        )

        self.folder_icon_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_icon_btn)
        layout.addLayout(folder_layout)

        # Initialize checkboxes list
        self.checkboxes = []

        # Sorting Operations Card
        sorting_labels = ["Sort by Type", "Sort by Date", "Sort by Size"]
        sorting_info_text = "Organize your files by type, date, or size. The app will create relevant folders in your target directory and move your files accordingly. \n\nNeed to revert? Use the Undo option to return to the previous state."
        sorting_card = self.build_checkbox_card(sorting_labels, info_text=sorting_info_text)
        layout.addWidget(sorting_card)

        # Detect Duplicates Card
        detect_duplicates_labels = ["Detect Duplicates"]
        detect_duplicates_info_text = "Identify and manage duplicate files by comparing their unique hashes. \n\nAll duplicates are relocated to a dedicated folder, helping you keep your storage clean and organized."
        detect_duplicates_card = self.build_checkbox_card(
            detect_duplicates_labels, info_text=detect_duplicates_info_text
        )
        layout.addWidget(detect_duplicates_card)

        # Rename Files Card
        rename_files_labels = ["Rename Files"]
        rename_files_info_text = "Rename your files by appending the date and hour of the operation. \n\nThis ensures each file name is unique and time-stamped for better organization."
        rename_files_card = self.build_checkbox_card(rename_files_labels, info_text=rename_files_info_text)
        layout.addWidget(rename_files_card)

        # Compress and Backup Files Card
        management_labels = ["Compress Files", "Backup Files"]
        management_info_text = "Compress or back up your files in one step. \n\nCreate ZIP archives to save space and simplify sharing, while also you can copy your important data to a backup folder to ensure they're safely stored."
        management_card = self.build_checkbox_card(management_labels, info_text=management_info_text)
        layout.addWidget(management_card)

        # Button layout for main interface buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Schedule Button aligned to the left
        self.schedule_btn = create_button("Auto", GREEN_BUTTON_STYLE, size=(50, 30))
        self.schedule_btn.clicked.connect(self.open_schedule_modal)
        button_layout.addWidget(self.schedule_btn, alignment=Qt.AlignLeft)

        # Spacer to push Undo and Run buttons to the right
        button_layout.addStretch()

        # Undo button using reusable component
        self.undo_btn = create_button("Undo", GRAY_BUTTON_STYLE)
        self.undo_btn.clicked.connect(self.on_undo_clicked)
        button_layout.addWidget(self.undo_btn)

        # Run button using reusable component
        self.run_btn = create_button("Run", BLUE_BUTTON_STYLE)
        self.run_btn.clicked.connect(self.on_run_clicked)
        button_layout.addWidget(self.run_btn)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def build_checkbox_card(self, labels, margins=(10, 10, 10, 10), spacing=3, info_text=""):
        """
        Build a card widget containing checkboxes with the relevant labels and an info icon placed to the right.
        """

        content_widgets = []

        # Loop through all labels to create checkboxes
        for idx, label in enumerate(labels):
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(lambda state, cb=checkbox: self.single_selection(cb))
            self.checkboxes.append(checkbox)
            self.checkbox_dict[label] = checkbox  # Store in dictionary

            # Create a horizontal layout for each checkbox and info icon
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(0)

            # Add checkbox to the layout
            row_layout.addWidget(checkbox)

            # For the first checkbox, add the info icon to the right
            if idx == 0:
                # Spacer to push the info icon to the right
                row_layout.addStretch()

                # Create info icon button
                info_button = create_icon_button(
                    icon_path="assets/photos/info.png",
                    icon_size=(16, 16),
                    button_size=(20, 20),
                )
                # Connect the info button to show info window
                info_button.clicked.connect(lambda _, text=info_text: self.show_info_window(text))

                # Add info button to the layout
                row_layout.addWidget(info_button)

            row_widget.setLayout(row_layout)
            content_widgets.append(row_widget)

            # Add separator if not the last checkbox
            if idx < len(labels) - 1:
                content_widgets.append(create_separator())

        # Create and return the card
        card = create_card(content_widgets, margins=margins, spacing=spacing)
        return card

    def show_info_window(self, info_text):
        """
        Displays an info window with the provided information text.
        """
        self.info_window = InfoWindow(info_text, parent=self)
        # Center the info window over the parent dialog
        parent_center = self.geometry().center()
        window_geometry = self.info_window.frameGeometry()
        window_geometry.moveCenter(parent_center)
        self.info_window.move(window_geometry.topLeft())
        self.info_window.show()

    def on_run_clicked(self):
        """
        Executes the selected organization operation.
        """
        folder_path = self.folder_input.text()  # Get the selected folder path
        if not folder_path:
            self.parent().update_status("Please select a folder to organize.")
            return

        try:
            # If an operation is checked, run that operation
            if any(checkbox.isChecked() for checkbox in self.checkboxes):
                if self.checkbox_dict.get("Sort by Type", None) and self.checkbox_dict["Sort by Type"].isChecked():
                    sort_by_type(folder_path)
                    self.parent().update_status("Files sorted by type successfully.")
                elif self.checkbox_dict.get("Sort by Date", None) and self.checkbox_dict["Sort by Date"].isChecked():
                    sort_by_date(folder_path)
                    self.parent().update_status("Files sorted by date successfully.")
                elif self.checkbox_dict.get("Sort by Size", None) and self.checkbox_dict["Sort by Size"].isChecked():
                    sort_by_size(folder_path)
                    self.parent().update_status("Files sorted by size successfully.")
                elif (
                    self.checkbox_dict.get("Detect Duplicates", None)
                    and self.checkbox_dict["Detect Duplicates"].isChecked()
                ):
                    detect_duplicates(folder_path)
                    self.parent().update_status("Duplicate files detected and moved successfully.")
                elif self.checkbox_dict.get("Rename Files", None) and self.checkbox_dict["Rename Files"].isChecked():
                    rename_files(folder_path)
                    self.parent().update_status("Files renamed successfully.")
            else:
                self.parent().update_status("Please select an operation to run.")
        except ValueError as e:
            self.parent().update_status(str(e))
        except Exception as e:
            self.parent().update_status(f"An unexpected error occurred: {str(e)}")

    def open_schedule_modal(self):
        """
        Opens the Schedule Modal Window for setting automation schedules.
        """
        schedule_modal = ScheduleModalWindow(self)  # Pass self as the parent
        # Center the modal relative to the FileOrganizerCustomizationDialog
        parent_center = self.geometry().center()
        modal_geometry = schedule_modal.frameGeometry()
        modal_geometry.moveCenter(parent_center)
        schedule_modal.move(modal_geometry.topLeft())

        result = schedule_modal.exec_()
        if result == QDialog.Accepted:
            # Retrieve the scheduled time and days
            scheduled_time = schedule_modal.time_edit.time().toString("HH:mm")
            selected_days = [day for day, btn in schedule_modal.day_buttons.items() if btn.isChecked()]
            # Update status or handle the scheduling as needed
            self.update_status(f"Scheduled at {scheduled_time} on: {', '.join(selected_days)}.")

    def center_modal(self, modal):
        """
        Centers the given modal relative to the parent window.
        """
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            parent_center = parent_geometry.center()
            modal_geometry = modal.frameGeometry()
            modal_geometry.moveCenter(parent_center)
            modal.move(modal_geometry.topLeft())
        else:
            # Fallback to centering on the screen if no parent is set
            screen_center = QDesktopWidget().availableGeometry().center()
            modal_geometry = modal.frameGeometry()
            modal_geometry.moveCenter(screen_center)
            modal.move(modal_geometry.topLeft())

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
