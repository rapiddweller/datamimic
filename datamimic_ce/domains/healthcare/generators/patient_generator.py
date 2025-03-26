# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient generator utilities.

This module provides utility functions for generating patient data.
"""

import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.utils.file_util import FileUtil


class PatientGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None):
        self._dataset = dataset or "US"
        self._person_generator = PersonGenerator(dataset=self._dataset)
        self._family_name_generator = FamilyNameGenerator(dataset=self._dataset)
        self._given_name_generator = GivenNameGenerator(dataset=self._dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=self._dataset)

    @property
    def person_generator(self) -> PersonGenerator:
        """Get the person generator.

        Returns:
            The person generator.
        """
        return self._person_generator

    def generate_age_appropriate_conditions(self, age: int) -> list[str]:
        """Generate a list of medical conditions appropriate for the given age.

        Args:
            age: The age of the patient.

        Returns:
            A list of medical conditions.
        """
        # Define age-appropriate conditions
        child_conditions = [
            "Asthma",
            "Allergies",
            "Eczema",
            "ADHD",
            "Autism spectrum disorder",
            "Congenital heart defects",
            "Type 1 diabetes",
            "Epilepsy",
            "Cerebral palsy",
        ]

        young_adult_conditions = [
            "Anxiety",
            "Depression",
            "Acne",
            "Migraine",
            "Irritable bowel syndrome",
            "Asthma",
            "Type 1 diabetes",
            "Allergies",
            "Obesity",
        ]

        middle_age_conditions = [
            "Hypertension",
            "Type 2 diabetes",
            "Hyperlipidemia",
            "Obesity",
            "Depression",
            "Anxiety",
            "GERD",
            "Migraine",
            "Sleep apnea",
            "Hypothyroidism",
        ]

        elderly_conditions = [
            "Hypertension",
            "Coronary artery disease",
            "Heart failure",
            "Type 2 diabetes",
            "Osteoarthritis",
            "Osteoporosis",
            "COPD",
            "Chronic kidney disease",
            "Alzheimer's disease",
            "Parkinson's disease",
            "Atrial fibrillation",
            "Cataracts",
            "Macular degeneration",
            "Hearing loss",
        ]

        # Select conditions based on age
        if age < 18:
            condition_pool = child_conditions
        elif age < 40:
            condition_pool = young_adult_conditions
        elif age < 65:
            condition_pool = middle_age_conditions
        else:
            condition_pool = elderly_conditions

        # Determine how many conditions to generate
        # Older people tend to have more conditions
        if age < 18:
            weights = [0.8, 0.15, 0.04, 0.01, 0.0]
        elif age < 40:
            weights = [0.6, 0.25, 0.1, 0.04, 0.01]
        elif age < 65:
            weights = [0.4, 0.3, 0.15, 0.1, 0.05]
        else:
            weights = [0.2, 0.3, 0.25, 0.15, 0.1]

        num_conditions = random.choices([0, 1, 2, 3, 4], weights=weights, k=1)[0]

        if num_conditions == 0:
            return []

        # Generate unique conditions
        result = []
        for _ in range(num_conditions):
            condition = random.choice(condition_pool)
            if condition not in result:
                result.append(condition)

        return result

    def generate_insurance_provider(self) -> str:
        """Generate a random insurance provider.

        Returns:
            A random insurance provider.
        """
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"insurance_providers_{self._dataset}.csv"
        )
        loaded_data = FileUtil.read_weight_csv(file_path)
        return random.choices(loaded_data[0], weights=loaded_data[1], k=1)[0]  # type: ignore

    def get_allergies(self) -> list[str]:
        # Determine how many allergies to generate (most people have 0-3)
        num_allergies = random.choices([0, 1, 2, 3, 4, 5], weights=[0.5, 0.2, 0.15, 0.1, 0.03, 0.02], k=1)[0]

        if num_allergies == 0:
            return []

        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"allergies_{self._dataset}.csv"
        )
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")

        random_choices = random.choices(loaded_data, weights=wgt, k=num_allergies)
        return [choice["allergen"] for choice in random_choices]

    def get_medications(self, age: int) -> list[str]:
        # Determine how many medications to generate
        # Older people tend to take more medications
        if age < 18:
            weights = [0.7, 0.2, 0.08, 0.02, 0.0, 0.0]
        elif age < 40:
            weights = [0.5, 0.3, 0.15, 0.04, 0.01, 0.0]
        elif age < 65:
            weights = [0.3, 0.3, 0.2, 0.1, 0.07, 0.03]
        else:
            weights = [0.1, 0.2, 0.3, 0.2, 0.15, 0.05]

        num_medications = random.choices([0, 1, 2, 3, 4, 5], weights=weights, k=1)[0]

        if num_medications == 0:
            return []

        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"medications_{self._dataset}.csv"
        )
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")

        random_choices = random.choices(loaded_data, weights=wgt, k=num_medications)
        return [choice["name"] for choice in random_choices]

    def get_emergency_contact(self, family_name: str) -> dict[str, str]:
        """Generate a random emergency contact.

        Returns:
            A dictionary containing emergency contact information.
        """
        # Generate a name for the emergency contact
        given_name = self._given_name_generator.generate()

        # 50% chance the emergency contact has the same family name
        family_name = self._family_name_generator.generate() if random.random() < 0.5 else family_name

        # Generate a relationship
        relationships = [
            "Spouse",
            "Parent",
            "Child",
            "Sibling",
            "Friend",
            "Grandparent",
            "Aunt",
            "Uncle",
            "Cousin",
            "Partner",
        ]
        relationship = random.choice(relationships)
        phone_number = self._phone_number_generator.generate()

        return {"name": f"{given_name} {family_name}", "relationship": relationship, "phone": phone_number}
