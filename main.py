import sys
from PyQt6.QtWidgets import QApplication
from taskscheduler import TaskScheduler

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskScheduler()
    window.show()
    sys.exit(app.exec())