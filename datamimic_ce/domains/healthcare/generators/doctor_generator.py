# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor generator utilities.

This module provides utility functions for generating doctor data.
"""

import random
from typing import TypeVar

T = TypeVar("T")  # Define a type variable for generic typing


def weighted_choice(choices: list[tuple[T, float]]) -> T:
    """Choose a random item from a weighted list.

    Args:
        choices: A list of tuples containing items and their weights

    Returns:
        A randomly selected item based on weights
    """
    if not choices:
        raise ValueError("Cannot make a weighted choice from an empty list")

    # Extract items and weights
    items = [item for item, _ in choices]
    weights = [weight for _, weight in choices]

    # Make a weighted choice
    return random.choices(items, weights=weights, k=1)[0]


def generate_doctor_schedule(weekday_probability: float = 0.9, weekend_probability: float = 0.3) -> dict[str, str]:
    """Generate a doctor's weekly schedule.

    Args:
        weekday_probability: Probability of working on a weekday
        weekend_probability: Probability of working on a weekend

    Returns:
        A dictionary mapping days to hours
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    hours = {}

    for day in days:
        if random.random() < weekday_probability:
            start_hour = random.randint(7, 10)
            end_hour = random.randint(16, 19)
            hours[day] = f"{start_hour:02d}:00 - {end_hour:02d}:00"
        else:
            hours[day] = "Closed"

    # Weekend hours
    for day in ["Saturday", "Sunday"]:
        if random.random() < weekend_probability:
            start_hour = random.randint(8, 11)
            end_hour = random.randint(14, 17)
            hours[day] = f"{start_hour:02d}:00 - {end_hour:02d}:00"
        else:
            hours[day] = "Closed"

    return hours


def generate_doctor_email(first_name: str, last_name: str) -> str:
    """Generate a doctor's email address.

    Args:
        first_name: The doctor's first name
        last_name: The doctor's last name

    Returns:
        An email address
    """
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com"]
    first = first_name.lower()
    last = last_name.lower()
    domain = random.choice(domains)

    email_formats = [
        f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}{last[0]}@{domain}",
        f"{first}_{last}@{domain}",
        f"dr.{last}@{domain}",
    ]

    return random.choice(email_formats)


def generate_doctor_phone() -> str:
    """Generate a doctor's phone number.

    Returns:
        A formatted phone number
    """
    area_code = random.randint(100, 999)
    prefix = random.randint(100, 999)
    line = random.randint(1000, 9999)
    return f"({area_code}) {prefix}-{line}"


def generate_doctor_id() -> str:
    """Generate a unique doctor ID.

    Returns:
        A unique doctor ID
    """
    import uuid

    return f"DOC-{uuid.uuid4().hex[:8].upper()}"


def generate_npi_number() -> str:
    """Generate an NPI (National Provider Identifier) number.

    Returns:
        A 10-digit NPI number
    """
    return "".join(str(random.randint(0, 9)) for _ in range(10))


def generate_license_number() -> str:
    """Generate a medical license number.

    Returns:
        A medical license number
    """
    import string

    prefix = "".join(random.choices(string.ascii_uppercase, k=2))
    number = "".join(random.choices(string.digits, k=6))
    return f"{prefix}-{number}"


def calculate_graduation_year(age: int) -> int:
    """Calculate a plausible graduation year based on age.

    Args:
        age: The doctor's age

    Returns:
        A graduation year
    """
    import datetime

    current_year = datetime.datetime.now().year
    min_years_after_graduation = 5  # Minimum years after graduation
    max_years_after_graduation = 45  # Maximum years after graduation

    # Calculate graduation year based on age and years after graduation
    years_after_graduation = random.randint(
        min_years_after_graduation,
        min(max_years_after_graduation, age - 25),  # Assume graduated at 25 at the earliest
    )
    return current_year - years_after_graduation
