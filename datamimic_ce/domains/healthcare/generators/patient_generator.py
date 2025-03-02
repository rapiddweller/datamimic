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


def weighted_choice(items: list[str | tuple[str, float]]) -> str:
    """Choose an item from a list, with optional weights.

    Args:
        items: A list of items, where each item is either a string or a tuple of (string, weight).

    Returns:
        A randomly selected item.
    """
    if not items:
        return ""

    # Check if items have weights
    if isinstance(items[0], tuple) and len(items[0]) == 2:
        # Items are (value, weight) tuples
        values, weights = zip(*items, strict=False)
        return random.choices(values, weights=weights, k=1)[0]
    else:
        # Items are just values
        return random.choice(items)


def generate_age_appropriate_conditions(age: int) -> list[str]:
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


def generate_age_appropriate_medications(age: int, conditions: list[str]) -> list[str]:
    """Generate a list of medications appropriate for the given age and conditions.

    Args:
        age: The age of the patient.
        conditions: The patient's medical conditions.

    Returns:
        A list of medications.
    """
    # Define condition-specific medications
    condition_medications = {
        "Hypertension": ["Lisinopril", "Amlodipine", "Losartan", "Hydrochlorothiazide", "Metoprolol"],
        "Type 2 Diabetes": ["Metformin", "Glipizide", "Januvia", "Jardiance", "Ozempic"],
        "Type 1 Diabetes": ["Insulin (Lantus)", "Insulin (Humalog)", "Insulin (Novolog)"],
        "Asthma": ["Albuterol", "Fluticasone", "Montelukast", "Budesonide"],
        "COPD": ["Albuterol", "Tiotropium", "Fluticasone/Salmeterol", "Budesonide/Formoterol"],
        "Hyperlipidemia": ["Atorvastatin", "Simvastatin", "Rosuvastatin", "Pravastatin"],
        "Depression": ["Sertraline", "Fluoxetine", "Escitalopram", "Bupropion", "Venlafaxine"],
        "Anxiety": ["Sertraline", "Escitalopram", "Buspirone", "Lorazepam", "Alprazolam"],
        "GERD": ["Omeprazole", "Pantoprazole", "Famotidine", "Esomeprazole"],
        "Hypothyroidism": ["Levothyroxine"],
        "Osteoarthritis": ["Acetaminophen", "Ibuprofen", "Naproxen", "Celecoxib", "Tramadol"],
        "Osteoporosis": ["Alendronate", "Risedronate", "Denosumab", "Calcium/Vitamin D"],
        "Allergies": ["Cetirizine", "Loratadine", "Fexofenadine", "Fluticasone nasal spray"],
        "Migraine": ["Sumatriptan", "Rizatriptan", "Propranolol", "Topiramate", "Amitriptyline"],
        "Heart failure": ["Lisinopril", "Carvedilol", "Furosemide", "Spironolactone", "Sacubitril/Valsartan"],
        "Atrial fibrillation": ["Apixaban", "Rivaroxaban", "Warfarin", "Metoprolol", "Amiodarone"],
        "Coronary artery disease": ["Aspirin", "Atorvastatin", "Metoprolol", "Clopidogrel", "Isosorbide"],
        "Chronic kidney disease": ["Lisinopril", "Furosemide", "Sevelamer", "Calcitriol"],
        "ADHD": ["Methylphenidate", "Amphetamine/Dextroamphetamine", "Atomoxetine"],
        "Epilepsy": ["Levetiracetam", "Lamotrigine", "Valproic acid", "Carbamazepine"],
        "Obesity": ["Phentermine", "Orlistat", "Liraglutide", "Semaglutide"],
        "Sleep apnea": ["CPAP therapy"],
        "Alzheimer's disease": ["Donepezil", "Memantine", "Rivastigmine"],
        "Parkinson's disease": ["Carbidopa/Levodopa", "Pramipexole", "Ropinirole"],
    }

    # Common medications by age group
    child_medications = ["Amoxicillin", "Ibuprofen", "Acetaminophen", "Cetirizine", "Fluticasone nasal spray"]
    young_adult_medications = ["Ibuprofen", "Acetaminophen", "Cetirizine", "Loratadine", "Fluticasone nasal spray"]
    middle_age_medications = ["Ibuprofen", "Acetaminophen", "Omeprazole", "Atorvastatin", "Lisinopril"]
    elderly_medications = ["Acetaminophen", "Omeprazole", "Atorvastatin", "Lisinopril", "Amlodipine"]

    # Select medications based on conditions
    result = []
    for condition in conditions:
        if condition in condition_medications:
            medication = random.choice(condition_medications[condition])
            if medication not in result:
                result.append(medication)

    # Add some common medications based on age
    if age < 18:
        medication_pool = child_medications
    elif age < 40:
        medication_pool = young_adult_medications
    elif age < 65:
        medication_pool = middle_age_medications
    else:
        medication_pool = elderly_medications

    # Add 0-2 common medications
    num_common = random.randint(0, 2)
    for _ in range(num_common):
        medication = random.choice(medication_pool)
        if medication not in result:
            result.append(medication)

    return result


def generate_emergency_contact(patient_last_name: str, first_names: list[str], last_names: list[str]) -> dict[str, str]:
    """Generate emergency contact information.

    Args:
        patient_last_name: The patient's last name.
        first_names: A list of first names to choose from.
        last_names: A list of last names to choose from.

    Returns:
        A dictionary containing emergency contact information.
    """
    # Generate a name for the emergency contact
    first_name = random.choice(first_names)

    # 50% chance the emergency contact has the same last name
    if random.random() < 0.5:
        last_name = patient_last_name
    else:
        last_name = random.choice(last_names)

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

    # Generate a phone number
    area_code = random.randint(100, 999)
    prefix = random.randint(100, 999)
    line = random.randint(1000, 9999)
    phone = f"({area_code}) {prefix}-{line}"

    return {"name": f"{first_name} {last_name}", "relationship": relationship, "phone": phone}
