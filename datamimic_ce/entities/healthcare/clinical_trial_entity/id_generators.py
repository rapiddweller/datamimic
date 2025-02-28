# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
ID generators for the Clinical Trial Entity.

This module provides functions for generating various IDs related to clinical trials.
"""

import random
import string
from datetime import datetime

from datamimic_ce.entities.healthcare.clinical_trial_entity.utils import generate_trial_id


def generate_nct_id() -> str:
    """Generate a unique NCT (National Clinical Trial) identifier.

    Returns:
        A string in the format "NCT" followed by 8 digits
    """
    return generate_trial_id()


def generate_irb_number() -> str:
    """Generate an IRB (Institutional Review Board) number.

    Returns:
        A string representing an IRB number
    """
    # Generate a random IRB number in the format "IRB-YYYY-NNNN"
    year = random.randint(datetime.now().year - 5, datetime.now().year)
    number = random.randint(1000, 9999)
    return f"IRB-{year}-{number}"


def generate_protocol_id(sponsor_prefix: str | None = None) -> str:
    """Generate a protocol ID.

    Args:
        sponsor_prefix: Optional prefix to use for the protocol ID

    Returns:
        A string representing a protocol ID
    """
    # If a sponsor prefix is provided, use it
    if sponsor_prefix:
        # Clean the prefix to use only alphanumeric characters
        prefix = ''.join(c for c in sponsor_prefix if c.isalnum())[:3].upper()
    else:
        # Generate a random 3-letter prefix
        prefix = ''.join(random.choices(string.ascii_uppercase, k=3))

    # Generate a random protocol ID in the format "PREFIX-NNNN"
    number = random.randint(1000, 9999)
    return f"{prefix}-{number}"


def generate_eudract_number() -> str:
    """Generate a EudraCT (European Union Drug Regulating Authorities Clinical Trials) number.

    Returns:
        A string representing a EudraCT number
    """
    # Generate a random EudraCT number in the format "YYYY-NNNNNN-CC"
    year = random.randint(datetime.now().year - 10, datetime.now().year)
    number = random.randint(100000, 999999)
    check = random.randint(10, 99)
    return f"{year}-{number}-{check}"
