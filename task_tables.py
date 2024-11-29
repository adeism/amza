from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QVBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon #Import QIcon


class TaskTables(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.active_table = QTableWidget()
        self.active_table.setColumnCount(5)
        self.active_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "Play", "Edit"])
        self.setup_table(self.active_table)
        layout.addWidget(self.active_table)

        self.inactive_button = QPushButton("Show Inactive Tasks")
        layout.addWidget(self.inactive_button)

        self.inactive_table = QTableWidget()
        self.inactive_table.setColumnCount(5)
        self.inactive_table.setHorizontalHeaderLabels(["Task Name", "Start Time", "Recurrence", "Play", "Edit"])
        self.setup_table(self.inactive_table)
        self.inactive_table.setVisible(False)
        layout.addWidget(self.inactive_table)

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