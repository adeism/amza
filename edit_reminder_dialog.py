from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateTimeEdit,
    QRadioButton, QButtonGroup, QComboBox, QPushButton, QFileDialog, QCheckBox,
    QDialogButtonBox, QMessageBox, QSpinBox, QWidget
)
from PyQt6.QtCore import QDateTime
import pygame
import os

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

        # MONTHLY RECURRENCE CHECKBOXES
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
        main_audio_layout.addWidget(self.audio_path_edit)

        self.select_audio_button = QPushButton("Select Audio")
        self.select_audio_button.clicked.connect(self.upload_audio)
        main_audio_layout.addWidget(self.select_audio_button)

        self.preview_audio_button = QPushButton("Preview")
        self.preview_audio_button.clicked.connect(self.preview_audio)
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
                self.parent().audio_player.stop_audio()
            self.parent().reminder_actions.delete_reminder(self.reminder) # Call delete through reminder_actions
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
                self.parent().audio_player.preview_pre_audio(selected_file)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error playing pre-audio: {e}")
        else:
            QMessageBox.warning(self, "Error", "No pre-audio file selected.")

    def preview_audio(self):
        audio_file = self.audio_path_edit.text()
        if audio_file and os.path.exists(audio_file):
            try:
                self.parent().audio_player.preview_audio(audio_file)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error playing audio: {e}")
        else:
            QMessageBox.warning(self, "Error", "Invalid audio file selected.")

    def upload_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Main Audio File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.audio_path_edit.setText(file_path)