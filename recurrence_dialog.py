from PyQt6.QtWidgets import (
    QDialog, QLabel, QSpinBox, QHBoxLayout, QVBoxLayout, QGridLayout, QCheckBox,
    QDialogButtonBox
)

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

