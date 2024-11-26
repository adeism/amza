import sys
import os
import json
from functools import partial
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QDateTimeEdit, QSpinBox, QRadioButton, QButtonGroup, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QStatusBar, QMessageBox, QCheckBox, QGridLayout, QHeaderView
)
from PyQt6.QtCore import QDateTime, QTimer, Qt
from PyQt6.QtGui import QIcon
import pygame


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
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Task Form
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

        # Weekly Recurrence Settings
        self.weekly_settings_layout = QGridLayout()
        self.weekly_settings_layout.addWidget(QLabel("Recur every:"), 0, 0)

        self.weekly_interval_spinbox = QSpinBox()
        self.weekly_interval_spinbox.setRange(1, 52)
        self.weekly_interval_spinbox.setValue(1)
        self.weekly_settings_layout.addWidget(self.weekly_interval_spinbox, 0, 1)

        self.weekly_settings_layout.addWidget(QLabel("weeks on:"), 0, 2)

        self.days_checkboxes = {
            "Monday": QCheckBox("Monday"),
            "Tuesday": QCheckBox("Tuesday"),
            "Wednesday": QCheckBox("Wednesday"),
            "Thursday": QCheckBox("Thursday"),
            "Friday": QCheckBox("Friday"),
            "Saturday": QCheckBox("Saturday"),
            "Sunday": QCheckBox("Sunday"),
        }

        for idx, day in enumerate(self.days_checkboxes.values()):
            self.weekly_settings_layout.addWidget(day, 1 + idx // 4, idx % 4)

        form_layout.addLayout(self.weekly_settings_layout)

        # Disable weekly settings by default
        self.toggle_weekly_settings(False)

        # Audio File Upload
        audio_layout = QHBoxLayout()
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setPlaceholderText("No file selected")
        audio_layout.addWidget(QLabel("Audio File:"))
        audio_layout.addWidget(self.audio_path_edit)
        self.upload_button = QPushButton("Upload Audio")
        self.upload_button.clicked.connect(self.upload_audio)
        audio_layout.addWidget(self.upload_button)
        form_layout.addLayout(audio_layout)

        # Add Reminder Button
        self.add_button = QPushButton("Add Reminder")
        self.add_button.clicked.connect(self.add_reminder)
        form_layout.addWidget(self.add_button)

        main_layout.addLayout(form_layout)

        # Active Task Table
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(5)
        self.active_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "", ""])
        self.setup_table(self.active_table)
        main_layout.addWidget(self.active_table)

        # Inactive Task Table
        self.inactive_button = QPushButton("Show Inactive Tasks")
        self.inactive_button.clicked.connect(self.toggle_inactive_tasks)
        self.inactive_table = QTableWidget()
        self.inactive_table.setColumnCount(5)
        self.inactive_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "", ""])
        self.setup_table(self.inactive_table)
        self.inactive_table.setVisible(False)
        main_layout.addWidget(self.inactive_button)
        main_layout.addWidget(self.inactive_table)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Connect radio buttons to toggle recurrence options
        self.recurrence_group.buttonClicked.connect(self.update_recurrence_options)

        # Refresh table on startup
        self.refresh_tables()

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

    def update_recurrence_options(self):
        """Update recurrence options visibility based on selected type."""
        if self.weekly_radio.isChecked():
            self.toggle_weekly_settings(True)
        else:
            self.toggle_weekly_settings(False)

    def toggle_weekly_settings(self, enabled):
        """Enable or disable weekly recurrence settings."""
        self.weekly_interval_spinbox.setEnabled(enabled)
        for checkbox in self.days_checkboxes.values():
            checkbox.setEnabled(enabled)

    def upload_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.audio_path_edit.setText(file_path)

    def add_reminder(self):
        task_name = self.task_name_edit.text()
        start_time = self.start_datetime.dateTime().toSecsSinceEpoch()
        audio_file = self.audio_path_edit.text()

        if not task_name or not audio_file:
            self.status_bar.showMessage("Task name and audio file are required!", 5000)
            return

        if self.one_time_radio.isChecked():
            recurrence = {"type": "one_time"}
        elif self.daily_radio.isChecked():
            recurrence = {"type": "daily"}
        elif self.weekly_radio.isChecked():
            recurrence = {
                "type": "weekly",
                "interval": self.weekly_interval_spinbox.value(),
                "days": [day for day, checkbox in self.days_checkboxes.items() if checkbox.isChecked()],
            }
        elif self.monthly_radio.isChecked():
            recurrence = {"type": "monthly"}
        else:
            recurrence = {"type": "one_time"}  # Default

        reminder = {
            "task_name": task_name,
            "start_time": start_time,
            "recurrence": recurrence,
            "audio_file": audio_file,
            "active": True,
        }
        self.reminders.append(reminder)
        self.save_reminders()
        self.refresh_tables()
        self.clear_inputs()

    def toggle_inactive_tasks(self):
        is_visible = self.inactive_table.isVisible()
        self.inactive_table.setVisible(not is_visible)
        self.inactive_button.setText("Hide Inactive Tasks" if not is_visible else "Show Inactive Tasks")

    def clear_inputs(self):
        self.task_name_edit.clear()
        self.start_datetime.setDateTime(QDateTime.currentDateTime())
        self.weekly_interval_spinbox.setValue(1)
        for checkbox in self.days_checkboxes.values():
            checkbox.setChecked(False)
        self.audio_path_edit.clear()
        self.one_time_radio.setChecked(True)

    def check_reminders(self):
        current_time = QDateTime.currentDateTime().toSecsSinceEpoch()
        for reminder in self.reminders:
            if reminder["active"] and reminder["start_time"] <= current_time:
                self.play_audio(reminder["audio_file"], loop=True)
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
                    # Add 1 month to start_time
                    reminder["start_time"] = self.add_months(reminder["start_time"], 1)
                else:
                    reminder["active"] = False  # Default to one-time

        self.save_reminders()
        self.refresh_tables()

    def compute_next_weekly_occurrence(self, last_time, interval, days):
        """Compute the next occurrence time for a weekly recurring reminder."""
        day_numbers = {
            "Monday": 1,
            "Tuesday": 2,
            "Wednesday": 3,
            "Thursday": 4,
            "Friday": 5,
            "Saturday": 6,
            "Sunday": 7,
        }
        day_indices = [day_numbers[day] for day in days]
        if not day_indices:
            return None  # No days selected

        next_datetime = QDateTime.fromSecsSinceEpoch(last_time).addDays(1)
        weeks_added = 0

        while weeks_added < 52:  # Limit to prevent infinite loops
            day_of_week = next_datetime.date().dayOfWeek()
            if day_of_week in day_indices:
                weeks_since_start = (next_datetime.date().toJulianDay() - QDateTime.fromSecsSinceEpoch(last_time).date().toJulianDay()) // 7
                if weeks_since_start % interval == 0:
                    if next_datetime.toSecsSinceEpoch() > last_time:
                        return next_datetime.toSecsSinceEpoch()
            next_datetime = next_datetime.addDays(1)
            if next_datetime.date().dayOfWeek() == 1:  # Monday
                weeks_added += 1
        return None

    def add_months(self, start_time, months):
        """Add months to a timestamp."""
        start_datetime = QDateTime.fromSecsSinceEpoch(start_time)
        month = start_datetime.date().month() + months
        year = start_datetime.date().year() + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(start_datetime.date().day(), QDateTime(year, month, 1, 0, 0).date().daysInMonth())
        new_date = QDateTime(year, month, day, start_datetime.time().hour(), start_datetime.time().minute(), start_datetime.time().second())
        return new_date.toSecsSinceEpoch()

    def play_audio(self, audio_file, loop=False):
        """Play the reminder's audio file."""
        if not os.path.exists(audio_file):
            self.status_bar.showMessage(f"Audio file not found: {audio_file}", 5000)
            return
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play(-1 if loop else 0)  # Loop indefinitely or play once
            self.audio_looping = loop
            self.status_bar.showMessage(f"Playing reminder audio: {audio_file}", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Error playing audio: {e}", 5000)

    def stop_audio(self):
        """Stop the currently playing audio."""
        pygame.mixer.music.stop()
        self.status_bar.showMessage("Audio playback stopped.", 5000)
        if self.currently_playing_button is not None:
            try:
                self.currently_playing_button.setIcon(QIcon('play_icon.png'))
            except RuntimeError:
                # The button has been deleted
                pass
            self.currently_playing_reminder = None
            self.currently_playing_button = None

    def check_audio_finished(self):
        """Check if the audio has finished playing."""
        if not pygame.mixer.music.get_busy():
            # Music has stopped playing
            if not self.audio_looping:
                if self.currently_playing_button is not None:
                    try:
                        self.currently_playing_button.setIcon(QIcon('play_icon.png'))
                    except RuntimeError:
                        # The button has been deleted
                        pass
                    self.currently_playing_reminder = None
                    self.currently_playing_button = None

    def refresh_tables(self):
        self.active_table.setRowCount(0)
        self.inactive_table.setRowCount(0)

        for reminder in self.reminders:
            table = self.active_table if reminder["active"] else self.inactive_table
            row_position = table.rowCount()
            table.insertRow(row_position)

            # Create play button with icon
            play_button = QPushButton()
            play_button.setIcon(QIcon.fromTheme('media-playback-start'))
            play_button.clicked.connect(partial(self.toggle_audio, reminder, play_button))
            play_button.setFixedSize(30, 30)

            # Create delete button with icon
            delete_button = QPushButton()
            delete_button.setIcon(QIcon.fromTheme('edit-delete'))
            delete_button.clicked.connect(partial(self.delete_reminder, reminder))
            delete_button.setFixedSize(30, 30)

            table.setItem(row_position, 0, QTableWidgetItem(reminder["task_name"]))
            table.setItem(row_position, 1, QTableWidgetItem(QDateTime.fromSecsSinceEpoch(reminder["start_time"]).toString("dd/MM/yyyy hh:mm:ss")))
            recurrence_str = self.format_recurrence(reminder["recurrence"])
            table.setItem(row_position, 2, QTableWidgetItem(recurrence_str))
            table.setCellWidget(row_position, 3, play_button)
            table.setCellWidget(row_position, 4, delete_button)

            # Center-align cells
            for col in range(5):
                item = table.item(row_position, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Remove headers for play and delete columns
        for table in [self.active_table, self.inactive_table]:
            table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "", ""])

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
            return "Monthly"
        else:
            return "One time"

    def toggle_audio(self, reminder, button):
        if self.currently_playing_reminder == reminder:
            # Audio is playing, stop it
            self.stop_audio()
        else:
            # Stop any currently playing audio
            self.stop_audio()
            # Play the new audio
            self.play_audio(reminder['audio_file'], loop=False)
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

    def show_reminder_popup(self, reminder):
        """Display popup for reminder."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Reminder Alert")
        msg_box.setText(f"Task: {reminder['task_name']}")

        stop_button = msg_box.addButton("Stop Audio", QMessageBox.ButtonRole.ActionRole)
        minimize_button = msg_box.addButton("Minimize", QMessageBox.ButtonRole.ActionRole)

        stop_button.clicked.connect(self.stop_audio)
        minimize_button.clicked.connect(self.minimize_app)

        msg_box.exec()

    def minimize_app(self):
        """Minimize application."""
        self.showMinimized()

    def load_reminders(self):
        if os.path.exists(self.reminders_file):
            with open(self.reminders_file, "r") as f:
                return json.load(f)
        return []

    def save_reminders(self):
        with open(self.reminders_file, "w") as f:
            json.dump(self.reminders, f, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskScheduler()
    window.show()
    sys.exit(app.exec())
