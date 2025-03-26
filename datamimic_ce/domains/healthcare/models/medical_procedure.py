# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure entity model.

This module provides the MedicalProcedure entity model for generating realistic medical procedure data.
"""

import random
import string
import uuid
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.healthcare.generators.medical_procedure_generator import MedicalProcedureGenerator


class MedicalProcedure(BaseEntity):
    """Generate medical procedure data.

    This class generates realistic medical procedure data including procedure codes,
    names, descriptions, durations, costs, and associated medical specialties.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    def __init__(self, medical_procedure_generator: MedicalProcedureGenerator):
        """Initialize the MedicalProcedure entity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
        """
        super().__init__()
        self._medical_procedure_generator = medical_procedure_generator

    @property
    @property_cache
    def procedure_id(self) -> str:
        """Get the procedure ID.

        Returns:
            A unique identifier for the procedure.
        """
        return f"PROC-{uuid.uuid4().hex[:8].upper()}"

    @property
    @property_cache
    def procedure_code(self) -> str:
        """Get the procedure code.

        Returns:
            A procedure code.
        """
        # Generate a procedure code with a format like "P12345"
        prefix = "P"
        number = "".join(random.choices(string.digits, k=5))

        return f"{prefix}{number}"

    @property
    @property_cache
    def cpt_code(self) -> str:
        """Get the CPT (Current Procedural Terminology) code.

        Returns:
            A CPT code.
        """
        return f"{random.randint(10000, 99999)}"

    @property
    @property_cache
    def name(self) -> str:
        """Get the procedure name.

        Returns:
            The procedure name.
        """
        return self._medical_procedure_generator.get_procedure_name(
            self.category, self.specialty, self.is_surgical, self.is_diagnostic
        )

    @property
    @property_cache
    def category(self) -> str:
        """Get the procedure category.

        Returns:
            The procedure category.
        """
        return self._medical_procedure_generator.generate_category()

    @property
    @property_cache
    def description(self) -> str:
        """Get the procedure description.

        Returns:
            The procedure description.
        """
        return self._medical_procedure_generator.generate_procedure_description(
            self.name, self.category, self.is_surgical, self.is_diagnostic, self.is_preventive, self.requires_anesthesia
        )

    @property
    @property_cache
    def specialty(self) -> str:
        """Get the medical specialty associated with the procedure.

        Returns:
            The medical specialty.
        """
        return self._medical_procedure_generator.generate_specialty()

    @property
    @property_cache
    def duration_minutes(self) -> int:
        """Get the procedure duration in minutes.

        Returns:
            The procedure duration in minutes.
        """
        # Duration depends on whether the procedure is surgical
        if self.is_surgical:
            # Surgical procedures tend to be longer
            return random.randint(30, 240)  # 30 minutes to 4 hours
        else:
            # Non-surgical procedures tend to be shorter
            return random.randint(10, 120)  # 10 minutes to 2 hours

    @property
    @property_cache
    def cost(self) -> float:
        """Get the procedure cost.

        Returns:
            The procedure cost.
        """
        # Cost depends on various factors
        base_cost = 0.0

        # Surgical procedures are more expensive
        if self.is_surgical:
            base_cost += random.uniform(1000, 5000)
        else:
            base_cost += random.uniform(100, 1000)

        # Procedures requiring anesthesia are more expensive
        if self.requires_anesthesia:
            base_cost += random.uniform(500, 1500)

        # Longer procedures are more expensive
        duration_factor = self.duration_minutes / 60  # Convert to hours
        base_cost += duration_factor * random.uniform(200, 500)

        # Add some random variation
        variation = base_cost * 0.2  # 20% variation
        final_cost = base_cost + random.uniform(-variation, variation)

        return round(final_cost, 2)

    @property
    @property_cache
    def requires_anesthesia(self) -> bool:
        """Get whether the procedure requires anesthesia.

        Returns:
            True if the procedure requires anesthesia, False otherwise.
        """
        # Surgical procedures usually require anesthesia
        if self.is_surgical:
            return random.random() < 0.9  # 90% chance
        else:
            return random.random() < 0.2  # 20% chance

    @property
    @property_cache
    def is_surgical(self) -> bool:
        """Get whether the procedure is surgical.

        Returns:
            True if the procedure is surgical, False otherwise.
        """
        return random.random() < 0.3

    @property
    @property_cache
    def is_diagnostic(self) -> bool:
        """Get whether the procedure is diagnostic.

        Returns:
            True if the procedure is diagnostic, False otherwise.
        """
        # About 50% of procedures are diagnostic
        # Surgical procedures are less likely to be diagnostic
        if self.is_surgical:
            return random.random() < 0.2  # 20% chance
        else:
            return random.random() < 0.7  # 70% chance

    @property
    @property_cache
    def is_preventive(self) -> bool:
        """Get whether the procedure is preventive.

        Returns:
            True if the procedure is preventive, False otherwise.
        """
        # About 20% of procedures are preventive
        # Surgical procedures are less likely to be preventive
        if self.is_surgical:
            return random.random() < 0.05  # 5% chance
        else:
            return random.random() < 0.3  # 30% chance

    @property
    @property_cache
    def recovery_time_days(self) -> int:
        """Get the recovery time in days.

        Returns:
            The recovery time in days.
        """
        # Recovery time depends on whether the procedure is surgical
        if self.is_surgical:
            # Surgical procedures have longer recovery times
            return random.randint(1, 30)  # 1 day to 1 month
        else:
            # Non-surgical procedures have shorter recovery times
            return random.randint(0, 3)  # 0 to 3 days

    def to_dict(self) -> dict[str, Any]:
        """Convert the medical procedure entity to a dictionary.

        Returns:
            A dictionary containing all medical procedure properties.
        """
        return {
            "procedure_id": self.procedure_id,
            "procedure_code": self.procedure_code,
            "cpt_code": self.cpt_code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "specialty": self.specialty,
            "duration_minutes": self.duration_minutes,
            "cost": self.cost,
            "requires_anesthesia": self.requires_anesthesia,
            "is_surgical": self.is_surgical,
            "is_diagnostic": self.is_diagnostic,
            "is_preventive": self.is_preventive,
            "recovery_time_days": self.recovery_time_days,
        }
