from PyQt6.QtWidgets import QTableWidgetItem, QPushButton, QHeaderView
from PyQt6.QtCore import  QDateTime, Qt
from PyQt6.QtGui import QIcon

class ReminderTableManager:
    def __init__(self, parent):
        self.parent = parent

    def refresh_tables(self, reminders):
        self.parent.task_tables.active_table.setRowCount(0)
        self.parent.task_tables.inactive_table.setRowCount(0)
        for i, reminder in enumerate(reminders):
            table = self.parent.task_tables.active_table if reminder["active"] else self.parent.task_tables.inactive_table
            self.add_reminder_to_table(table, reminder, i)

    def add_reminder_to_table(self, table, reminder, row_index):
        row_position = table.rowCount()
        table.insertRow(row_position)

        play_button = QPushButton()
        play_button.setIcon(QIcon.fromTheme('media-playback-start'))
        play_button.clicked.connect(lambda _, r=reminder, b=play_button: self.parent.reminder_actions.toggle_audio(r, b))
        play_button.setFixedSize(30, 30)

        edit_button = QPushButton()
        edit_button.setIcon(QIcon.fromTheme('document-open'))
        edit_button.clicked.connect(lambda _, ri=row_index: self.parent.show_edit_dialog(ri))
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
            days_str = ", ".join(days)
            return f"Weekly, every {interval} week(s) on {days_str}"
        elif rec_type == "monthly":
            interval = recurrence.get("interval", 1)
            months = recurrence.get("months", [])
            months_str = ", ".join(months)
            return f"Monthly, every {interval} month(s) on {months_str}"
        else:
            return "One time"