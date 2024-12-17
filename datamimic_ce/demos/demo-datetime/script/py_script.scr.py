from datetime import datetime, timedelta


def add_days(current_date: datetime, days: int):
    return current_date + timedelta(days=days)
