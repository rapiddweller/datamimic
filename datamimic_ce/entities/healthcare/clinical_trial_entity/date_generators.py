# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Date generators for the Clinical Trial Entity.

This module provides functions for generating various dates related to clinical trials.
"""

import random
from datetime import datetime, timedelta


def generate_start_date(min_years_ago: int = 5, max_years_ago: int = 0) -> datetime:
    """Generate a start date for a clinical trial.

    Args:
        min_years_ago: Minimum number of years ago for the start date
        max_years_ago: Maximum number of years ago for the start date

    Returns:
        A datetime object representing the start date
    """
    # Calculate the date range
    now = datetime.now()
    min_date = now - timedelta(days=365 * min_years_ago)
    max_date = now - timedelta(days=365 * max_years_ago) if max_years_ago > 0 else now

    # Generate a random date within the range
    days_diff = (max_date - min_date).days
    random_days = random.randint(0, days_diff)
    return min_date + timedelta(days=random_days)


def generate_end_date(start_date: datetime, status: str) -> datetime | None:
    """Generate an end date for a clinical trial based on the start date and status.

    Args:
        start_date: The start date of the trial
        status: The status of the trial

    Returns:
        A datetime object representing the end date, or None if the trial is ongoing
    """
    # If the trial is completed, terminated, or withdrawn, generate an end date
    if status.lower() in ["completed", "terminated", "withdrawn"]:
        # Calculate a random duration between 6 months and 5 years
        min_duration = 180  # 6 months in days
        max_duration = 1825  # 5 years in days
        duration = random.randint(min_duration, max_duration)
        return start_date + timedelta(days=duration)

    # If the trial is recruiting, active but not recruiting, or not yet recruiting,
    # it doesn't have an end date yet
    return None


def generate_primary_completion_date(start_date: datetime, end_date: datetime | None, status: str) -> datetime | None:
    """Generate a primary completion date for a clinical trial.

    Args:
        start_date: The start date of the trial
        end_date: The end date of the trial, or None if the trial is ongoing
        status: The status of the trial

    Returns:
        A datetime object representing the primary completion date, or None if not applicable
    """
    # If the trial is completed, the primary completion date is before the end date
    if status.lower() == "completed" and end_date:
        # Calculate a random date between the start date and end date, biased towards the end
        days_diff = (end_date - start_date).days
        # Primary completion is typically near the end, so use the last 25% of the trial period
        min_days = int(days_diff * 0.75)
        random_days = random.randint(min_days, days_diff)
        return start_date + timedelta(days=random_days)

    # If the trial is terminated or withdrawn, the primary completion date might not exist
    if status.lower() in ["terminated", "withdrawn"]:
        # 50% chance of having a primary completion date
        if random.random() < 0.5:
            return None
        # If it has one, it's before the end date
        if end_date:
            days_diff = (end_date - start_date).days
            random_days = random.randint(0, days_diff)
            return start_date + timedelta(days=random_days)

    # For ongoing trials, primary completion date might be in the future
    if status.lower() in ["recruiting", "active, not recruiting"]:
        # Calculate a future date between 6 months and 2 years from now
        now = datetime.now()
        min_future = 180  # 6 months in days
        max_future = 730  # 2 years in days
        future_days = random.randint(min_future, max_future)
        return now + timedelta(days=future_days)

    # For not yet recruiting trials, primary completion date is further in the future
    if status.lower() == "not yet recruiting":
        # Calculate a future date between 1 and 3 years from now
        now = datetime.now()
        min_future = 365  # 1 year in days
        max_future = 1095  # 3 years in days
        future_days = random.randint(min_future, max_future)
        return now + timedelta(days=future_days)

    return None


def generate_date_range(status: str) -> dict[str, datetime | None]:
    """Generate a consistent set of dates for a clinical trial based on its status.

    Args:
        status: The status of the trial

    Returns:
        A dictionary containing the start date, primary completion date, and end date
    """
    # Generate a start date
    start_date = generate_start_date()

    # Generate an end date based on the start date and status
    end_date = generate_end_date(start_date, status)

    # Generate a primary completion date
    primary_completion_date = generate_primary_completion_date(start_date, end_date, status)

    return {
        "start_date": start_date,
        "primary_completion_date": primary_completion_date,
        "end_date": end_date,
    }
