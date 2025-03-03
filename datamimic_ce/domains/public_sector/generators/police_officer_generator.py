# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police officer generator utilities.

This module provides utility functions for generating police officer data.
"""

import datetime
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


def generate_officer_id() -> str:
    """Generate a unique officer ID.

    Returns:
        A unique officer ID
    """
    import uuid

    return f"OFF-{uuid.uuid4().hex[:8].upper()}"


def generate_badge_number() -> str:
    """Generate a badge number.

    Returns:
        A badge number
    """
    return f"{random.randint(1000, 9999)}"


def generate_police_unit() -> str:
    """Generate a police unit.

    Returns:
        A police unit name
    """
    units = [
        "Patrol",
        "Traffic",
        "Detectives",
        "SWAT",
        "K-9",
        "Narcotics",
        "Homicide",
        "Internal Affairs",
        "Community Relations",
        "Juvenile",
        "Cyber Crimes",
        "Evidence",
        "Training",
    ]
    return random.choice(units)


def generate_hire_date(age: int) -> str:
    """Generate a hire date based on age.

    Args:
        age: The officer's age

    Returns:
        A hire date in YYYY-MM-DD format
    """
    # Calculate a reasonable hire date
    years_of_service = random.randint(1, min(30, age - 21))  # Assume minimum age of 21 to join
    current_date = datetime.datetime.now()
    hire_date = current_date - datetime.timedelta(days=years_of_service * 365)
    return hire_date.strftime("%Y-%m-%d")


def calculate_years_of_service(hire_date: str) -> int:
    """Calculate years of service based on hire date.

    Args:
        hire_date: The hire date in YYYY-MM-DD format

    Returns:
        Years of service
    """
    hire_date_obj = datetime.datetime.strptime(hire_date, "%Y-%m-%d")
    current_date = datetime.datetime.now()
    return (current_date - hire_date_obj).days // 365


def generate_police_certifications(count: int = None) -> list[str]:
    """Generate a list of police certifications.

    Args:
        count: The number of certifications to generate (default: random 1-4)

    Returns:
        A list of certifications
    """
    all_certifications = [
        "Basic Law Enforcement",
        "Advanced Law Enforcement",
        "Firearms Training",
        "Defensive Tactics",
        "Emergency Vehicle Operations",
        "Crisis Intervention",
        "De-escalation Techniques",
        "First Aid/CPR",
        "Narcotics Investigation",
        "Hostage Negotiation",
        "K-9 Handler",
        "SWAT Operations",
        "Cyber Crime Investigation",
        "Crime Scene Investigation",
        "Motorcycle Patrol",
    ]

    if count is None:
        count = random.randint(1, 4)

    return random.sample(all_certifications, min(count, len(all_certifications)))


def generate_shift() -> str:
    """Generate a work shift.

    Returns:
        A shift name
    """
    shifts = ["Day Shift (7AM-3PM)", "Evening Shift (3PM-11PM)", "Night Shift (11PM-7AM)", "Rotating Shift"]
    return random.choice(shifts)


def generate_police_email(first_name: str, last_name: str, badge_number: str, department: str) -> str:
    """Generate a police officer email.

    Args:
        first_name: The officer's first name
        last_name: The officer's last name
        badge_number: The officer's badge number
        department: The officer's department

    Returns:
        An email address
    """
    # Simplify department name for email domain
    domain = department.lower()
    domain = domain.replace(" police department", "pd")
    domain = domain.replace(" county sheriff's office", "sheriff")
    domain = domain.replace(" ", "")

    # Create email formats
    email_formats = [
        f"{first_name.lower()}.{last_name.lower()}@{domain}.gov",
        f"{first_name.lower()[0]}{last_name.lower()}@{domain}.gov",
        f"{badge_number}@{domain}.gov",
        f"{last_name.lower()}.{badge_number}@{domain}.gov",
    ]

    return random.choice(email_formats)


def generate_languages(include_english: bool = True) -> list[str]:
    """Generate a list of languages.

    Args:
        include_english: Whether to include English as the primary language

    Returns:
        A list of languages
    """
    languages = ["English"] if include_english else []

    # Chance to add additional languages
    additional_languages = [
        "Spanish",
        "French",
        "German",
        "Chinese",
        "Arabic",
        "Russian",
        "Japanese",
        "Korean",
        "Portuguese",
        "Italian",
    ]
    num_additional = random.randint(0, 2)

    if num_additional > 0:
        languages.extend(random.sample(additional_languages, num_additional))

    return languages
