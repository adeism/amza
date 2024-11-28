import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QDateTimeEdit, QSpinBox, QRadioButton, QButtonGroup, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QStatusBar, QMessageBox, QCheckBox, QGridLayout,
    QHeaderView, QDialog, QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import QDateTime, QTimer, Qt
from PyQt6.QtGui import QIcon
import pygame
from datetime import datetime, timedelta


class WeeklyRecurrenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weekly Recurrence Settings")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Recur every
        recur_layout = QHBoxLayout()
        recur_layout.addWidget(QLabel("Recur every:"))
        self.weekly_interval_spinbox = QSpinBox()
        self.weekly_interval_spinbox.setRange(1, 52)
        self.weekly_interval_spinbox.setValue(1)
        recur_layout.addWidget(self.weekly_interval_spinbox)
        recur_layout.addWidget(QLabel("week(s)"))
        layout.addLayout(recur_layout)

        # Days checkboxes
        self.days_checkboxes = {
            "Monday": QCheckBox("Monday"),
            "Tuesday": QCheckBox("Tuesday"),
            "Wednesday": QCheckBox("Wednesday"),
            "Thursday": QCheckBox("Thursday"),
            "Friday": QCheckBox("Friday"),
            "Saturday": QCheckBox("Saturday"),
            "Sunday": QCheckBox("Sunday"),
        }
        days_layout = QHBoxLayout()
        for day in self.days_checkboxes.values():
            days_layout.addWidget(day)
        layout.addLayout(days_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self):
        interval = self.weekly_interval_spinbox.value()
        days = [day for day, checkbox in self.days_checkboxes.items() if checkbox.isChecked()]
        return interval, days


class MonthlyRecurrenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monthly Recurrence Settings")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Recur every
        recur_layout = QHBoxLayout()
        recur_layout.addWidget(QLabel("Recur every:"))
        self.monthly_interval_spinbox = QSpinBox()
        self.monthly_interval_spinbox.setRange(1, 12)
        self.monthly_interval_spinbox.setValue(1)
        recur_layout.addWidget(self.monthly_interval_spinbox)
        recur_layout.addWidget(QLabel("month(s)"))
        layout.addLayout(recur_layout)

        # Month checkboxes
        self.month_checkboxes = {
            "January": QCheckBox("January"),
            "February": QCheckBox("February"),
            "March": QCheckBox("March"),
            "April": QCheckBox("April"),
            "May": QCheckBox("May"),
            "June": QCheckBox("June"),
            "July": QCheckBox("July"),
            "August": QCheckBox("August"),
            "September": QCheckBox("September"),
            "October": QCheckBox("October"),
            "November": QCheckBox("November"),
            "December": QCheckBox("December"),
        }
        months_layout = QHBoxLayout()
        for month in self.month_checkboxes.values():
            months_layout.addWidget(month)
        layout.addLayout(months_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self):
        interval = self.monthly_interval_spinbox.value()
        months = [month for month, checkbox in self.month_checkboxes.items() if checkbox.isChecked()]
        return interval, months


