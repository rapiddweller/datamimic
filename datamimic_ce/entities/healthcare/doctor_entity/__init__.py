# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor entity package for generating realistic doctor data.

This package provides classes and functions for generating realistic doctor data,
including doctor IDs, names, specialties, license numbers, contact information,
education, certifications, and schedules.
"""

from datamimic_ce.entities.healthcare.doctor_entity.core import DoctorEntity
from datamimic_ce.entities.healthcare.doctor_entity.data_loader import DoctorDataLoader
from datamimic_ce.entities.healthcare.doctor_entity.generators import DoctorGenerators
from datamimic_ce.entities.healthcare.doctor_entity.utils import (
    PropertyCache,
    format_phone_number,
    generate_email,
    generate_license_number,
    generate_npi_number,
    parse_weighted_value,
    weighted_choice,
)

__all__ = [
    "DoctorEntity",
    "DoctorDataLoader",
    "DoctorGenerators",
    "PropertyCache",
    "weighted_choice",
    "parse_weighted_value",
    "generate_license_number",
    "generate_npi_number",
    "format_phone_number",
    "generate_email",
]
