from datetime import UTC, date, datetime, timedelta


def current_learning_streak(attendance_dates: list[str | date]) -> int:
    attended = {
        value if isinstance(value, date) else date.fromisoformat(value)
        for value in attendance_dates
        if value
    }
    today = datetime.now(UTC).date()
    streak = 0
    while today - timedelta(days=streak) in attended:
        streak += 1
    return streak