class TaskScheduler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMZ Announcement")
        self.setGeometry(100, 100, 800, 600)

        # Initialize pygame for audio playback
        pygame.mixer.init()

        # Load reminders from JSON file
        self.reminders_file = "reminders.json"
        self.reminders = self.load_reminders()

        # Pre-audio directory
        self.pre_audio_dir = "preaudio"
        os.makedirs(self.pre_audio_dir, exist_ok=True)  # Ensure the directory exists

        # UI setup
        self.init_ui()

        # Timer to check reminders every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(1000)  # Check every 1 second

        # Timer to check if audio has finished playing
        self.audio_check_timer = QTimer()
        self.audio_check_timer.timeout.connect(self.check_audio_finished)
        self.audio_check_timer.start(500)  # Check every 500ms

        # Attributes for recurrence
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None

        # Attributes to track audio playback
        self.currently_playing_reminder = None
        self.currently_playing_button = None
        self.audio_looping = False

    def closeEvent(self, event):
        """Override close event to show confirmation dialog."""
        reply = QMessageBox.question(
            self,
            "Exit Confirmation",
            "Are you sure you want to exit the application?\n\nNote: If closed, reminders will not function.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def init_ui(self):
        self.create_central_widget()
        self.create_task_form()
        self.create_task_tables()
        self.create_status_bar()

    def create_central_widget(self):
        """Create central widget and main layout."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

    def create_task_form(self):
        """Create the task input form."""
        form_layout = QVBoxLayout()

        # Task Name
        task_name_layout = QHBoxLayout()
        task_name_layout.addWidget(QLabel("Task Name:"))
        self.task_name_edit = QLineEdit()
        task_name_layout.addWidget(self.task_name_edit)
        form_layout.addLayout(task_name_layout)

        # Start DateTime
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.start_datetime = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_datetime.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.start_datetime.setCalendarPopup(True)
        start_layout.addWidget(self.start_datetime)
        form_layout.addLayout(start_layout)

        # Recurrence Type
        recurrence_layout = QHBoxLayout()
        self.recurrence_group = QButtonGroup(self)

        self.one_time_radio = QRadioButton("One time")
        self.one_time_radio.setChecked(True)  # Default selection
        self.recurrence_group.addButton(self.one_time_radio)
        recurrence_layout.addWidget(self.one_time_radio)

        self.daily_radio = QRadioButton("Daily")
        self.recurrence_group.addButton(self.daily_radio)
        recurrence_layout.addWidget(self.daily_radio)

        self.weekly_radio = QRadioButton("Weekly")
        self.recurrence_group.addButton(self.weekly_radio)
        recurrence_layout.addWidget(self.weekly_radio)

        self.monthly_radio = QRadioButton("Monthly")
        self.recurrence_group.addButton(self.monthly_radio)
        recurrence_layout.addWidget(self.monthly_radio)

        form_layout.addLayout(recurrence_layout)

        # Audio File Upload and Loops
        audio_layout = QVBoxLayout()

        # Loops and Delay
        loops_delay_layout = QHBoxLayout()

        # Loops input
        loops_label = QLabel("Loops:")
        self.loops_spinbox = QSpinBox()
        self.loops_spinbox.setRange(1, 1000)
        self.loops_spinbox.setValue(1)

        loops_input_layout = QHBoxLayout()
        loops_input_layout.addWidget(loops_label)
        loops_input_layout.addWidget(self.loops_spinbox)
        loops_input_widget = QWidget()
        loops_input_widget.setLayout(loops_input_layout)

        loops_delay_layout.addWidget(loops_input_widget)

        # Delay input
        delay_label = QLabel("Delay between loops (s):")
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 3600)
        self.delay_spinbox.setValue(0)

        delay_input_layout = QHBoxLayout()
        delay_input_layout.addWidget(delay_label)
        delay_input_layout.addWidget(self.delay_spinbox)
        delay_input_widget = QWidget()
        delay_input_widget.setLayout(delay_input_layout)

        loops_delay_layout.addWidget(delay_input_widget)

        audio_layout.addLayout(loops_delay_layout)

        # Pre-Audio Selection and Preview Button
        pre_audio_layout = QHBoxLayout()
        self.pre_audio_combo = QComboBox()
        self.pre_audio_combo.setPlaceholderText("Select Pre-Audio")
        self.load_pre_audio_files()
        pre_audio_layout.addWidget(self.pre_audio_combo)

        self.preview_pre_audio_button = QPushButton("Preview")
        self.preview_pre_audio_button.clicked.connect(self.preview_pre_audio)
        self.preview_pre_audio_button.setFixedWidth(70)
        pre_audio_layout.addWidget(self.preview_pre_audio_button)
        audio_layout.addLayout(pre_audio_layout)

        # Main Audio Upload
        main_audio_layout = QHBoxLayout()
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setPlaceholderText("No audio selected")
        main_audio_layout.addWidget(self.audio_path_edit)

        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.upload_audio)
        main_audio_layout.addWidget(self.upload_button)

        # Preview Audio Button
        self.preview_audio_button = QPushButton("Preview")
        self.preview_audio_button.clicked.connect(self.preview_audio)
        main_audio_layout.addWidget(self.preview_audio_button)

        audio_layout.addLayout(main_audio_layout)

        form_layout.addLayout(audio_layout)

        # Add Reminder Button
        self.add_button = QPushButton("Add Reminder")
        self.add_button.clicked.connect(self.add_reminder)
        form_layout.addWidget(self.add_button)

        self.main_layout.addLayout(form_layout)

        # Connect recurrence selection
        self.recurrence_group.buttonClicked.connect(self.handle_recurrence_selection)

    def create_task_tables(self):
        """Create active and inactive task tables."""
        # Active Task Table
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(5)
        self.active_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "", ""])
        self.setup_table(self.active_table)
        self.main_layout.addWidget(self.active_table)

        # Inactive Task Table
        self.inactive_button = QPushButton("Show Inactive Tasks")
        self.inactive_button.clicked.connect(self.toggle_inactive_tasks)
        self.inactive_table = QTableWidget()
        self.inactive_table.setColumnCount(5)
        self.inactive_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "", ""])
        self.setup_table(self.inactive_table)
        self.inactive_table.setVisible(False)
        self.main_layout.addWidget(self.inactive_button)
        self.main_layout.addWidget(self.inactive_table)

        # Connect double click for editing
        self.active_table.cellDoubleClicked.connect(self.edit_reminder)
        self.inactive_table.cellDoubleClicked.connect(self.edit_reminder)

        # Refresh table on startup
        self.refresh_tables()

    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def setup_table(self, table):
        """Set up table properties for consistent UI/UX."""
        header = table.horizontalHeader()
        # Set resize modes for columns
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Task Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Start Time
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Recurrence
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Play Button
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Delete Button

        # Set fixed widths for play and delete columns
        table.setColumnWidth(3, 40)
        table.setColumnWidth(4, 40)

        # Align headers to center
        for i in range(table.columnCount()):
            item = table.horizontalHeaderItem(i)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def handle_recurrence_selection(self, button):
        """Handle recurrence type selection."""
        if button == self.weekly_radio:
            dialog = WeeklyRecurrenceDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.weekly_interval, self.weekly_days = dialog.get_values()
            else:
                # If the dialog is cancelled, revert to 'One time'
                self.one_time_radio.setChecked(True)
                self.weekly_interval = None
                self.weekly_days = None
        elif button == self.monthly_radio:
            dialog = MonthlyRecurrenceDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.monthly_interval, self.monthly_months = dialog.get_values()
            else:
                # If the dialog is cancelled, revert to 'One time'
                self.one_time_radio.setChecked(True)
                self.monthly_interval = None
                self.monthly_months = None
        else:
            # For 'One time' and 'Daily', reset recurrence settings
            self.weekly_interval = None
            self.weekly_days = None
            self.monthly_interval = None
            self.monthly_months = None

    def load_pre_audio_files(self):
        """Load pre-audio files from the preaudio directory into the combo box."""
        self.pre_audio_combo.clear()
        self.pre_audio_combo.addItem("None")  # Default option
        audio_files = [f for f in os.listdir(self.pre_audio_dir) if f.lower().endswith(('.mp3', '.wav'))]
        if audio_files:
            self.pre_audio_combo.addItems(audio_files)

    def preview_pre_audio(self):
        """Play the selected pre-audio file."""
        selected_file = self.pre_audio_combo.currentText()
        if selected_file and selected_file != "None":
            pre_audio_path = os.path.join(self.pre_audio_dir, selected_file)
            self.play_audio(pre_audio_path, loops=1)
        else:
            self.status_bar.showMessage("No pre-audio file selected.", 5000)

    def upload_audio(self):
        """Upload the main audio file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Main Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.audio_path_edit.setText(file_path)

    def add_reminder(self):
        """Add a reminder based on user inputs."""
        task_name = self.task_name_edit.text()
        start_time = self.start_datetime.dateTime().toSecsSinceEpoch()
        audio_file = self.audio_path_edit.text()
        pre_audio_file = self.pre_audio_combo.currentText()
        loops = self.loops_spinbox.value()
        delay_between_loops = self.delay_spinbox.value()

        if not task_name or not audio_file:
            self.status_bar.showMessage("Task name and main audio file are required!", 5000)
            return

        if pre_audio_file == "None":
            pre_audio_file = None

        recurrence = None
        if self.one_time_radio.isChecked():
            recurrence = {"type": "one_time"}
        elif self.daily_radio.isChecked():
            recurrence = {"type": "daily"}
        elif self.weekly_radio.isChecked():
            if not self.weekly_interval or not self.weekly_days:
                self.status_bar.showMessage("Weekly recurrence settings are missing!", 5000)
                return
            recurrence = {
                "type": "weekly",
                "interval": self.weekly_interval,
                "days": self.weekly_days,
            }
        elif self.monthly_radio.isChecked():
            if not self.monthly_interval or not self.monthly_months:
                self.status_bar.showMessage("Monthly recurrence settings are missing!", 5000)
                return
            recurrence = {
                "type": "monthly",
                "interval": self.monthly_interval,
                "months": self.monthly_months,
            }
        else:
            recurrence = {"type": "one_time"}  # Default

        reminder = {
            "task_name": task_name,
            "start_time": start_time,
            "recurrence": recurrence,
            "audio_file": audio_file,
            "pre_audio_file": pre_audio_file,
            "loops": loops,
            "delay_between_loops": delay_between_loops,
            "active": True,
        }
        self.reminders.append(reminder)
        self.save_reminders()
        self.refresh_tables()
        self.clear_inputs()
        self.status_bar.showMessage("Reminder added successfully!", 5000)

    def preview_audio(self):
        """Preview the selected audio file."""
        audio_file = self.audio_path_edit.text()
        if audio_file:
            self.play_audio(audio_file, loops=1)  # Play once for preview
        else:
            self.status_bar.showMessage("No audio file selected.", 5000)

    def toggle_inactive_tasks(self):
        """Toggle visibility of inactive tasks table."""
        is_visible = self.inactive_table.isVisible()
        self.inactive_table.setVisible(not is_visible)
        self.inactive_button.setText("Hide Inactive Tasks" if not is_visible else "Show Inactive Tasks")

    def clear_inputs(self):
        """Clear all input fields."""
        self.task_name_edit.clear()
        self.start_datetime.setDateTime(QDateTime.currentDateTime())
        self.loops_spinbox.setValue(1)
        self.delay_spinbox.setValue(0)
        self.one_time_radio.setChecked(True)
        self.load_pre_audio_files()  # Reload pre-audio files in case they have changed
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None
        self.audio_path_edit.clear()
        self.pre_audio_combo.setCurrentIndex(0) #Reset pre-audio selection


    def check_reminders(self):
        """Check and trigger reminders based on current time."""
        current_time = datetime.now().timestamp()
        for reminder in self.reminders:
            if reminder["active"] and reminder["start_time"] <= current_time:
                self.play_reminder(reminder)
                self.show_reminder_popup(reminder)

                # Handle recurrence
                recurrence = reminder.get("recurrence", {"type": "one_time"})
                rec_type = recurrence.get("type", "one_time")

                if rec_type == "one_time":
                    reminder["active"] = False  # Mark reminder as inactive
                elif rec_type == "daily":
                    # Add 1 day to start_time
                    reminder["start_time"] += 86400  # seconds in a day
                elif rec_type == "weekly":
                    interval = recurrence.get("interval", 1)
                    days = recurrence.get("days", [])
                    next_time = self.compute_next_weekly_occurrence(reminder["start_time"], interval, days)
                    if next_time:
                        reminder["start_time"] = next_time
                    else:
                        reminder["active"] = False  # No more occurrences
                elif rec_type == "monthly":
                    interval = recurrence.get("interval", 1)
                    months = recurrence.get("months", [])
                    next_time = self.compute_next_monthly_occurrence(reminder["start_time"], interval, months)
                    if next_time:
                        reminder["start_time"] = next_time
                    else:
                        reminder["active"] = False  # No more occurrences
                else:
                    reminder["active"] = False  # Default to one-time

        self.save_reminders()
        self.refresh_tables()

    def compute_next_weekly_occurrence(self, last_time, interval, days):
        """Compute the next occurrence time for a weekly recurring reminder."""
        day_numbers = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        selected_days = [day_numbers[day] for day in days]
        if not selected_days:
            return None  # No days selected

        last_datetime = datetime.fromtimestamp(last_time)
        next_datetime = last_datetime + timedelta(days=1)
        weeks_added = 0

        while weeks_added < 52:  # Limit to prevent infinite loops
            day_of_week = next_datetime.weekday()
            if day_of_week in selected_days:
                weeks_since_start = ((next_datetime - last_datetime).days) // 7
                if weeks_since_start % interval == 0:
                    if next_datetime.timestamp() > last_time:
                        return int(next_datetime.timestamp())
            next_datetime += timedelta(days=1)
            if next_datetime.weekday() == 0:  # Monday
                weeks_added += 1
        return None

    def compute_next_monthly_occurrence(self, last_time, interval, months):
        """Compute the next occurrence time for a monthly recurring reminder."""
        month_numbers = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12,
        }
        selected_months = [month_numbers[month] for month in months]
        if not selected_months:
            return None  # No months selected

        last_datetime = datetime.fromtimestamp(last_time)
        next_datetime = last_datetime + timedelta(days=1)
        months_added = 0

        while months_added < 120:  # Limit to prevent infinite loops (10 years)
            month = next_datetime.month
            if month in selected_months:
                # Check if it's the correct interval
                months_since_start = (next_datetime.year - last_datetime.year) * 12 + (next_datetime.month - last_datetime.month)
                if months_since_start % interval == 0:
                    if next_datetime.timestamp() > last_time:
                        return int(next_datetime.timestamp())
            # Move to next day
            next_datetime += timedelta(days=1)
        return None

    def play_reminder(self, reminder):
        """Play the reminder's pre-audio and main audio."""
        pre_audio_file = reminder.get("pre_audio_file")
        audio_file = reminder.get("audio_file")
        loops = reminder.get("loops", 1)
        delay_between_loops = reminder.get("delay_between_loops", 0)

        if pre_audio_file:
            pre_audio_path = os.path.join(self.pre_audio_dir, pre_audio_file)
            self.play_audio(pre_audio_path, loops=1)
            # Wait for pre-audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)

        if loops > 1 and delay_between_loops > 0:
            for i in range(loops):
                self.play_audio(audio_file, loops=1)
                # Wait for audio to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                if i < loops - 1:
                    pygame.time.wait(int(delay_between_loops * 1000))
        else:
            self.play_audio(audio_file, loops=loops)

    def play_audio(self, audio_file, loops=1):
        """Plays an audio file.  Improved error handling."""
        if not audio_file:
            self.status_bar.showMessage("No audio file specified.", 5000)
            return

        if not os.path.exists(audio_file):
            self.status_bar.showMessage(f"Audio file not found: {audio_file}", 5000)
            return

        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play(loops=loops - 1)  # loops parameter in pygame is number of repeats
            self.audio_looping = loops > 1
            self.status_bar.showMessage(f"Playing audio: {os.path.basename(audio_file)}", 5000)
        except pygame.error as e:
            self.status_bar.showMessage(f"Error playing audio: {e}", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"An unexpected error occurred: {e}", 5000)

    def stop_audio(self):
        """Stop the currently playing audio."""
        pygame.mixer.music.stop()
        self.status_bar.showMessage("Audio playback stopped.", 5000)
        if self.currently_playing_button is not None:
            try:
                self.currently_playing_button.setIcon(QIcon.fromTheme('media-playback-start'))
            except RuntimeError:
                pass  # The button has been deleted
            self.currently_playing_reminder = None
            self.currently_playing_button = None

    def check_audio_finished(self):
        """Check if the audio has finished playing."""
        if not pygame.mixer.music.get_busy():
            # Music has stopped playing
            if not self.audio_looping:
                if self.currently_playing_button is not None:
                    try:
                        self.currently_playing_button.setIcon(QIcon.fromTheme('media-playback-start'))
                    except RuntimeError:
                        pass  # The button has been deleted
                    self.currently_playing_reminder = None
                    self.currently_playing_button = None

    def refresh_tables(self):
        """Refresh the active and inactive task tables."""
        self.active_table.setRowCount(0)
        self.inactive_table.setRowCount(0)

        for reminder in self.reminders:
            table = self.active_table if reminder["active"] else self.inactive_table
            self.add_reminder_to_table(table, reminder)

    def add_reminder_to_table(self, table, reminder):
        """Add a reminder to the specified table."""
        row_position = table.rowCount()
        table.insertRow(row_position)

        # Create play button with icon
        play_button = QPushButton()
        play_button.setIcon(QIcon.fromTheme('media-playback-start'))
        play_button.clicked.connect(lambda _, r=reminder, b=play_button: self.toggle_audio(r, b))
        play_button.setFixedSize(30, 30)

        # Create delete button with icon
        delete_button = QPushButton()
        delete_button.setIcon(QIcon.fromTheme('edit-delete'))
        delete_button.clicked.connect(lambda _, r=reminder: self.delete_reminder(r))
        delete_button.setFixedSize(30, 30)

        # Set table items
        table.setItem(row_position, 0, QTableWidgetItem(reminder["task_name"]))
        start_time_str = QDateTime.fromSecsSinceEpoch(int(reminder["start_time"])).toString("dd/MM/yyyy hh:mm:ss")
        table.setItem(row_position, 1, QTableWidgetItem(start_time_str))
        recurrence_str = self.format_recurrence(reminder["recurrence"])
        table.setItem(row_position, 2, QTableWidgetItem(recurrence_str))
        table.setCellWidget(row_position, 3, play_button)
        table.setCellWidget(row_position, 4, delete_button)

        # Center-align cells
        for col in range(5):
            item = table.item(row_position, col)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def format_recurrence(self, recurrence):
        """Format the recurrence information for display."""
        rec_type = recurrence.get("type", "one_time")
        if rec_type == "one_time":
            return "One time"
        elif rec_type == "daily":
            return "Daily"
        elif rec_type == "weekly":
            interval = recurrence.get("interval", 1)
            days = recurrence.get("days", [])
            days_str = ', '.join(days)
            return f"Weekly, every {interval} week(s) on {days_str}"
        elif rec_type == "monthly":
            interval = recurrence.get("interval", 1)
            months = recurrence.get("months", [])
            months_str = ', '.join(months)
            return f"Monthly, every {interval} month(s) on {months_str}"
        else:
            return "One time"

    def toggle_audio(self, reminder, button):
        """Toggle audio playback for a reminder."""
        if self.currently_playing_reminder == reminder:
            # Audio is playing, stop it
            self.stop_audio()
        else:
            # Stop any currently playing audio
            self.stop_audio()
            # Play the new audio (including pre-audio)
            self.play_reminder(reminder)
            self.currently_playing_reminder = reminder
            self.currently_playing_button = button
            button.setIcon(QIcon.fromTheme('media-playback-stop'))

    def delete_reminder(self, reminder):
        """Delete a reminder."""
        reply = QMessageBox.question(
            self,
            "Delete Reminder",
            "Are you sure you want to delete this reminder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.currently_playing_reminder == reminder:
                self.stop_audio()
            self.reminders.remove(reminder)
            self.save_reminders()
            self.refresh_tables()
            self.status_bar.showMessage("Reminder deleted successfully.", 5000)

    def show_reminder_popup(self, reminder):
        """Display popup for reminder."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Reminder Alert")
        msg_box.setText(f"Task: {reminder['task_name']}")

        stop_button = msg_box.addButton("Stop Audio", QMessageBox.ButtonRole.ActionRole)
        minimize_button = msg_box.addButton("Minimize        ", QMessageBox.ButtonRole.ActionRole)

        stop_button.clicked.connect(self.stop_audio)
        minimize_button.clicked.connect(self.minimize_app)

        msg_box.exec()

    def minimize_app(self):
        """Minimize application."""
        self.showMinimized()

    def load_reminders(self):
        """Load reminders from the JSON file."""
        if os.path.exists(self.reminders_file):
            with open(self.reminders_file, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_reminders(self):
        """Save reminders to the JSON file."""
        with open(self.reminders_file, "w") as f:
            json.dump(self.reminders, f, indent=4)

    def edit_reminder(self, row, col):
        """Opens the edit dialog when a reminder row is double-clicked."""
        table = self.sender()
        row_index = table.rowAt(row)  # Get the index of the clicked row
        if 0 <= row_index < len(self.reminders): #Check if a valid row is clicked
            reminder = self.reminders[row_index]
            self.show_edit_dialog(reminder, table)
        else:
            QMessageBox.warning(self, "Error", "Invalid row selected for editing.")

    def show_edit_dialog(self, reminder, table):
        """Shows the edit reminder dialog."""
        dialog = EditReminderDialog(self, reminder)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_reminder = dialog.get_values()
            index = self.reminders.index(reminder)
            self.reminders[index] = updated_reminder
            self.save_reminders()
            self.refresh_tables()



class EditReminderDialog(QDialog):
    def __init__(self, parent, reminder):
        super().__init__(parent)
        self.setWindowTitle("Edit Reminder")
        self.setModal(True)
        self.reminder = reminder
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Task Name
        task_name_layout = QHBoxLayout()
        task_name_layout.addWidget(QLabel("Task Name:"))
        self.task_name_edit = QLineEdit(self.reminder["task_name"])
        task_name_layout.addWidget(self.task_name_edit)
        layout.addLayout(task_name_layout)

        # Start DateTime
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.start_datetime = QDateTimeEdit(QDateTime.fromSecsSinceEpoch(int(self.reminder["start_time"])))
        self.start_datetime.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.start_datetime.setCalendarPopup(True)
        start_layout.addWidget(self.start_datetime)
        layout.addLayout(start_layout)

        # Recurrence Type
        recurrence_layout = QHBoxLayout()
        self.recurrence_group = QButtonGroup(self)
        self.one_time_radio = QRadioButton("One time")
        self.daily_radio = QRadioButton("Daily")
        self.weekly_radio = QRadioButton("Weekly")
        self.monthly_radio = QRadioButton("Monthly")
        self.recurrence_group.addButton(self.one_time_radio)
        self.recurrence_group.addButton(self.daily_radio)
        self.recurrence_group.addButton(self.weekly_radio)
        self.recurrence_group.addButton(self.monthly_radio)
        recurrence_layout.addWidget(self.one_time_radio)
        recurrence_layout.addWidget(self.daily_radio)
        recurrence_layout.addWidget(self.weekly_radio)
        recurrence_layout.addWidget(self.monthly_radio)
        layout.addLayout(recurrence_layout)

        # Audio File Upload and Loops
        audio_layout = QVBoxLayout()

        # Loops and Delay
        loops_delay_layout = QHBoxLayout()
        loops_label = QLabel("Loops:")
        self.loops_spinbox = QSpinBox()
        self.loops_spinbox.setRange(1, 1000)
        self.loops_spinbox.setValue(self.reminder["loops"])
        loops_delay_layout.addWidget(loops_label)
        loops_delay_layout.addWidget(self.loops_spinbox)

        delay_label = QLabel("Delay between loops (s):")
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 3600)
        self.delay_spinbox.setValue(self.reminder["delay_between_loops"])
        loops_delay_layout.addWidget(delay_label)
        loops_delay_layout.addWidget(self.delay_spinbox)
        audio_layout.addLayout(loops_delay_layout)

        # Pre-Audio Selection and Preview
        pre_audio_layout = QHBoxLayout()
        self.pre_audio_combo = QComboBox()
        self.pre_audio_combo.setPlaceholderText("Select Pre-Audio")
        self.load_pre_audio_files()
        self.pre_audio_combo.setCurrentText(self.reminder.get("pre_audio_file", "None"))
        pre_audio_layout.addWidget(self.pre_audio_combo)
        self.preview_pre_audio_button = QPushButton("Preview")
        self.preview_pre_audio_button.clicked.connect(self.preview_pre_audio)
        pre_audio_layout.addWidget(self.preview_pre_audio_button)
        audio_layout.addLayout(pre_audio_layout)

        # Main Audio Upload
        main_audio_layout = QHBoxLayout()
        self.audio_path_edit = QLineEdit(self.reminder["audio_file"])
        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.upload_audio)
        self.preview_audio_button = QPushButton("Preview")
        self.preview_audio_button.clicked.connect(self.preview_audio)
        main_audio_layout.addWidget(self.audio_path_edit)
        main_audio_layout.addWidget(self.upload_button)
        main_audio_layout.addWidget(self.preview_audio_button)
        audio_layout.addLayout(main_audio_layout)
        layout.addLayout(audio_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.recurrence_group.buttonClicked.connect(self.handle_recurrence_selection)

        # Set initial recurrence selection
        recurrence_type = self.reminder["recurrence"].get("type", "one_time")
        if recurrence_type == "one_time":
            self.one_time_radio.setChecked(True)
        elif recurrence_type == "daily":
            self.daily_radio.setChecked(True)
        elif recurrence_type == "weekly":
            self.weekly_radio.setChecked(True)
            self.weekly_interval, self.weekly_days = self.reminder["recurrence"].get("interval",1), self.reminder["recurrence"].get("days",[])

        elif recurrence_type == "monthly":
            self.monthly_radio.setChecked(True)
            self.monthly_interval, self.monthly_months = self.reminder["recurrence"].get("interval",1), self.reminder["recurrence"].get("months",[])

    def load_pre_audio_files(self):
        self.pre_audio_combo.clear()
        self.pre_audio_combo.addItem("None")
        audio_files = [f for f in os.listdir("preaudio") if f.lower().endswith(('.mp3', '.wav'))]
        self.pre_audio_combo.addItems(audio_files)

    def preview_pre_audio(self):
        selected_file = self.pre_audio_combo.currentText()
        if selected_file and selected_file != "None":
            pre_audio_path = os.path.join("preaudio", selected_file)
            try:
                pygame.mixer.music.load(pre_audio_path)
                pygame.mixer.music.play()
            except pygame.error as e:
                QMessageBox.warning(self, "Error", f"Error playing pre-audio: {e}")
        else:
            QMessageBox.warning(self, "Error", "No pre-audio file selected.")

    def preview_audio(self):
        audio_file = self.audio_path_edit.text()
        if audio_file and os.path.exists(audio_file):
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
            except pygame.error as e:
                QMessageBox.warning(self, "Error", f"Error playing audio: {e}")
        else:
            QMessageBox.warning(self, "Error", "Invalid audio file selected.")

    def upload_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Main Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.audio_path_edit.setText(file_path)

    def handle_recurrence_selection(self, button):
        if button == self.weekly_radio:
            dialog = WeeklyRecurrenceDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.weekly_interval, self.weekly_days = dialog.get_values()
            else:
                self.one_time_radio.setChecked(True)
        elif button == self.monthly_radio:
            dialog = MonthlyRecurrenceDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.monthly_interval, self.monthly_months = dialog.get_values()
            else:
                self.one_time_radio.setChecked(True)

    def get_values(self):
        task_name = self.task_name_edit.text()
        start_time = self.start_datetime.dateTime().toSecsSinceEpoch()
        audio_file = self.audio_path_edit.text()
        pre_audio_file = self.pre_audio_combo.currentText()
        loops = self.loops_spinbox.value()
        delay_between_loops = self.delay_spinbox.value()

        recurrence = None
        if self.one_time_radio.isChecked():
            recurrence = {"type": "one_time"}
        elif self.daily_radio.isChecked():
            recurrence = {"type": "daily"}
        elif self.weekly_radio.isChecked():
            recurrence = {"type": "weekly", "interval": self.weekly_interval, "days": self.weekly_days}
        elif self.monthly_radio.isChecked():
            recurrence = {"type": "monthly", "interval": self.monthly_interval, "months": self.monthly_months}

        return {
            "task_name": task_name,
            "start_time": start_time,
            "audio_file": audio_file,
            "pre_audio_file": pre_audio_file if pre_audio_file != "None" else None,
            "loops": loops,
            "delay_between_loops": delay_between_loops,
            "recurrence": recurrence,
            "active": self.reminder["active"]
        }



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskScheduler()
    window.show()
    sys.exit(app.exec())
