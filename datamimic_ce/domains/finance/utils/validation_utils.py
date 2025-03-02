# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Finance validation utilities.

This module provides utility functions for validating financial data
such as credit card numbers, IBAN numbers, etc.
"""

import random
import re
from typing import List


def luhn_checksum(number: str) -> bool:
    """Validate a number using the Luhn algorithm.

    Args:
        number: The number to validate

    Returns:
        True if the number is valid according to the Luhn algorithm
    """
    # Remove any spaces or dashes
    number = number.replace(" ", "").replace("-", "")
    
    # Check that the number only consists of digits
    if not number.isdigit():
        return False
    
    # Calculate Luhn checksum
    digits = [int(d) for d in number]
    check_digit = digits.pop()
    digits.reverse()
    
    # Double every second digit
    processed_digits = []
    for i, d in enumerate(digits):
        if i % 2 == 0:
            d = d * 2
            if d > 9:
                d = d - 9
        processed_digits.append(d)
    
    # Add the check digit back
    processed_digits.append(check_digit)
    
    # If the sum is divisible by 10, the number is valid
    return sum(processed_digits) % 10 == 0


def generate_luhn_number(prefix: str, length: int) -> str:
    """Generate a valid number using the Luhn algorithm.

    Args:
        prefix: The prefix for the number
        length: The total length of the number including the prefix

    Returns:
        A valid number according to the Luhn algorithm
    """
    # Calculate the number of random digits needed
    num_random_digits = length - len(prefix) - 1  # -1 for the check digit
    
    # Generate random digits
    random_digits = [str(random.randint(0, 9)) for _ in range(num_random_digits)]
    
    # Combine prefix and random digits
    number = prefix + "".join(random_digits) + "0"  # Temporary check digit
    
    # Calculate the correct check digit
    digits = [int(d) for d in number]
    check_digit = digits.pop()  # Remove the temporary check digit
    digits.reverse()
    
    # Double every second digit
    processed_digits = []
    for i, d in enumerate(digits):
        if i % 2 == 0:
            d = d * 2
            if d > 9:
                d = d - 9
        processed_digits.append(d)
    
    # Calculate the correct check digit
    checksum = sum(processed_digits) % 10
    if checksum == 0:
        correct_check_digit = 0
    else:
        correct_check_digit = 10 - checksum
    
    # Replace the temporary check digit with the correct one
    number = number[:-1] + str(correct_check_digit)
    
    return number


def format_credit_card_number(number: str) -> str:
    """Format a credit card number with spaces.

    Args:
        number: The credit card number to format

    Returns:
        The formatted credit card number
    """
    # Remove any existing spaces or dashes
    number = number.replace(" ", "").replace("-", "")
    
    # Format the number with spaces every 4 digits
    if len(number) == 15:  # AMEX
        return f"{number[:4]} {number[4:10]} {number[10:]}"
    else:
        return " ".join([number[i:i+4] for i in range(0, len(number), 4)])


def validate_iban(iban: str) -> bool:
    """Validate an IBAN (International Bank Account Number).

    Args:
        iban: The IBAN to validate

    Returns:
        True if the IBAN is valid
    """
    # Remove spaces and convert to uppercase
    iban = iban.replace(" ", "").upper()
    
    # Basic format check
    if not re.match(r'^[A-Z]{2}[0-9A-Z]{2,30}$', iban):
        return False
    
    # Move the first 4 characters to the end
    rearranged = iban[4:] + iban[:4]
    
    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric = ""
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - 55)  # A=65-55=10, B=66-55=11, etc.
        else:
            numeric += char
    
    # Check if the numeric value is divisible by 97
    return int(numeric) % 97 == 1


def generate_us_routing_number() -> str:
    """Generate a valid US bank routing number.

    Returns:
        A valid US bank routing number
    """
    # The first digit must be 0, 1, 2, 3, 6, 7, or 8
    first_digit = random.choice([0, 1, 2, 3, 6, 7, 8])
    
    # Generate 7 more random digits
    digits = [first_digit] + [random.randint(0, 9) for _ in range(7)]
    
    # Calculate the checksum
    checksum = (
        3 * (digits[0] + digits[3] + digits[6]) +
        7 * (digits[1] + digits[4] + digits[7]) +
        (digits[2] + digits[5])
    ) % 10
    
    # If the checksum is not 0, subtract it from 10
    if checksum != 0:
        checksum = 10 - checksum
    
    # Add the checksum to the number
    digits.append(checksum)
    
    # Convert to string
    return "".join(str(d) for d in digits)