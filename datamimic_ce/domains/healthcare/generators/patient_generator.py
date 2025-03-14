# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
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
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class PatientGenerator(BaseDomainGenerator):
    def __init__(self):
        self._person_generator = PersonGenerator()

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
        file_path = Path(__file__).parent.parent.parent.parent / "data" / "insurance_providers.json"
        loaded_data = FileContentStorage.load_file_with_custom_function(
            str(file_path),
            lambda: FileUtil.read_weight_csv(str(file_path))
        )
        return random.choices(loaded_data["insurance_providers"])