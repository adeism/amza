import json
from datetime import datetime, timedelta
import os

class ReminderManager:
    def __init__(self, reminders_file):
        self.reminders_file = reminders_file
        self.reminders = self.load_reminders()

    def load_reminders(self):
        if os.path.exists(self.reminders_file):
            with open(self.reminders_file, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_reminders(self):
        with open(self.reminders_file, "w") as f:
            json.dump(self.reminders, f, indent=4)

    def get_reminders_to_play(self, current_time):
        return [r for r in self.reminders if r["active"] and r["start_time"] <= current_time]

    def update_reminder_time(self, reminder):
        recurrence = reminder.get("recurrence", {"type": "one_time"})
        rec_type = recurrence.get("type", "one_time")

        if rec_type == "one_time":
            reminder["active"] = False
        elif rec_type == "daily":
            reminder["start_time"] += 86400  # Add one day (seconds)
        elif rec_type == "weekly":
            interval = recurrence.get("interval", 1)
            days = recurrence.get("days", [])
            next_time = self.compute_next_weekly_occurrence(reminder["start_time"], interval, days)
            if next_time:
                reminder["start_time"] = next_time
            else:
                reminder["active"] = False
        elif rec_type == "monthly":
            interval = recurrence.get("interval", 1)
            months = recurrence.get("months", [])
            next_time = self.compute_next_monthly_occurrence(reminder["start_time"], interval, months)
            if next_time:
                reminder["start_time"] = next_time
            else:
                reminder["active"] = False
        else:
            reminder["active"] = False
        self.save_reminders()

    def compute_next_weekly_occurrence(self, last_time, interval, days):
        day_numbers = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        selected_days = [day_numbers[day] for day in days]
        if not selected_days:
            return None

        last_datetime = datetime.fromtimestamp(last_time)
        next_datetime = last_datetime + timedelta(days=1)
        weeks_added = 0

        while weeks_added < 52: # Limit to 52 weeks to prevent infinite loop
            day_of_week = next_datetime.weekday()
            if day_of_week in selected_days:
                weeks_since_start = ((next_datetime - last_datetime).days) // 7
                if weeks_since_start % interval == 0:
                    if next_datetime.timestamp() > last_time:
                        return int(next_datetime.timestamp())
            next_datetime += timedelta(days=1)
            if next_datetime.weekday() == 0:
                weeks_added += 1
        return None

    def compute_next_monthly_occurrence(self, last_time, interval, months):
        month_numbers = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5,
            "June": 6, "July": 7, "August": 8, "September": 9, "October": 10,
            "November": 11, "December": 12,
        }
        selected_months = [month_numbers[month] for month in months]
        if not selected_months:
            return None

        last_datetime = datetime.fromtimestamp(last_time)
        next_datetime = last_datetime + timedelta(days=1)
        months_added = 0

        while months_added < 120: # Limit to 10 years to prevent infinite loop
            month = next_datetime.month
            if month in selected_months:
                months_since_start = (next_datetime.year - last_datetime.year) * 12 + (next_datetime.month - last_datetime.month)
                if months_since_start % interval == 0:
                    if next_datetime.timestamp() > last_time:
                        return int(next_datetime.timestamp())

            next_datetime += timedelta(days=31) # Approximate, adjust if needed for accuracy

            months_added += 1

        return None

    def add_reminder(self, reminder):
        self.reminders.append(reminder)
        self.save_reminders()

    def delete_reminder(self, reminder):
        self.reminders.remove(reminder)
        self.save_reminders()