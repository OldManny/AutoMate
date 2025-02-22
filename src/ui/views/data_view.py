from datetime import datetime
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

from src.automation.data_entry import merge_data, mirror_data
from src.ui.components.components import (
    create_button,
    create_card,
    create_folder_input,
    create_icon_button,
    create_separator,
)
from src.ui.components.file_attachment import FileAttachmentWidget
from src.ui.components.toast_notification import ToastNotification
from src.ui.modals.info_modal import InfoWindow
from src.ui.modals.schedule_modal import ScheduleModalWindow
from src.ui.style import BLUE_BUTTON_STYLE, GRAY_BUTTON_STYLE
from src.utils.undo_manager import undo_data_operation


class DataView(QWidget):
    """
    UI component for managing data files, allowing users to merge or mirror CSV/Excel files,
    always forcing a single 'Full Name' column.
    """

    CARD_FIXED_HEIGHT = 260  # Fixed height for the multi-file selection card

    def __init__(self, parent=None, scheduler_manager=None):
        super().__init__(parent)
        self.scheduler_manager = scheduler_manager
        self.setObjectName("DataView")

        self.single_file_path = None
        self.multi_file_paths = []

        # 1) Instantiate the toast
        self.toast = ToastNotification(self)

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

        info_header = QWidget()
        info_header_layout = QHBoxLayout(info_header)
        info_header_layout.setContentsMargins(10, 10, 0, 0)
        info_header_layout.setSpacing(5)

        info_text = QLabel("Drag and drop multiple CSV/Excel files below:")
        info_text.setStyleSheet("color: #C9D3D5; font-size: 12px;")
        info_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_header_layout.addWidget(info_text)

        info_button = create_icon_button(
            icon_path="assets/icons/info.png",
            icon_size=(16, 16),
            button_size=(20, 20),
        )
        info_button.clicked.connect(
            lambda: self.show_info_window(
                "Merge combines data from multiple files into a single master, "
                "while Mirror copies the master’s contents to every other file."
                "\n\nThis workflow keeps everything synchronized and updated."
            )
        )
        info_header_layout.addWidget(info_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        card_layout.addWidget(info_header)

        self.multi_file_area = FileAttachmentWidget()
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

        # Action Buttons (Undo / Run)
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

    def clear_form(self):
        """Clears selected files and resets the UI to its initial state."""
        self.single_file_path = None
        self.file_input.clear()
        self.multi_file_paths.clear()
        self.multi_file_area.clear_attachments()
        self.merge_radio.setChecked(True)

    def on_run_clicked(self):
        """Perform merge or mirror immediately, always forcing single 'Full Name' column."""
        mode = "Merge" if self.merge_radio.isChecked() else "Mirror"
        if not self.single_file_path:
            self.toast.show_message("No master file selected.", "info")
            return
        if not self.multi_file_paths:
            self.toast.show_message("No additional files selected.", "info")
            return

        if mode == "Merge":
            merge_data(
                source_directory=self.single_file_path,
                data_params={
                    "master_file": self.single_file_path,
                    "other_files": self.multi_file_paths,
                    "column_map": None,
                    "mode": "merge",
                    "force_single_name_col": True,  # Force a single Full Name column
                },
            )
        else:  # Mirror
            mirror_data(
                source_directory=self.single_file_path,
                data_params={
                    "master_file": self.single_file_path,
                    "other_files": self.multi_file_paths,
                    "column_map": None,
                    "mode": "mirror",
                    "force_single_name_col": True,  # Force single name col
                },
            )

        self.toast.show_message(f"{mode} completed", "success")

    def on_undo_clicked(self):
        """Handles the Undo button click by attempting to revert the last data operation."""
        try:
            undo_data_operation()
            self.toast.show_message("Undo successful", "success")
            # Update UI state
            # self.clear_form()
        except Exception as e:
            self.toast.show_message(f"Undo failed: {str(e)}", "error")

    def open_schedule_modal(self):
        """Open the ScheduleModalWindow for merging or mirroring tasks."""
        if not self.single_file_path or not self.multi_file_paths:
            self.toast.show_message("Select files first", "info")
            return

        schedule_modal = ScheduleModalWindow(self)
        schedule_modal.schedule_saved.connect(self.on_schedule_saved)
        schedule_modal.schedule_canceled.connect(self.on_schedule_canceled)

        self.center_modal(schedule_modal)
        schedule_modal.exec_()

    def on_schedule_saved(self, selected_time, selected_days):
        """Handle scheduling a data operation to be run at the specified time/days."""

        if self.merge_radio.isChecked():
            task_type = "merge_data"
            operation_mode = "Merge"
        else:
            task_type = "mirror_data"
            operation_mode = "Mirror"

        # Create data params dictionary
        data_params = {
            "master_file": self.single_file_path,
            "other_files": self.multi_file_paths,
            "column_map": None,
            "mode": operation_mode,
            "force_single_name_col": True,
        }

        if self.scheduler_manager:
            try:
                # Add the scheduled job
                job_id = self.scheduler_manager.add_scheduled_job(
                    task_type=task_type,
                    folder_target=self.single_file_path,
                    run_time=selected_time,
                    recurring_days=selected_days,
                    job_id=f"{task_type}_{datetime.now().timestamp()}",
                    data_params=data_params,
                )
                self.scheduler_manager.job_metadata[job_id]["data_params"] = data_params

                if selected_days:
                    days_list = ", ".join(selected_days)
                    self.toast.show_message(
                        f"{operation_mode} scheduled for {selected_time}\non {days_list}", "success"
                    )
                else:
                    self.toast.show_message(f"{operation_mode} scheduled for {selected_time}", "success")

                # Clear the form after successful scheduling
                self.clear_form()

            except Exception as e:
                self.toast.show_message(f"Failed to schedule: {str(e)}", "error")
                return

    def on_schedule_canceled(self):
        """Handle scheduling canceled."""
        self.toast.show_message("Scheduling canceled", "info")

    def center_modal(self, modal):
        """Centers the modal relative to the main window."""
        main_window = self.window()
        if main_window:
            center = main_window.geometry().center()
            g = modal.frameGeometry()
            g.moveCenter(center)
            modal.move(g.topLeft())
