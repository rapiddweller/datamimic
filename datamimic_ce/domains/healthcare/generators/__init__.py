# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Healthcare domain generators.

This module provides generators for the healthcare domain entities.
"""

from datamimic_ce.domains.healthcare.generators.doctor_generator import (
    calculate_graduation_year,
    generate_doctor_email,
    generate_doctor_id,
    generate_doctor_phone,
    generate_doctor_schedule,
    generate_license_number,
    generate_npi_number,
    weighted_choice,
)

__all__ = [
    "weighted_choice",
    "generate_doctor_schedule",
    "generate_doctor_email",
    "generate_doctor_phone",
    "generate_doctor_id",
    "generate_npi_number",
    "generate_license_number",
    "calculate_graduation_year",
]
