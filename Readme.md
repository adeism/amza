# 📢 AMZ Announcement

AMZ Announcement is a task scheduling application built with Python and PyQt6. It allows users to create reminders that play audio files at specified times, with support for various recurrence patterns such as one-time, daily, weekly, and monthly reminders.

---

## 🖼️ Screenshots

![screenshot](https://github.com/adeism/amza/blob/main/ss.png?raw=true)

---

---

## ✨ Features

- 📝 **Create Reminders**: Add reminders with a task name, start time, and an audio file to be played.
- 🔁 **Recurrence Options**:
  - 🔂 **One-time**: Reminders that occur once at the specified time.
  - 📅 **Daily**: Reminders that occur every day at the specified time.
  - 📆 **Weekly**: Reminders that occur on specified days of the week, with customizable intervals.
  - 🗓️ **Monthly**: Reminders that occur monthly on the specified date.
- 🎵 **Audio Playback**:
  - ▶️ Play audio files associated with reminders.
  - 🔁 Supports playing audio once or in a loop until stopped.
- 🚨 **Reminder Notifications**:
  - ⚠️ Pop-up alerts when reminders trigger, with options to stop audio or minimize the application.
- ✅ **Task Management**:
  - 📋 View active and inactive reminders.
  - 🎛️ Play or stop audio directly from the task list.
  - ❌ Delete reminders as needed.

---

## 🚀 Installation

### 🚒 Prerequisites

- **Python 3.6 or higher**
- **Pip package manager**

### 📥 Dependencies

- **PyQt6**: For the GUI framework.
- **pygame**: For audio playback.

### 🗃️ Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/adeism/amza.git
   cd amza
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   If a `requirements.txt` file is not present, you can install the dependencies directly:

   ```bash
   pip install PyQt6 pygame
   ```

---

## 🖥️ Usage

1. **Run the Application**

   ```bash
   python app.py
   ```

2. **Add a Reminder**

   - Enter the **task name**.
   - Set the **start date and time**.
   - Choose a **recurrence type**:
     - 🔂 **One-time**
     - 📅 **Daily**
     - 📆 **Weekly** (Specify the interval and select the days of the week)
     - 🗓️ **Monthly**
   - Upload an **audio file** (`.mp3` or `.wav`) to be played when the reminder triggers.
   - Click **Add Reminder**.

3. **Manage Reminders**

   - **Active Tasks**: View and manage active reminders.
     - ▶️ Click the **Play** button to play the associated audio.
     - ❌ Click the **Delete** button to remove the reminder.
   - **Inactive Tasks**: Click **Show Inactive Tasks** to view reminders that are no longer active.
     - You can delete inactive reminders as well.

4. **Reminder Notifications**

   - When a reminder triggers, a **pop-up alert** will appear:
     - 🚫 **Stop Audio**: Stops the audio playback.
     - 📉 **Minimize**: Minimizes the application.

---



## ⚙️ Configuration

### 🔊 Supported Audio Formats

- `.mp3`
- `.wav`

### 🖼️ Custom Icons

If the play or delete icons do not display correctly, ensure that the icon files are present in the application directory. You can replace the default icons with your own by modifying the paths in the code.

---

## 📜 Notes

- **Audio Files**: Ensure that the audio files you select exist and are accessible. If an audio file is missing or cannot be played, an error message will be displayed.
- **Closing the Application**: Closing the application will stop all reminders. A confirmation dialog will appear when attempting to close the application.

---

## ❓ Troubleshooting

- **Icons Not Displaying**: Ensure that the icon files are in the correct path or use system theme icons if supported.
- **Audio Playback Issues**: Make sure `pygame` is properly installed and that your audio files are in a supported format (`.mp3` or `.wav`).
