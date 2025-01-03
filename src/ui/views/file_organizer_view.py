from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from daemon import TASK_LABELS
from src.automation.file_organizer import (
    backup_files,
    compress_files,
    detect_duplicates,
    rename_files,
    sort_by_date,
    sort_by_size,
    sort_by_type,
    undo_last_operation,
)
from src.ui.components.components import (
    create_button,
    create_card,
    create_folder_input,
    create_icon_button,
    create_separator,
)
from src.ui.components.toast_notification import ToastNotification
from src.ui.modals.info_modal import InfoWindow
from src.ui.modals.schedule_modal import ScheduleModalWindow
from src.ui.style import BLUE_BUTTON_STYLE, GRAY_BUTTON_STYLE


class FileOrganizerCustomizationDialog(QWidget):
    def __init__(self, parent=None, scheduler_manager=None):
        super().__init__(parent)
        self.scheduler_manager = scheduler_manager

        # Initialize the checkbox dictionary
        self.checkbox_dict = {}

        self.setObjectName("FileOrganizerDialog")
        self.toast = ToastNotification(self)

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
            icon_size=(29, 29),
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
        detect_duplicates_info_text = "Identify and manage duplicate files by comparing their unique hashes. \n\nAll duplicates are relocated to a dedicated folder, helping you to keep your storage clean and organized."
        detect_duplicates_card = self.build_checkbox_card(
            detect_duplicates_labels, info_text=detect_duplicates_info_text
        )
        layout.addWidget(detect_duplicates_card)

        # Rename Files Card
        rename_files_labels = ["Rename Files"]
        rename_files_info_text = "Rename your files by appending the date and hour of the operation. \n\nThis ensures each file name is unique and time stamped for better organization."
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

    def show_status(self, message, message_type="info"):
        """Shows a toast notification with the given message and type."""
        self.toast.show_message(message, message_type)

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
        # Center the info window over the main window instead of the widget
        main_window = self.window()
        if main_window:
            main_window_center = main_window.geometry().center()
            window_geometry = self.info_window.frameGeometry()
            window_geometry.moveCenter(main_window_center)
            self.info_window.move(window_geometry.topLeft())
        self.info_window.show()

    def on_run_clicked(self):
        """
        Executes the selected organization operation.
        """
        folder_path = self.folder_input.text()  # Get the selected folder path
        if not folder_path:
            self.show_status("Select a folder", "info")
            return

        try:
            # If an operation is checked, run that operation
            if any(checkbox.isChecked() for checkbox in self.checkboxes):
                if self.checkbox_dict.get("Sort by Type", None) and self.checkbox_dict["Sort by Type"].isChecked():
                    sort_by_type(folder_path)
                    self.show_status("Files sorted by type", "success")
                elif self.checkbox_dict.get("Sort by Date", None) and self.checkbox_dict["Sort by Date"].isChecked():
                    sort_by_date(folder_path)
                    self.show_status("Files sorted by date", "success")
                elif self.checkbox_dict.get("Sort by Size", None) and self.checkbox_dict["Sort by Size"].isChecked():
                    sort_by_size(folder_path)
                    self.show_status("Files sorted by size", "success")
                elif (
                    self.checkbox_dict.get("Detect Duplicates", None)
                    and self.checkbox_dict["Detect Duplicates"].isChecked()
                ):
                    detect_duplicates(folder_path)
                    self.show_status("Duplicate files moved", "success")
                elif self.checkbox_dict.get("Rename Files", None) and self.checkbox_dict["Rename Files"].isChecked():
                    rename_files(folder_path)
                    self.show_status("Files renamed", "success")
                elif (
                    self.checkbox_dict.get("Compress Files", None) and self.checkbox_dict["Compress Files"].isChecked()
                ):
                    compress_files(folder_path)
                    self.show_status("Files compressed", "success")
                elif self.checkbox_dict.get("Backup Files", None) and self.checkbox_dict["Backup Files"].isChecked():
                    backup_files(folder_path)
                    self.show_status("Backup completed", "success")
            else:
                self.show_status("Select an operation", "info")
        except ValueError as e:
            self.show_status(str(e))
        except Exception as e:
            self.show_status(f"An unexpected error occurred: {str(e)}", "error")

    def open_schedule_modal(self):
        """
        Opens the Schedule Modal Window for setting automation schedules.
        """
        schedule_modal = ScheduleModalWindow(self)

        # Connect signals for notifications
        schedule_modal.schedule_saved.connect(self.on_schedule_saved)
        schedule_modal.schedule_canceled.connect(self.on_schedule_canceled)

        # Center the modal relative to the main window
        self.center_modal(schedule_modal)
        schedule_modal.exec_()

    def on_schedule_saved(self, selected_time, selected_days):
        """
        Handles the schedule saved signal. Schedules the currently selected operation.
        """
        folder_path = self.folder_input.text()
        if not folder_path:
            self.show_status("Select a folder", "info")
            return

        # Determine which operation is checked (only one can be checked per your single_selection logic)
        selected_task_type = None
        if self.checkbox_dict.get("Sort by Type") and self.checkbox_dict["Sort by Type"].isChecked():
            selected_task_type = "sort_by_type"
        elif self.checkbox_dict.get("Sort by Date") and self.checkbox_dict["Sort by Date"].isChecked():
            selected_task_type = "sort_by_date"
        elif self.checkbox_dict.get("Sort by Size") and self.checkbox_dict["Sort by Size"].isChecked():
            selected_task_type = "sort_by_size"
        elif self.checkbox_dict.get("Detect Duplicates") and self.checkbox_dict["Detect Duplicates"].isChecked():
            selected_task_type = "detect_duplicates"
        elif self.checkbox_dict.get("Rename Files") and self.checkbox_dict["Rename Files"].isChecked():
            selected_task_type = "rename_files"
        elif self.checkbox_dict.get("Compress Files") and self.checkbox_dict["Compress Files"].isChecked():
            selected_task_type = "compress_files"
        elif self.checkbox_dict.get("Backup Files") and self.checkbox_dict["Backup Files"].isChecked():
            selected_task_type = "backup_files"

        if not selected_task_type:
            self.show_status("Select an operation", "info")
            return

        # Now schedule using our shared SchedulerManager
        if self.scheduler_manager:
            self.scheduler_manager.add_scheduled_job(
                task_type=selected_task_type,
                folder_target=folder_path,
                run_time=selected_time,
                recurring_days=selected_days,
            )

        # Give the user feedback
        user_friendly = TASK_LABELS.get(selected_task_type, selected_task_type)
        if selected_days:
            days_list = ", ".join(selected_days)
            self.show_status(f"{user_friendly} will run at {selected_time}\non {days_list}", "success")
        else:
            self.show_status(f"{user_friendly} will run at {selected_time}", "success")

    def on_schedule_canceled(self):
        """Handles the schedule canceled signal and shows a toast notification."""
        self.show_status("Scheduling canceled", "info")

    def center_modal(self, modal):
        """
        Centers the given modal relative to the main window.
        """
        main_window = self.window()
        if main_window:
            main_window_center = main_window.geometry().center()
            modal_geometry = modal.frameGeometry()
            modal_geometry.moveCenter(main_window_center)
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

    def on_undo_clicked(self):
        """
        Handles the Undo button click to revert the last file organization operation.
        """
        try:
            undo_last_operation()
            self.show_status("Undone", "success")
        except ValueError as e:
            self.show_status(str(e))
        except Exception as e:
            self.show_status(f"An unexpected error occurred: {str(e)}", "error")
