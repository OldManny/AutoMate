from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from src.automation.scheduler_manager import TASK_LABELS
from src.ui.base_modal import BaseModalWindow
from src.ui.components import create_button, create_icon_button, create_separator
from src.ui.style import BLUE_BUTTON_STYLE, INFO_WINDOW_STYLE

# Abbreviations for day names
DAY_ABBREVIATIONS = {
    'Monday': 'Mon',
    'Tuesday': 'Tue',
    'Wednesday': 'Wed',
    'Thursday': 'Thu',
    'Friday': 'Fri',
    'Saturday': 'Sat',
    'Sunday': 'Sun',
}


class ElidedLabel(QLabel):
    """
    Custom QLabel that truncates text with ellipsis if it exceeds the max width.
    Displays the full text as a tooltip.
    """

    def __init__(self, text, max_width=None, font_size=None):
        super().__init__(text)
        self.full_text = text
        self.max_width = max_width
        self.setToolTip(text)  # Show full text in tooltip

        if max_width:
            self.setMaximumWidth(max_width)
        if font_size:
            self.setStyleSheet(f"font-size: {font_size}pt;")

    def paintEvent(self, event):
        """Override to render elided text if necessary."""
        if self.max_width:
            metrics = self.fontMetrics()
            if metrics.horizontalAdvance(self.full_text) > self.max_width:
                elided_text = metrics.elidedText(self.full_text, Qt.ElideMiddle, self.max_width)
                if self.text() != elided_text:
                    self.setText(elided_text)
        super().paintEvent(event)


class RunningJobsModal(BaseModalWindow):
    """
    Modal window for displaying scheduled jobs in a table-like format.
    Allows users to view details and cancel individual jobs.
    """

    COLUMN_WIDTHS = {"Type": 93, "Target": 120, "Time": 30, "Days": 50, "Cancel": 13}

    def __init__(self, scheduler_manager, parent=None):
        super().__init__(width=400, height=400, style_sheet=INFO_WINDOW_STYLE, parent=parent)
        self.scheduler_manager = scheduler_manager
        self.jobs_container_layout = None
        self.header_spacing = 5  # Default spacing between header columns
        self.font_size = 12  # Default font size for text
        self.init_ui()

    def init_ui(self):
        """Sets up the modal UI, including headers, job list, and controls."""
        # Clear existing layout if refreshing
        if self.main_layout.count():
            for i in reversed(range(self.main_layout.count())):
                item = self.main_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()

        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(self.header_spacing)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header_widths = {"Type": 90, "Target": 125, "Time": 9, "Days": 9, "": 10}  # Cancel column

        for text, width_percent in header_widths.items():
            label = QLabel(text)
            label.setStyleSheet(
                f"""
                font-weight: bold;
                color: #C9D3D5;
                font-size: {self.font_size}pt;
            """
            )
            label.setAlignment(Qt.AlignLeft)
            label.setMinimumWidth(int(self.width() * width_percent / 100))
            header_layout.addWidget(label)

        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(15)
        self.main_layout.addWidget(header_widget)

        # Separator below header
        self.main_layout.addWidget(create_separator())

        # Scrollable job container
        self.jobs_container = QWidget()
        self.jobs_container_layout = QVBoxLayout(self.jobs_container)
        self.jobs_container_layout.setContentsMargins(0, 0, 0, 0)
        self.jobs_container_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.jobs_container)
        scroll_area.setStyleSheet("border: none;")
        self.main_layout.addWidget(scroll_area)

        # Separator above bottom controls
        self.main_layout.addWidget(create_separator())

        # Bottom button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        ok_button = create_button("OK", BLUE_BUTTON_STYLE)
        ok_button.clicked.connect(self.accept)
        ok_button.setStyleSheet(ok_button.styleSheet() + f"font-size: {self.font_size}pt;")
        button_layout.addWidget(ok_button)

        button_container = QWidget()
        button_container.setLayout(button_layout)
        self.main_layout.addWidget(button_container)

        # Populate job rows
        self.populate_jobs()

    def set_header_spacing(self, spacing):
        """Adjust the spacing between header columns."""
        self.header_spacing = spacing
        self.init_ui()

    def set_font_size(self, size):
        """Adjust the font size for all UI elements."""
        self.font_size = size
        self.init_ui()

    def format_time(self, time_str):
        """Format a time string into HH:MM format."""
        try:
            if isinstance(time_str, str):
                dt = datetime.fromisoformat(time_str)
                return dt.strftime("%H:%M")
            elif isinstance(time_str, datetime):
                return time_str.strftime("%H:%M")
        except ValueError as e:
            print(f"Error parsing time: {e}")
        return time_str or "-"

    def format_days(self, days_list):
        """Convert full day names to abbreviations, or return '-' if empty."""
        if not days_list or not isinstance(days_list, list):
            return "-"
        return ", ".join(DAY_ABBREVIATIONS.get(day, day) for day in days_list)

    def populate_jobs(self):
        """Populate the job list with rows for each scheduled job."""
        for i in reversed(range(self.jobs_container_layout.count())):
            widget = self.jobs_container_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        jobs = self.scheduler_manager.list_scheduled_jobs()
        for row_index, job_info in enumerate(jobs):
            row_widget = self.create_job_row(job_info, row_index)
            self.jobs_container_layout.addWidget(row_widget)

        self.jobs_container_layout.setAlignment(Qt.AlignTop)

    def create_job_row(self, job_info, row_index):
        """Create a row for a single job's details."""
        background_color = "#333333" if row_index % 2 == 0 else "#494949"

        task_type = job_info.get("task_type", "Unknown")
        folder_target = job_info.get("folder_target", "-")
        next_run = self.format_time(job_info.get("next_run_time"))
        recurring_days = self.format_days(job_info.get("recurring_days", []))
        job_id = job_info.get("job_id")

        friendly_type = TASK_LABELS.get(task_type, task_type)

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(5, 0, 5, 0)
        row_layout.setSpacing(5)

        row_data = {"Type": friendly_type, "Target": folder_target, "Time": next_run, "Days": recurring_days}

        for column_name, text in row_data.items():
            label = ElidedLabel(text, max_width=self.COLUMN_WIDTHS[column_name], font_size=self.font_size)
            label.setAlignment(Qt.AlignLeft)
            label.setFixedWidth(self.COLUMN_WIDTHS[column_name])
            row_layout.addWidget(label)

        cancel_btn = create_icon_button("assets/photos/cancel.png", icon_size=(11, 11), button_size=(13, 13))
        cancel_btn.setToolTip("Cancel this scheduled operation")
        cancel_btn.clicked.connect(lambda _, j_id=job_id: self.on_cancel_job(j_id))
        cancel_btn.setFixedWidth(self.COLUMN_WIDTHS["Cancel"])
        row_layout.addWidget(cancel_btn)

        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        row_widget.setStyleSheet(f"background-color: {background_color}; font-size: {self.font_size}pt;")
        return row_widget

    def on_cancel_job(self, job_id):
        """Remove a job and refresh the job list."""
        self.scheduler_manager.remove_scheduled_job(job_id)
        self.populate_jobs()
