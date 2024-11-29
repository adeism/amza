from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QDateTimeEdit, QSpinBox,
                             QRadioButton, QButtonGroup, QComboBox, QPushButton)
from PyQt6.QtCore import QDateTime

class TaskForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        form_layout = QVBoxLayout(self)

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
        loops_delay_layout.addWidget(loops_label)
        loops_delay_layout.addWidget(self.loops_spinbox)

        delay_label = QLabel("Delay between loops (s):")
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 3600)
        self.delay_spinbox.setValue(0)
        loops_delay_layout.addWidget(delay_label)
        loops_delay_layout.addWidget(self.delay_spinbox)
        audio_layout.addLayout(loops_delay_layout)

        pre_audio_layout = QHBoxLayout()
        self.pre_audio_combo = QComboBox()
        self.pre_audio_combo.setPlaceholderText("Select Pre-Audio")
        pre_audio_layout.addWidget(self.pre_audio_combo)
        self.preview_pre_audio_button = QPushButton("Preview")
        pre_audio_layout.addWidget(self.preview_pre_audio_button)
        audio_layout.addLayout(pre_audio_layout)

        main_audio_layout = QHBoxLayout()
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setPlaceholderText("No audio selected")
        main_audio_layout.addWidget(self.audio_path_edit)

        self.select_audio_button = QPushButton("Select Audio")  # Button text changed
        main_audio_layout.addWidget(self.select_audio_button)
        self.preview_audio_button = QPushButton("Preview")
        main_audio_layout.addWidget(self.preview_audio_button)
        audio_layout.addLayout(main_audio_layout)

        form_layout.addLayout(audio_layout)
        self.add_button = QPushButton("Add Reminder")
        form_layout.addWidget(self.add_button)