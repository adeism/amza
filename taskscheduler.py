import sys
import os
import json
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QStatusBar, QMessageBox, QDialog, QFileDialog
)
from PyQt6.QtCore import QDateTime, QTimer, Qt
from PyQt6.QtGui import QIcon

from audio_player import AudioPlayer
from reminder_manager import ReminderManager
from recurrence_dialog import create_weekly_dialog, create_monthly_dialog
from edit_reminder_dialog import EditReminderDialog
from task_form import TaskForm
from task_tables import TaskTables
from reminder_table_manager import ReminderTableManager
from reminder_actions import ReminderActions

class TaskScheduler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMZ Announcement")
        self.setGeometry(100, 100, 800, 600)
        self.reminder_manager = ReminderManager("reminders.json")
        self.audio_player = AudioPlayer(self)
        self.reminder_table_manager = ReminderTableManager(self)
        self.reminder_actions = ReminderActions(self)

        self.currently_playing_reminder = None
        self.currently_playing_button = None
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(1000)

        # Connect signals and slots
        self.task_form.recurrence_group.buttonClicked.connect(self.handle_recurrence_selection)
        self.task_form.add_button.clicked.connect(self.add_reminder)
        self.task_form.select_audio_button.clicked.connect(self.upload_audio) #changed button name
        self.task_form.preview_audio_button.clicked.connect(self.preview_audio)
        self.task_form.preview_pre_audio_button.clicked.connect(self.preview_pre_audio)

        self.task_tables.inactive_button.clicked.connect(self.toggle_inactive_tasks)
        self.task_tables.active_table.cellClicked.connect(self.handle_table_click)
        self.task_tables.inactive_table.cellClicked.connect(self.handle_table_click)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Exit Confirmation", "Are you sure you want to exit?\nReminders will not function if closed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def init_ui(self):
        self.create_central_widget()
        self.create_status_bar()

    def create_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.task_form = TaskForm()
        self.task_tables = TaskTables()
        self.main_layout.addWidget(self.task_form)
        self.main_layout.addWidget(self.task_tables)
        self.load_pre_audio_files()
        self.refresh_tables()

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def handle_recurrence_selection(self, button):
        if button == self.task_form.weekly_radio:
            dialog = create_weekly_dialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.weekly_interval, self.weekly_days = dialog.get_values()
            else:
                self.task_form.one_time_radio.setChecked(True)
                self.weekly_interval = None
                self.weekly_days = None
        elif button == self.task_form.monthly_radio:
            dialog = create_monthly_dialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.monthly_interval, self.monthly_months = dialog.get_values()
            else:
                self.task_form.one_time_radio.setChecked(True)
                self.monthly_interval = None
                self.monthly_months = None
        else:
            self.weekly_interval = None
            self.weekly_days = None
            self.monthly_interval = None
            self.monthly_months = None

    def upload_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Main Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.task_form.audio_path_edit.setText(file_path)

    def preview_audio(self):
        audio_file = self.task_form.audio_path_edit.text()
        if audio_file:
            self.audio_player.preview_audio(audio_file)
        else:
            self.status_bar.showMessage("No audio file selected.", 5000)

    def load_pre_audio_files(self):
        pre_audio_files = self.audio_player.load_pre_audio_files()
        self.task_form.pre_audio_combo.clear()
        self.task_form.pre_audio_combo.addItems(pre_audio_files)

    def preview_pre_audio(self):
        selected_file = self.task_form.pre_audio_combo.currentText()
        self.audio_player.preview_pre_audio(selected_file)

    def add_reminder(self):
        reminder_data = self.get_reminder_data()
        self.reminder_actions.add_reminder(reminder_data)

    def get_reminder_data(self):
        task_name = self.task_form.task_name_edit.text()
        start_time = self.task_form.start_datetime.dateTime().toSecsSinceEpoch()
        audio_file = self.task_form.audio_path_edit.text()
        pre_audio_file = self.task_form.pre_audio_combo.currentText()
        loops = self.task_form.loops_spinbox.value()
        delay_between_loops = self.task_form.delay_spinbox.value()
        recurrence = self.get_recurrence_data()
        return {
            "task_name": task_name,
            "start_time": start_time,
            "audio_file": audio_file,
            "pre_audio_file": pre_audio_file if pre_audio_file != "None" else None,
            "loops": loops,
            "delay_between_loops": delay_between_loops,
            "recurrence": recurrence,
        }

    def get_recurrence_data(self):
        if self.task_form.one_time_radio.isChecked():
            return {"type": "one_time"}
        elif self.task_form.daily_radio.isChecked():
            return {"type": "daily"}
        elif self.task_form.weekly_radio.isChecked():
            return {"type": "weekly", "interval": self.weekly_interval, "days": self.weekly_days}
        elif self.task_form.monthly_radio.isChecked():
            return {"type": "monthly", "interval": self.monthly_interval, "months": self.monthly_months}
        else:
            return {"type": "one_time"}

    def toggle_inactive_tasks(self):
        self.task_tables.inactive_table.setVisible(not self.task_tables.inactive_table.isVisible())
        self.task_tables.inactive_button.setText("Hide Inactive Tasks" if self.task_tables.inactive_table.isVisible() else "Show Inactive Tasks")

    def clear_inputs(self):
        self.task_form.task_name_edit.clear()
        self.task_form.start_datetime.setDateTime(QDateTime.currentDateTime())
        self.task_form.loops_spinbox.setValue(1)
        self.task_form.delay_spinbox.setValue(0)
        self.task_form.one_time_radio.setChecked(True)
        self.task_form.audio_path_edit.clear()
        self.task_form.pre_audio_combo.setCurrentIndex(0)
        self.weekly_interval = None
        self.weekly_days = None
        self.monthly_interval = None
        self.monthly_months = None

    def check_reminders(self):
        current_time = datetime.now().timestamp()
        reminders_to_play = self.reminder_manager.get_reminders_to_play(current_time)

        for reminder in reminders_to_play:
            self.audio_player.play_reminder(reminder)
            self.show_reminder_popup(reminder)
            self.reminder_manager.update_reminder_time(reminder)

        self.refresh_tables()

    def show_reminder_popup(self, reminder):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Reminder Alert")
        msg_box.setText(f"Task: {reminder['task_name']}")

        stop_button = msg_box.addButton("Stop Audio", QMessageBox.ButtonRole.ActionRole)
        minimize_button = msg_box.addButton("Minimize", QMessageBox.ButtonRole.ActionRole)

        stop_button.clicked.connect(self.audio_player.stop_audio)
        minimize_button.clicked.connect(self.showMinimized)

        msg_box.exec()

    def minimize_app(self):
        self.showMinimized()

    def refresh_tables(self):
        self.reminder_table_manager.refresh_tables(self.reminder_manager.reminders)

    def show_edit_dialog(self, row_index):
        reminder = self.reminder_manager.reminders[row_index]
        dialog = EditReminderDialog(self, reminder, row_index)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_reminder = dialog.get_values()
            self.reminder_actions.edit_reminder(row_index, updated_reminder)

    def handle_table_click(self, row, col):
        table = self.sender()
        if col == 3: #Play button
            row_index = table.currentRow()
            reminder = self.reminder_manager.reminders[row_index]
            button = table.cellWidget(row, col)
            self.audio_player.stop_audio() #added to stop audio before showing edit dialog
            self.reminder_actions.toggle_audio(reminder, button)

        elif col == 4: #Edit button
            self.audio_player.stop_audio() #added to stop audio before showing edit dialog
            row_index = table.currentRow()
            self.show_edit_dialog(row_index)