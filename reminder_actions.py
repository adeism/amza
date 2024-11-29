from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon


class ReminderActions:
    def __init__(self, parent):
        self.parent = parent
        self.reminder_manager = parent.reminder_manager
        self.audio_player = parent.audio_player

    def add_reminder(self, reminder_data):
        reminder = {
            "task_name": reminder_data["task_name"],
            "start_time": reminder_data["start_time"],
            "recurrence": reminder_data["recurrence"],
            "audio_file": reminder_data["audio_file"],
            "pre_audio_file": reminder_data["pre_audio_file"],
            "loops": reminder_data["loops"],
            "delay_between_loops": reminder_data["delay_between_loops"],
            "active": True,
        }
        self.reminder_manager.add_reminder(reminder)
        self.parent.refresh_tables()
        self.parent.clear_inputs()
        self.parent.status_bar.showMessage("Reminder added successfully!", 5000)

    def edit_reminder(self, row_index, updated_reminder):
        self.reminder_manager.reminders[row_index] = updated_reminder
        self.reminder_manager.save_reminders()
        self.parent.refresh_tables()
        self.parent.status_bar.showMessage("Reminder updated successfully!", 5000)

    def delete_reminder(self, reminder):
        reply = QMessageBox.question(
            self.parent,
            "Delete Reminder",
            "Are you sure you want to delete this reminder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.parent.currently_playing_reminder == reminder:
                self.audio_player.stop_audio()
            self.reminder_manager.delete_reminder(reminder)
            self.parent.refresh_tables()
            self.parent.status_bar.showMessage("Reminder deleted successfully.", 5000)

    def toggle_audio(self, reminder, button):
        if self.parent.currently_playing_reminder == reminder:
            self.audio_player.stop_audio()
            self.parent.currently_playing_reminder = None
            if button:
                button.setIcon(QIcon.fromTheme('media-playback-start'))
        else:
            if self.parent.currently_playing_reminder:
                self.audio_player.stop_audio()

            self.audio_player.play_reminder(reminder)
            self.parent.currently_playing_reminder = reminder
            if button:
                button.setIcon(QIcon.fromTheme('media-playback-stop'))