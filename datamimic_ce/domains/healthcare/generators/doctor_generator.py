# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor generator utilities.

This module provides utility functions for generating doctor data.
"""

import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class DoctorGenerator(BaseDomainGenerator):
    """Generate doctor data."""

    def __init__(self, dataset: str | None = None):
        self._dataset = dataset or "US"
        self._person_generator = PersonGenerator(dataset=self._dataset, min_age=25)
        self._hospital_generator = HospitalGenerator(dataset=self._dataset)

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def hospital_generator(self) -> HospitalGenerator:
        return self._hospital_generator

    def generate_specialty(self) -> str:
        """Generate a medical specialty.

        Returns:
            A medical specialty.
        """
        try:
            file_path = (
                Path(__file__).parent.parent.parent.parent
                / "domain_data"
                / "healthcare"
                / "medical"
                / f"specialties_{self._dataset}.csv"
            )
            wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
            loaded_data = [item["specialty"] for item in loaded_data]
        except FileNotFoundError as e:
            logger.warning(f"Specialties file not found for dataset {self._dataset}. Using default specialties: {e}")
            default_data = [
                ("Cardiology", 1.0),
                ("Dermatology", 1.0),
                ("Emergency Medicine", 1.0),
                ("Family Medicine", 1.0),
                ("Gastroenterology", 1.0),
                ("Internal Medicine", 1.0),
                ("Neurology", 1.0),
                ("Obstetrics and Gynecology", 1.0),
                ("Oncology", 1.0),
                ("Ophthalmology", 1.0),
                ("Orthopedic Surgery", 1.0),
                ("Pediatrics", 1.0),
                ("Psychiatry", 1.0),
                ("Radiology", 1.0),
                ("Surgery", 1.0),
                ("Urology", 1.0),
            ]
            loaded_data, wgt = [], []
            for item in default_data:
                loaded_data.append(item[0])
                wgt.append(float(item[1]))

        return random.choices(loaded_data, weights=wgt)[0]

    def generate_medical_school(self) -> str:
        """Generate a medical school.

        Returns:
            A medical school.
        """
        # TODO: Add more medical schools
        all_medical_schools = [
            "Harvard Medical School",
            "Johns Hopkins School of Medicine",
            "Stanford University School of Medicine",
            "University of California, San Francisco",
            "Columbia University Vagelos College of Physicians and Surgeons",
            "Mayo Clinic Alix School of Medicine",
            "University of Pennsylvania Perelman School of Medicine",
            "Washington University School of Medicine",
            "Yale School of Medicine",
            "Duke University School of Medicine",
        ]
        return random.choice(all_medical_schools)

    def generate_certifications(self) -> list[str]:
        """Generate a list of certifications.

        Returns:
            A list of certifications.
        """
        try:
            file_path = (
                Path(__file__).parent.parent.parent.parent
                / "domain_data"
                / "healthcare"
                / "medical"
                / f"certifications_{self._dataset}.csv"
            )
            wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        except FileNotFoundError as e:
            logger.warning(
                f"Certifications file not found for dataset {self._dataset}. Using default certifications: {e}"
            )
            default_data = [
                ("Board Certified", 1.0),
                ("American Board of Medical Specialties", 1.0),
                ("Fellow of the American College of Physicians", 1.0),
                ("Fellow of the American College of Surgeons", 1.0),
                ("American Board of Internal Medicine", 1.0),
                ("American Board of Pediatrics", 1.0),
                ("American Board of Surgery", 1.0),
                ("American Board of Psychiatry and Neurology", 1.0),
                ("American Board of Radiology", 1.0),
                ("American Board of Family Medicine", 1.0),
            ]
            loaded_data, wgt = [], []
            for item in default_data:
                loaded_data.append(item[0])
                wgt.append(float(item[1]))
        return random.choices(loaded_data, weights=wgt, k=random.randint(1, 3))
