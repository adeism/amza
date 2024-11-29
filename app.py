import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QDateTimeEdit, QSpinBox, QRadioButton, QButtonGroup, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QStatusBar, QMessageBox, QCheckBox,
    QHeaderView, QDialog, QComboBox, QDialogButtonBox, QGridLayout
)
from PyQt6.QtCore import QDateTime, QTimer, Qt
from PyQt6.QtGui import QIcon
import pygame
from datetime import datetime, timedelta


class RecurrenceDialog(QDialog):
    def __init__(self, parent=None, title="Recurrence Settings", interval_range=(1, 1), interval_label="interval(s)", items={}):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.interval_range = interval_range
        self.interval_label = interval_label
        self.items = items
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        recur_layout = QHBoxLayout()
        recur_layout.addWidget(QLabel(f"Recur every:"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(*self.interval_range)
        self.interval_spinbox.setValue(1)
        recur_layout.addWidget(self.interval_spinbox)
        recur_layout.addWidget(QLabel(self.interval_label))
        layout.addLayout(recur_layout)

        items_layout = QGridLayout()
        row, col = 0, 0
        for item_name, checkbox in self.items.items():
            items_layout.addWidget(checkbox, row, col)
            col += 1
            if col == 4:  # 4 columns per row
                row += 1
                col = 0
        layout.addLayout(items_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self):
        interval = self.interval_spinbox.value()
        selected_items = [item_name for item_name, checkbox in self.items.items() if checkbox.isChecked()]
        return interval, selected_items


def create_weekly_dialog(parent):
    days = {day: QCheckBox(day) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    return RecurrenceDialog(parent, "Weekly Recurrence", (1, 52), "week(s)", days)


def create_monthly_dialog(parent):
    months = {month: QCheckBox(month) for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
    return RecurrenceDialog(parent, "Monthly Recurrence", (1, 12), "month(s)", months)


class TaskScheduler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMZ Announcement")
        self.setGeometry(100, 100, 800, 600)
        pygame.mixer.init()
        self.reminders_file = "reminders.json"
        self.reminders = self.load_reminders()
        self.pre_audio_dir = "preaudio"
        os.makedirs(self.pre_audio_dir, exist_ok=True)
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(1000)
        self.audio_check_timer = QTimer()
        self.audio_check_timer.timeout.connect(self.check_audio_finished)
        self.audio_check_timer.start(500)
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None
        self.currently_playing_reminder = None
        self.currently_playing_button = None
        self.audio_looping = False

    def closeEvent(self, event):
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
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

    def create_task_form(self):
        form_layout = QVBoxLayout()

        task_name_layout = QHBoxLayout()
        task_name_layout.addWidget(QLabel("Task Name:"))
        self.task_name_edit = QLineEdit()
        task_name_layout.addWidget(self.task_name_edit)
        form_layout.addLayout(task_name_layout)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.start_datetime = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_datetime.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.start_datetime.setCalendarPopup(True)
        start_layout.addWidget(self.start_datetime)
        form_layout.addLayout(start_layout)

        recurrence_layout = QHBoxLayout()
        self.recurrence_group = QButtonGroup(self)

        self.one_time_radio = QRadioButton("One time")
        self.one_time_radio.setChecked(True)
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

        audio_layout = QVBoxLayout()

        loops_delay_layout = QHBoxLayout()

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

        main_audio_layout = QHBoxLayout()
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setPlaceholderText("No audio selected")
        main_audio_layout.addWidget(self.audio_path_edit)

        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.upload_audio)
        main_audio_layout.addWidget(self.upload_button)

        self.preview_audio_button = QPushButton("Preview")
        self.preview_audio_button.clicked.connect(self.preview_audio)
        main_audio_layout.addWidget(self.preview_audio_button)

        audio_layout.addLayout(main_audio_layout)

        form_layout.addLayout(audio_layout)

        self.add_button = QPushButton("Add Reminder")
        self.add_button.clicked.connect(self.add_reminder)
        form_layout.addWidget(self.add_button)

        self.main_layout.addLayout(form_layout)

        self.recurrence_group.buttonClicked.connect(self.handle_recurrence_selection)

    def create_task_tables(self):
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(5)
        self.active_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "Play", "Edit"])
        self.setup_table(self.active_table)
        self.main_layout.addWidget(self.active_table)

        self.inactive_button = QPushButton("Show Inactive Tasks")
        self.inactive_button.clicked.connect(self.toggle_inactive_tasks)
        self.inactive_table = QTableWidget()
        self.inactive_table.setColumnCount(5)
        self.inactive_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "Play", "Edit"])
        self.setup_table(self.inactive_table)
        self.inactive_table.setVisible(False)
        self.main_layout.addWidget(self.inactive_button)
        self.main_layout.addWidget(self.inactive_table)

        self.active_table.cellClicked.connect(self.handle_table_click)
        self.inactive_table.cellClicked.connect(self.handle_table_click)

        self.refresh_tables()

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def setup_table(self, table):
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        table.setColumnWidth(3, 40)
        table.setColumnWidth(4, 40)

        for i in range(table.columnCount()):
            item = table.horizontalHeaderItem(i)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def handle_recurrence_selection(self, button):
        if button == self.weekly_radio:
            dialog = WeeklyRecurrenceDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.weekly_interval, self.weekly_days = dialog.get_values()
            else:
                self.one_time_radio.setChecked(True)
                self.weekly_interval = None
                self.weekly_days = None
        elif button == self.monthly_radio:
            dialog = MonthlyRecurrenceDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.monthly_interval, self.monthly_months = dialog.get_values()
            else:
                self.one_time_radio.setChecked(True)
                self.monthly_interval = None
                self.monthly_months = None
        else:
            self.weekly_interval = None
            self.weekly_days = None
            self.monthly_interval = None
            self.monthly_months = None

    def load_pre_audio_files(self):
        self.pre_audio_combo.clear()
        self.pre_audio_combo.addItem("None")
        audio_files = [f for f in os.listdir(self.pre_audio_dir) if f.lower().endswith(('.mp3', '.wav'))]
        if audio_files:
            self.pre_audio_combo.addItems(audio_files)

    def preview_pre_audio(self):
        selected_file = self.pre_audio_combo.currentText()
        if selected_file and selected_file != "None":
            pre_audio_path = os.path.join(self.pre_audio_dir, selected_file)
            self.play_audio(pre_audio_path, loops=1)
        else:
            self.status_bar.showMessage("No pre-audio file selected.", 5000)

    def upload_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Main Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.audio_path_edit.setText(file_path)

    def add_reminder(self):
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
            recurrence = {"type": "one_time"}

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
        audio_file = self.audio_path_edit.text()
        if audio_file:
            self.play_audio(audio_file, loops=1)
        else:
            self.status_bar.showMessage("No audio file selected.", 5000)

    def toggle_inactive_tasks(self):
        is_visible = self.inactive_table.isVisible()
        self.inactive_table.setVisible(not is_visible)
        self.inactive_button.setText("Hide Inactive Tasks" if not is_visible else "Show Inactive Tasks")

    def clear_inputs(self):
        self.task_name_edit.clear()
        self.start_datetime.setDateTime(QDateTime.currentDateTime())
        self.loops_spinbox.setValue(1)
        self.delay_spinbox.setValue(0)
        self.one_time_radio.setChecked(True)
        self.load_pre_audio_files()
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None
        self.audio_path_edit.clear()
        self.pre_audio_combo.setCurrentIndex(0)

    def check_reminders(self):
        current_time = datetime.now().timestamp()
        for reminder in self.reminders:
            if reminder["active"] and reminder["start_time"] <= current_time:
                self.play_reminder(reminder)
                self.show_reminder_popup(reminder)

                recurrence = reminder.get("recurrence", {"type": "one_time"})
                rec_type = recurrence.get("type", "one_time")

                if rec_type == "one_time":
                    reminder["active"] = False
                elif rec_type == "daily":
                    reminder["start_time"] += 86400
                elif rec_type == "weekly":
                    interval = recurrence.get("interval", 1)
                    days = recurrence.get("days", [])
                    next_time = self.compute_next_weekly_occurrence(reminder["start_time"], interval, days)
                    if next_time:
                        reminder["start_time"] = next_time
                    else:
                        reminder["active"] = False
                elif rec_type == "monthly":
                    interval = recurrence.get("interval", 1)
                    months = recurrence.get("months", [])
                    next_time = self.compute_next_monthly_occurrence(reminder["start_time"], interval, months)
                    if next_time:
                        reminder["start_time"] = next_time
                    else:
                        reminder["active"] = False
                else:
                    reminder["active"] = False

        self.save_reminders()
        self.refresh_tables()

    def compute_next_weekly_occurrence(self, last_time, interval, days):
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
            return None

        last_datetime = datetime.fromtimestamp(last_time)
        next_datetime = last_datetime + timedelta(days=1)
        weeks_added = 0

        while weeks_added < 52:
            day_of_week = next_datetime.weekday()
            if day_of_week in selected_days:
                weeks_since_start = ((next_datetime - last_datetime).days) // 7
                if weeks_since_start % interval == 0:
                    if next_datetime.timestamp() > last_time:
                        return int(next_datetime.timestamp())
            next_datetime += timedelta(days=1)
            if next_datetime.weekday() == 0:
                weeks_added += 1
        return None

    def compute_next_monthly_occurrence(self, last_time, interval, months):
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
            return None

        last_datetime = datetime.fromtimestamp(last_time)
        next_datetime = last_datetime + timedelta(days=1)
        months_added = 0

        while months_added < 120:
            month = next_datetime.month
            if month in selected_months:
                months_since_start = (next_datetime.year - last_datetime.year) * 12 + (next_datetime.month - last_datetime.month)
                if months_since_start % interval == 0:
                    if next_datetime.timestamp() > last_time:
                        return int(next_datetime.timestamp())
            next_datetime += timedelta(days=1)
        return None

    def play_reminder(self, reminder):
        pre_audio_file = reminder.get("pre_audio_file")
        audio_file = reminder.get("audio_file")
        loops = reminder.get("loops", 1)
        delay_between_loops = reminder.get("delay_between_loops", 0)

        if pre_audio_file:
            pre_audio_path = os.path.join(self.pre_audio_dir, pre_audio_file)
            self.play_audio(pre_audio_path, loops=1)
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)

        if loops > 1 and delay_between_loops > 0:
            for i in range(loops):
                self.play_audio(audio_file, loops=1)
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                if i < loops - 1:
                    pygame.time.wait(int(delay_between_loops * 1000))
        else:
            self.play_audio(audio_file, loops=loops)

    def play_audio(self, audio_file, loops=1):
        if not audio_file:
            self.status_bar.showMessage("No audio file specified.", 5000)
            return

        if not os.path.exists(audio_file):
            self.status_bar.showMessage(f"Audio file not found: {audio_file}", 5000)
            return

        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play(loops=loops - 1)
            self.audio_looping = loops > 1
            self.status_bar.showMessage(f"Playing audio: {os.path.basename(audio_file)}", 5000)
        except pygame.error as e:
            self.status_bar.showMessage(f"Error playing audio: {e}", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"An unexpected error occurred: {e}", 5000)

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.status_bar.showMessage("Audio playback stopped.", 5000)
        if self.currently_playing_button is not None:
            try:
                self.currently_playing_button.setIcon(QIcon.fromTheme('media-playback-start'))
            except RuntimeError:
                pass
            self.currently_playing_reminder = None
            self.currently_playing_button = None

    def check_audio_finished(self):
        if not pygame.mixer.music.get_busy():
            if not self.audio_looping:
                if self.currently_playing_button is not None:
                    try:
                        self.currently_playing_button.setIcon(QIcon.fromTheme('media-playback-start'))
                    except RuntimeError:
                        pass
                    self.currently_playing_reminder = None
                    self.currently_playing_button = None

    def refresh_tables(self):
        self.active_table.setRowCount(0)
        self.inactive_table.setRowCount(0)
        for i, reminder in enumerate(self.reminders):
            table = self.active_table if reminder["active"] else self.inactive_table
            self.add_reminder_to_table(table, reminder, i)

    def add_reminder_to_table(self, table, reminder, row_index):
        row_position = table.rowCount()
        table.insertRow(row_position)

        play_button = QPushButton()
        play_button.setIcon(QIcon.fromTheme('media-playback-start'))
        play_button.clicked.connect(lambda _, r=reminder, b=play_button: self.toggle_audio(r, b))
        play_button.setFixedSize(30, 30)

        edit_button = QPushButton()
        edit_button.setIcon(QIcon.fromTheme('document-open'))
        edit_button.clicked.connect(lambda _, ri=row_index: self.show_edit_dialog(ri))
        edit_button.setFixedSize(30, 30)

        table.setItem(row_position, 0, QTableWidgetItem(reminder["task_name"]))
        start_time_str = QDateTime.fromSecsSinceEpoch(int(reminder["start_time"])).toString("dd/MM/yyyy hh:mm:ss")
        table.setItem(row_position, 1, QTableWidgetItem(start_time_str))
        recurrence_str = self.format_recurrence(reminder["recurrence"])
        table.setItem(row_position, 2, QTableWidgetItem(recurrence_str))
        table.setCellWidget(row_position, 3, play_button)
        table.setCellWidget(row_position, 4, edit_button)

        for col in range(5):
            item = table.item(row_position, col)
            if item:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)


    def format_recurrence(self, recurrence):
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
        if self.currently_playing_reminder == reminder:
            self.stop_audio()
        else:
            self.stop_audio()
            self.play_reminder(reminder)
            self.currently_playing_reminder = reminder
            self.currently_playing_button = button
            button.setIcon(QIcon.fromTheme('media-playback-stop'))

    def delete_reminder(self, reminder):
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
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Reminder Alert")
        msg_box.setText(f"Task: {reminder['task_name']}")

        stop_button = msg_box.addButton("Stop Audio", QMessageBox.ButtonRole.ActionRole)
        minimize_button = msg_box.addButton("Minimize", QMessageBox.ButtonRole.ActionRole)

        stop_button.clicked.connect(self.stop_audio)
        minimize_button.clicked.connect(self.minimize_app)

        msg_box.exec()

    def minimize_app(self):
        self.showMinimized()

    def load_reminders(self):
        if os.path.exists(self.reminders_file):
            with open(self.reminders_file, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_reminders(self):
        with open(self.reminders_file, "w") as f:
            json.dump(self.reminders, f, indent=4)

    def handle_table_click(self, row, col):
        table = self.sender()
        if col == 4:  # Clicked on "Edit" button
            row_index = table.row()
            self.show_edit_dialog(row_index)

    def show_edit_dialog(self, row_index):
        if 0 <= row_index < len(self.reminders):
            reminder = self.reminders[row_index]
            dialog = EditReminderDialog(self, reminder, row_index)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_reminder = dialog.get_values()
                self.reminders[row_index] = updated_reminder
                self.save_reminders()
                self.refresh_tables()
            elif dialog.result() == QDialog.DialogCode.Rejected:
                pass



class EditReminderDialog(QDialog):
    def __init__(self, parent, reminder, row_index):
        super().__init__(parent)
        self.setWindowTitle("Edit Reminder")
        self.setModal(True)
        self.reminder = reminder
        self.row_index = row_index
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        task_name_layout = QHBoxLayout()
        task_name_layout.addWidget(QLabel("Task Name:"))
        self.task_name_edit = QLineEdit(self.reminder["task_name"])
        task_name_layout.addWidget(self.task_name_edit)
        layout.addLayout(task_name_layout)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.start_datetime = QDateTimeEdit(QDateTime.fromSecsSinceEpoch(int(self.reminder["start_time"])))
        self.start_datetime.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.start_datetime.setCalendarPopup(True)
        start_layout.addWidget(self.start_datetime)
        layout.addLayout(start_layout)

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


        # WEEKLY RECURRENCE CHECKBOXES
        self.weekly_checkboxes = {
            "Monday": QCheckBox("Monday"),
            "Tuesday": QCheckBox("Tuesday"),
            "Wednesday": QCheckBox("Wednesday"),
            "Thursday": QCheckBox("Thursday"),
            "Friday": QCheckBox("Friday"),
            "Saturday": QCheckBox("Saturday"),
            "Sunday": QCheckBox("Sunday"),
        }
        weekly_layout = QVBoxLayout()
        weekly_interval_layout = QHBoxLayout()
        weekly_interval_layout.addWidget(QLabel("Recur every:"))
        self.weekly_interval_spinbox = QSpinBox()
        self.weekly_interval_spinbox.setRange(1, 52)
        weekly_interval_layout.addWidget(self.weekly_interval_spinbox)
        weekly_interval_layout.addWidget(QLabel("week(s)"))
        weekly_layout.addLayout(weekly_interval_layout)
        days_layout = QHBoxLayout()
        for day, cb in self.weekly_checkboxes.items():
            days_layout.addWidget(cb)
        weekly_layout.addLayout(days_layout)
        self.weekly_layout_widget = QWidget()
        self.weekly_layout_widget.setLayout(weekly_layout)
        self.weekly_layout_widget.setVisible(False)
        layout.addWidget(self.weekly_layout_widget)

        # MONTHLY RECURRENCE CHECKBOXES (Concise version)
        months_layout = QHBoxLayout()
        self.monthly_checkboxes = {month: QCheckBox(month) for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
        for month in self.monthly_checkboxes.values():
            months_layout.addWidget(month)
        monthly_layout = QVBoxLayout()
        monthly_interval_layout = QHBoxLayout()
        monthly_interval_layout.addWidget(QLabel("Recur every:"))
        self.monthly_interval_spinbox = QSpinBox()
        self.monthly_interval_spinbox.setRange(1, 12)
        monthly_interval_layout.addWidget(self.monthly_interval_spinbox)
        monthly_interval_layout.addWidget(QLabel("month(s)"))
        monthly_layout.addLayout(monthly_interval_layout)
        monthly_layout.addLayout(months_layout)
        self.monthly_layout_widget = QWidget()
        self.monthly_layout_widget.setLayout(monthly_layout)
        self.monthly_layout_widget.setVisible(False)
        layout.addWidget(self.monthly_layout_widget)


        audio_layout = QVBoxLayout()

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

        active_checkbox_layout = QHBoxLayout()
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(self.reminder["active"])
        active_checkbox_layout.addWidget(self.active_checkbox)
        layout.addLayout(active_checkbox_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_reminder)
        buttons.addButton(delete_button, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.recurrence_group.buttonClicked.connect(self.handle_recurrence_selection)

        recurrence_type = self.reminder["recurrence"].get("type", "one_time")
        if recurrence_type == "one_time":
            self.one_time_radio.setChecked(True)
        elif recurrence_type == "daily":
            self.daily_radio.setChecked(True)
        elif recurrence_type == "weekly":
            self.weekly_radio.setChecked(True)
            self.weekly_interval = self.reminder["recurrence"].get("interval", 1)
            self.weekly_layout_widget.setVisible(True)
            for day, cb in self.weekly_checkboxes.items():
                cb.setChecked(day in self.reminder["recurrence"].get("days", []))
            self.weekly_interval_spinbox.setValue(self.weekly_interval)

        elif recurrence_type == "monthly":
            self.monthly_radio.setChecked(True)
            self.monthly_interval = self.reminder["recurrence"].get("interval", 1)
            self.monthly_layout_widget.setVisible(True)
            for month, cb in self.monthly_checkboxes.items():
                cb.setChecked(month in self.reminder["recurrence"].get("months", []))
            self.monthly_interval_spinbox.setValue(self.monthly_interval)



    def handle_recurrence_selection(self, button):
        if button == self.weekly_radio:
            self.weekly_layout_widget.setVisible(True)
            self.monthly_layout_widget.setVisible(False)
        elif button == self.monthly_radio:
            self.monthly_layout_widget.setVisible(True)
            self.weekly_layout_widget.setVisible(False)
        else:
            self.weekly_layout_widget.setVisible(False)
            self.monthly_layout_widget.setVisible(False)


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
            interval = self.weekly_interval_spinbox.value()
            days = [day for day, cb in self.weekly_checkboxes.items() if cb.isChecked()]
            recurrence = {"type": "weekly", "interval": interval, "days": days}
        elif self.monthly_radio.isChecked():
            interval = self.monthly_interval_spinbox.value()
            months = [month for month, cb in self.monthly_checkboxes.items() if cb.isChecked()]
            recurrence = {"type": "monthly", "interval": interval, "months": months}

        return {
            "task_name": task_name,
            "start_time": start_time,
            "audio_file": audio_file,
            "pre_audio_file": pre_audio_file if pre_audio_file != "None" else None,
            "loops": loops,
            "delay_between_loops": delay_between_loops,
            "recurrence": recurrence,
            "active": self.active_checkbox.isChecked()
        }

    def delete_reminder(self):
        reply = QMessageBox.question(
            self,
            "Delete Reminder",
            "Are you sure you want to delete this reminder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.parent().currently_playing_reminder == self.reminder:
                self.parent().stop_audio()
            self.parent().delete_reminder(self.reminder)
            self.accept()

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
            self.weekly_layout_widget.setVisible(True)
            self.monthly_layout_widget.setVisible(False)
        elif button == self.monthly_radio:
            self.monthly_layout_widget.setVisible(True)
            self.weekly_layout_widget.setVisible(False)
        else:
            self.weekly_layout_widget.setVisible(False)
            self.monthly_layout_widget.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskScheduler()
    window.show()
    sys.exit(app.exec())
