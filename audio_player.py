import pygame
import os
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, QTimer, QObject
from PyQt6.QtWidgets import QMessageBox

class AudioPlayerThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, audio_file, loops=1, duration_seconds=None, parent=None):
        super().__init__(parent)
        self.audio_file = audio_file
        self.loops = loops
        self.duration_seconds = duration_seconds

    def run(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.audio_file)
            if self.duration_seconds:
                pygame.mixer.music.play()
                pygame.time.wait(int(self.duration_seconds * 1000))
                pygame.mixer.music.stop()
            else:
                pygame.mixer.music.play(loops=self.loops - 1)
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            self.finished.emit()
        except pygame.error as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))

class AudioPlayer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.mixer.init()
        self.currently_playing = None
        self.thread = None
        self.parent = parent

    def play_reminder(self, reminder):
        pre_audio_file = reminder.get("pre_audio_file")
        audio_file = reminder.get("audio_file")
        loops = reminder.get("loops", 1)
        delay_between_loops = reminder.get("delay_between_loops", 0)

        if pre_audio_file:
            pre_audio_path = os.path.join("preaudio", pre_audio_file)
            self.play_audio(pre_audio_path, loops=1)

        if loops > 1 and delay_between_loops > 0:
            for i in range(loops):
                self.play_audio(audio_file, loops=1)
                if i < loops - 1:
                    self.wait(int(delay_between_loops * 1000))
        else:
            self.play_audio(audio_file, loops=loops)

    def play_audio(self, audio_file, loops=1, duration_seconds=None):
        if self.thread is not None and self.thread.isRunning():
            self.stop_audio()

        self.thread = AudioPlayerThread(audio_file, loops, duration_seconds=duration_seconds)
        self.thread.finished.connect(self.on_audio_finished)
        self.thread.error.connect(self.on_audio_error)
        self.thread.start()

    def stop_audio(self):
        if self.thread is not None and self.thread.isRunning():
            pygame.mixer.music.stop()
            self.thread.terminate()
            self.thread.wait()
            self.thread = None

    def load_pre_audio_files(self):
        files = ["None"] + [f for f in os.listdir("preaudio") if f.lower().endswith(('.mp3', '.wav'))]
        return files

    def preview_pre_audio(self, selected_file):
        if selected_file and selected_file != "None":
            pre_audio_path = os.path.join("preaudio", selected_file)
            self.play_audio(pre_audio_path, loops=1, duration_seconds=5)

    def preview_audio(self, audio_file):
        if audio_file:
            self.play_audio(audio_file, loops=1, duration_seconds=5)

    def wait(self, milliseconds):
        timer = QTimer()
        timer.singleShot(milliseconds, self.thread.finished.emit)
        timer.start()

    @pyqtSlot()
    def on_audio_finished(self):
        self.thread = None
        self.currently_playing = None

    @pyqtSlot(str)
    def on_audio_error(self, error_message):
        self.thread = None
        self.currently_playing = None
        print(f"Audio playback error: {error_message}")
        QMessageBox.warning(self.parent, "Error", f"Audio playback error: {error_message}")