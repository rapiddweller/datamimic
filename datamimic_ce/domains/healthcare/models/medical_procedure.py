# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure entity model.

This module provides the MedicalProcedure entity model for generating realistic medical procedure data.
"""

from typing import Any, ClassVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.healthcare.data_loaders.medical_procedure_loader import MedicalProcedureLoader


class MedicalProcedure(BaseEntity):
    """Generate medical procedure data.

    This class generates realistic medical procedure data including procedure codes,
    names, descriptions, durations, costs, and associated medical specialties.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Class-level cache for shared data
    _DATA_CACHE: ClassVar[dict[str, Any]] = {}

    def __init__(
        self,
        class_factory_util: Any,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the MedicalProcedure entity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._dataset = dataset
        self._country_code = dataset or "US"

        # Initialize data loader
        self._data_loader = MedicalProcedureLoader()

        # Initialize field generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize all field generators."""
        # Basic information
        self._procedure_id_generator = PropertyCache(self._generate_procedure_id)
        self._procedure_code_generator = PropertyCache(self._generate_procedure_code)
        self._name_generator = PropertyCache(self._generate_name)
        self._description_generator = PropertyCache(self._generate_description)
        self._category_generator = PropertyCache(self._generate_category)
        self._specialty_generator = PropertyCache(self._generate_specialty)
        self._duration_minutes_generator = PropertyCache(self._generate_duration_minutes)
        self._cost_generator = PropertyCache(self._generate_cost)
        self._requires_anesthesia_generator = PropertyCache(self._generate_requires_anesthesia)
        self._is_surgical_generator = PropertyCache(self._generate_is_surgical)
        self._is_diagnostic_generator = PropertyCache(self._generate_is_diagnostic)
        self._is_preventive_generator = PropertyCache(self._generate_is_preventive)
        self._required_equipment_generator = PropertyCache(self._generate_required_equipment)
        self._recovery_time_days_generator = PropertyCache(self._generate_recovery_time_days)
        self._common_complications_generator = PropertyCache(self._generate_common_complications)
        self._cpt_code_generator = PropertyCache(self._generate_cpt_code)

    def reset(self) -> None:
        """Reset all field generators, causing new values to be generated on the next access."""
        self._procedure_id_generator.reset()
        self._procedure_code_generator.reset()
        self._name_generator.reset()
        self._description_generator.reset()
        self._category_generator.reset()
        self._specialty_generator.reset()
        self._duration_minutes_generator.reset()
        self._cost_generator.reset()
        self._requires_anesthesia_generator.reset()
        self._is_surgical_generator.reset()
        self._is_diagnostic_generator.reset()
        self._is_preventive_generator.reset()
        self._required_equipment_generator.reset()
        self._recovery_time_days_generator.reset()
        self._common_complications_generator.reset()
        self._cpt_code_generator.reset()

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
            "required_equipment": self.required_equipment,
            "recovery_time_days": self.recovery_time_days,
            "common_complications": self.common_complications,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of medical procedure entities.

        Args:
            count: The number of medical procedure entities to generate.

        Returns:
            A list of dictionaries containing the generated medical procedure entities.
        """
        procedures = []
        for _ in range(count):
            procedures.append(self.to_dict())
            self.reset()
        return procedures

    # Property getters
    @property
    def procedure_id(self) -> str:
        """Get the procedure ID.

        Returns:
            A unique identifier for the procedure.
        """
        return self._procedure_id_generator.get()

    @property
    def procedure_code(self) -> str:
        """Get the procedure code.

        Returns:
            A procedure code.
        """
        return self._procedure_code_generator.get()

    @property
    def cpt_code(self) -> str:
        """Get the CPT (Current Procedural Terminology) code.

        Returns:
            A CPT code.
        """
        return self._cpt_code_generator.get()

    @property
    def name(self) -> str:
        """Get the procedure name.

        Returns:
            The procedure name.
        """
        return self._name_generator.get()

    @property
    def description(self) -> str:
        """Get the procedure description.

        Returns:
            The procedure description.
        """
        return self._description_generator.get()

    @property
    def category(self) -> str:
        """Get the procedure category.

        Returns:
            The procedure category.
        """
        return self._category_generator.get()

    @property
    def specialty(self) -> str:
        """Get the medical specialty associated with the procedure.

        Returns:
            The medical specialty.
        """
        return self._specialty_generator.get()

    @property
    def duration_minutes(self) -> int:
        """Get the procedure duration in minutes.

        Returns:
            The procedure duration in minutes.
        """
        return self._duration_minutes_generator.get()

    @property
    def cost(self) -> float:
        """Get the procedure cost.

        Returns:
            The procedure cost.
        """
        return self._cost_generator.get()

    @property
    def requires_anesthesia(self) -> bool:
        """Get whether the procedure requires anesthesia.

        Returns:
            True if the procedure requires anesthesia, False otherwise.
        """
        return self._requires_anesthesia_generator.get()

    @property
    def is_surgical(self) -> bool:
        """Get whether the procedure is surgical.

        Returns:
            True if the procedure is surgical, False otherwise.
        """
        return self._is_surgical_generator.get()

    @property
    def is_diagnostic(self) -> bool:
        """Get whether the procedure is diagnostic.

        Returns:
            True if the procedure is diagnostic, False otherwise.
        """
        return self._is_diagnostic_generator.get()

    @property
    def is_preventive(self) -> bool:
        """Get whether the procedure is preventive.

        Returns:
            True if the procedure is preventive, False otherwise.
        """
        return self._is_preventive_generator.get()

    @property
    def required_equipment(self) -> list[str]:
        """Get the equipment required for the procedure.

        Returns:
            A list of required equipment.
        """
        return self._required_equipment_generator.get()

    @property
    def recovery_time_days(self) -> int:
        """Get the recovery time in days.

        Returns:
            The recovery time in days.
        """
        return self._recovery_time_days_generator.get()

    @property
    def common_complications(self) -> list[str]:
        """Get common complications associated with the procedure.

        Returns:
            A list of common complications.
        """
        return self._common_complications_generator.get()

    # Generator methods
    def _generate_procedure_id(self) -> str:
        """Generate a unique procedure ID.

        Returns:
            A unique procedure ID.
        """
        import uuid

        return f"PROC-{uuid.uuid4().hex[:8].upper()}"

    def _generate_procedure_code(self) -> str:
        """Generate a procedure code.

        Returns:
            A procedure code.
        """
        import random
        import string

        # Generate a procedure code with a format like "P12345"
        prefix = "P"
        number = "".join(random.choices(string.digits, k=5))

        return f"{prefix}{number}"

    def _generate_cpt_code(self) -> str:
        """Generate a CPT (Current Procedural Terminology) code.

        Returns:
            A CPT code.
        """
        import random

        # CPT codes are 5-digit numeric codes
        return f"{random.randint(10000, 99999)}"

    def _generate_name(self) -> str:
        """Generate a procedure name.

        Returns:
            A procedure name.
        """
        from datamimic_ce.domains.healthcare.generators.medical_procedure_generator import get_procedure_name

        category = self.category
        specialty = self.specialty
        is_surgical = self.is_surgical
        is_diagnostic = self.is_diagnostic

        return get_procedure_name(category, specialty, is_surgical, is_diagnostic)

    def _generate_description(self) -> str:
        """Generate a procedure description.

        Returns:
            A procedure description.
        """
        from datamimic_ce.domains.healthcare.generators.medical_procedure_generator import (
            generate_procedure_description,
        )

        name = self.name
        category = self.category
        is_surgical = self.is_surgical
        is_diagnostic = self.is_diagnostic
        is_preventive = self.is_preventive
        requires_anesthesia = self.requires_anesthesia

        return generate_procedure_description(
            name, category, is_surgical, is_diagnostic, is_preventive, requires_anesthesia
        )

    def _generate_category(self) -> str:
        """Generate a procedure category.

        Returns:
            A procedure category.
        """
        import random

        categories = self._data_loader.get_data("categories", self._country_code)
        return random.choice(categories)

    def _generate_specialty(self) -> str:
        """Generate a medical specialty.

        Returns:
            A medical specialty.
        """
        import random

        specialties = self._data_loader.get_data("specialties", self._country_code)
        return random.choice(specialties)

    def _generate_duration_minutes(self) -> int:
        """Generate a procedure duration in minutes.

        Returns:
            The procedure duration in minutes.
        """
        import random

        # Duration depends on whether the procedure is surgical
        if self.is_surgical:
            # Surgical procedures tend to be longer
            return random.randint(30, 240)  # 30 minutes to 4 hours
        else:
            # Non-surgical procedures tend to be shorter
            return random.randint(10, 120)  # 10 minutes to 2 hours

    def _generate_cost(self) -> float:
        """Generate a procedure cost.

        Returns:
            The procedure cost.
        """
        import random

        # Cost depends on various factors
        base_cost = 0

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

    def _generate_requires_anesthesia(self) -> bool:
        """Generate whether the procedure requires anesthesia.

        Returns:
            True if the procedure requires anesthesia, False otherwise.
        """
        import random

        # Surgical procedures usually require anesthesia
        if self.is_surgical:
            return random.random() < 0.9  # 90% chance
        else:
            return random.random() < 0.2  # 20% chance

    def _generate_is_surgical(self) -> bool:
        """Generate whether the procedure is surgical.

        Returns:
            True if the procedure is surgical, False otherwise.
        """
        import random

        # About 30% of procedures are surgical
        return random.random() < 0.3

    def _generate_is_diagnostic(self) -> bool:
        """Generate whether the procedure is diagnostic.

        Returns:
            True if the procedure is diagnostic, False otherwise.
        """
        import random

        # About 50% of procedures are diagnostic
        # Surgical procedures are less likely to be diagnostic
        if self.is_surgical:
            return random.random() < 0.2  # 20% chance
        else:
            return random.random() < 0.7  # 70% chance

    def _generate_is_preventive(self) -> bool:
        """Generate whether the procedure is preventive.

        Returns:
            True if the procedure is preventive, False otherwise.
        """
        import random

        # About 20% of procedures are preventive
        # Surgical procedures are less likely to be preventive
        if self.is_surgical:
            return random.random() < 0.05  # 5% chance
        else:
            return random.random() < 0.3  # 30% chance

    def _generate_required_equipment(self) -> list[str]:
        """Generate the equipment required for the procedure.

        Returns:
            A list of required equipment.
        """
        import random

        all_equipment = self._data_loader.get_data("equipment", self._country_code)

        # Determine how many pieces of equipment to include
        if self.is_surgical:
            # Surgical procedures require more equipment
            num_equipment = random.randint(3, 8)
        else:
            # Non-surgical procedures require less equipment
            num_equipment = random.randint(1, 4)

        # Select random equipment
        equipment = random.sample(all_equipment, min(num_equipment, len(all_equipment)))

        return equipment

    def _generate_recovery_time_days(self) -> int:
        """Generate the recovery time in days.

        Returns:
            The recovery time in days.
        """
        import random

        # Recovery time depends on whether the procedure is surgical
        if self.is_surgical:
            # Surgical procedures have longer recovery times
            return random.randint(1, 30)  # 1 day to 1 month
        else:
            # Non-surgical procedures have shorter recovery times
            return random.randint(0, 3)  # 0 to 3 days

    def _generate_common_complications(self) -> list[str]:
        """Generate common complications associated with the procedure.

        Returns:
            A list of common complications.
        """
        import random

        all_complications = self._data_loader.get_data("complications", self._country_code)

        # Determine how many complications to include
        if self.is_surgical:
            # Surgical procedures have more potential complications
            num_complications = random.randint(2, 5)
        else:
            # Non-surgical procedures have fewer potential complications
            num_complications = random.randint(0, 2)

        # Select random complications
        complications = random.sample(all_complications, min(num_complications, len(all_complications)))

        return complications
