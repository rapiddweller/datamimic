# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Healthcare domain module.

This module provides entities, data loaders, generators, and services for the healthcare domain.
"""

from datamimic_ce.domains.healthcare.data_loaders.doctor_loader import DoctorDataLoader
from datamimic_ce.domains.healthcare.data_loaders.hospital_loader import HospitalDataLoader
from datamimic_ce.domains.healthcare.data_loaders.patient_loader import PatientDataLoader
from datamimic_ce.domains.healthcare.models.doctor import Doctor
from datamimic_ce.domains.healthcare.models.hospital import Hospital
from datamimic_ce.domains.healthcare.models.patient import Patient
from datamimic_ce.domains.healthcare.services.doctor_service import DoctorService
from datamimic_ce.domains.healthcare.services.hospital_service import HospitalService
from datamimic_ce.domains.healthcare.services.patient_service import PatientService

__all__ = [
    # Models
    "Doctor",
    "Patient",
    "Hospital",
    # Data loaders
    "DoctorDataLoader",
    "PatientDataLoader",
    "HospitalDataLoader",
    # Services
    "DoctorService",
    "PatientService",
    "HospitalService",
]
