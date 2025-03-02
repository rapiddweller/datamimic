# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Study generators for the Clinical Trial Entity.

This module provides functions for generating study-related data for clinical trials.
"""

import random
import string

from datamimic_ce.entities.healthcare.clinical_trial_entity.data_loader import ClinicalTrialDataLoader
from datamimic_ce.entities.healthcare.clinical_trial_entity.utils import weighted_choice
from datamimic_ce.logger import logger


def generate_phase(data_loader: ClinicalTrialDataLoader | None = None, country_code: str = "US") -> str:
    """Generate a phase for a clinical trial.

    Args:
        data_loader: Optional data loader to use for retrieving phases
        country_code: Country code (default: "US")

    Returns:
        A string representing the phase
    """
    # Try to use the data loader if provided
    if data_loader:
        try:
            phases = data_loader.get_country_specific_data("phases", country_code)
            if phases:
                return weighted_choice(phases)
        except Exception as e:
            logger.warning(f"Failed to use data loader for phases: {e}")

    # Log error if no data is available
    logger.error(f"No phases found for {country_code}. Please create a data file.")
    # Return a safe default
    return "Phase 2"


def generate_status(data_loader: ClinicalTrialDataLoader | None = None, country_code: str = "US") -> str:
    """Generate a status for a clinical trial.

    Args:
        data_loader: Optional data loader to use for retrieving statuses
        country_code: Country code (default: "US")

    Returns:
        A string representing the status
    """
    # Try to use the data loader if provided
    if data_loader:
        try:
            statuses = data_loader.get_country_specific_data("statuses", country_code)
            if statuses:
                return weighted_choice(statuses)
        except Exception as e:
            logger.warning(f"Failed to use data loader for statuses: {e}")

    # Log error if no data is available
    logger.error(f"No statuses found for {country_code}. Please create a data file.")
    # Return a safe default
    return "Recruiting"


def generate_sponsor(data_loader: ClinicalTrialDataLoader | None = None, country_code: str = "US") -> str:
    """Generate a sponsor for a clinical trial.

    Args:
        data_loader: Optional data loader to use for retrieving sponsors
        country_code: Country code (default: "US")

    Returns:
        A string representing the sponsor
    """
    # Try to use the data loader if provided
    if data_loader:
        try:
            sponsors = data_loader.get_country_specific_data("sponsors", country_code)
            if sponsors:
                return weighted_choice(sponsors)
        except Exception as e:
            logger.warning(f"Failed to use data loader for sponsors: {e}")

    # Log error if no data is available
    logger.error(f"No sponsors found for {country_code}. Please create a data file.")
    # Return a safe default
    return "Unknown Sponsor"


def generate_condition(data_loader: ClinicalTrialDataLoader | None = None, country_code: str = "US") -> str:
    """Generate a medical condition for a clinical trial.

    Args:
        data_loader: Optional data loader to use for retrieving conditions
        country_code: Country code (default: "US")

    Returns:
        A string representing the medical condition
    """
    # Try to use the data loader if provided
    if data_loader:
        try:
            conditions = data_loader.get_country_specific_data("medical_conditions", country_code)
            if conditions:
                return weighted_choice(conditions)
        except Exception as e:
            logger.warning(f"Failed to use data loader for conditions: {e}")

    # Log error if no data is available
    logger.error(f"No medical conditions found for {country_code}. Please create a data file.")
    # Return a safe default
    return "Unspecified Condition"


def generate_intervention_type(data_loader: ClinicalTrialDataLoader | None = None, country_code: str = "US") -> str:
    """Generate an intervention type for a clinical trial.

    Args:
        data_loader: Optional data loader to use for retrieving intervention types
        country_code: Country code (default: "US")

    Returns:
        A string representing the intervention type
    """
    # Try to use the data loader if provided
    if data_loader:
        try:
            intervention_types = data_loader.get_country_specific_data("intervention_types", country_code)
            if intervention_types:
                return weighted_choice(intervention_types)
        except Exception as e:
            logger.warning(f"Failed to use data loader for intervention types: {e}")

    # Log error if no data is available
    logger.error(f"No intervention types found for {country_code}. Please create a data file.")
    # Return a safe default
    return "Drug"


def generate_intervention_name(intervention_type: str, condition: str) -> str:
    """Generate an intervention name based on the intervention type and condition.

    Args:
        intervention_type: The type of intervention
        condition: The medical condition being studied

    Returns:
        A string representing the intervention name
    """
    # Generate a name based on the intervention type
    if intervention_type.lower() == "drug":
        # Generate a drug name
        return generate_drug_name(condition)
    elif intervention_type.lower() == "device":
        # Generate a device name
        return generate_device_name(condition)
    elif intervention_type.lower() == "behavioral":
        # Generate a behavioral intervention name
        return generate_behavioral_name(condition)
    else:
        # Generate a generic intervention name
        return f"{condition.title()} {intervention_type} Therapy"


def generate_drug_name(condition: str) -> str:
    """Generate a realistic drug name.

    Args:
        condition: The medical condition being treated

    Returns:
        A string representing the drug name
    """
    # Generate a drug name with common prefixes and suffixes
    prefixes = [
        "Ab",
        "Ac",
        "Ad",
        "Al",
        "Am",
        "An",
        "Ar",
        "Az",
        "Bi",
        "Ca",
        "Ce",
        "Ci",
        "Co",
        "Cy",
        "Da",
        "De",
        "Di",
        "Do",
        "Du",
        "El",
        "En",
        "Ep",
        "Eq",
        "Es",
        "Ev",
        "Ex",
        "Fe",
        "Fi",
        "Fl",
        "Fo",
        "Ga",
        "Ge",
        "Gl",
        "Ha",
        "He",
        "Hy",
        "Im",
        "In",
        "Ir",
        "Ja",
        "Ju",
        "Ka",
        "Ke",
        "Ki",
        "La",
        "Le",
        "Li",
        "Lo",
        "Lu",
        "Ly",
        "Ma",
        "Me",
        "Mi",
        "Mo",
        "My",
        "Na",
        "Ne",
        "No",
        "Nu",
        "Ny",
        "Ob",
        "Oc",
        "Od",
        "Of",
        "Ol",
        "Om",
        "On",
        "Op",
        "Or",
        "Os",
        "Ov",
        "Ox",
        "Pa",
        "Pe",
        "Ph",
        "Pi",
        "Pl",
        "Po",
        "Pr",
        "Ps",
        "Qu",
        "Ra",
        "Re",
        "Rh",
        "Ri",
        "Ro",
        "Ru",
        "Sa",
        "Sc",
        "Se",
        "Si",
        "So",
        "Sp",
        "St",
        "Su",
        "Sy",
        "Ta",
        "Te",
        "Th",
        "Ti",
        "To",
        "Tr",
        "Tu",
        "Ty",
        "Un",
        "Up",
        "Ur",
        "Va",
        "Ve",
        "Vi",
        "Vo",
        "Wa",
        "We",
        "Xa",
        "Xe",
        "Xi",
        "Xy",
        "Ya",
        "Ye",
        "Yo",
        "Za",
        "Ze",
        "Zi",
        "Zo",
        "Zu",
    ]

    suffixes = [
        "ban",
        "bax",
        "cef",
        "cin",
        "dex",
        "dine",
        "dol",
        "dryl",
        "fen",
        "formin",
        "glip",
        "kine",
        "lol",
        "mab",
        "micin",
        "mide",
        "mine",
        "mune",
        "mycin",
        "nac",
        "nal",
        "nex",
        "nide",
        "nine",
        "nium",
        "nix",
        "nol",
        "pam",
        "parin",
        "phil",
        "phos",
        "pril",
        "profen",
        "relin",
        "ride",
        "rine",
        "sartan",
        "semide",
        "sin",
        "statin",
        "sulfa",
        "tant",
        "taxel",
        "tidine",
        "tocin",
        "toin",
        "trel",
        "tropin",
        "vastatin",
        "vir",
        "vudine",
        "xacin",
        "xamine",
        "xane",
        "xetine",
        "xicam",
        "xifene",
        "xime",
        "xine",
        "xolol",
        "zepam",
        "zide",
        "zine",
        "zole",
        "zolid",
        "zone",
        "zosin",
    ]

    # Generate a random drug name
    prefix = random.choice(prefixes)
    suffix = random.choice(suffixes)

    # Add a middle part based on the condition (take first 3 letters)
    if condition and len(condition) >= 3:
        middle = condition[:3].lower()
    else:
        # Random 2-3 letter middle if no condition or condition is too short
        middle = "".join(random.choices(string.ascii_lowercase, k=random.randint(2, 3)))

    return f"{prefix}{middle}{suffix}"


def generate_device_name(condition: str) -> str:
    """Generate a realistic medical device name.

    Args:
        condition: The medical condition being treated

    Returns:
        A string representing the device name
    """
    # Generate a device name
    prefixes = [
        "Accu",
        "Adva",
        "Aero",
        "Bio",
        "Cardio",
        "Cere",
        "Cryo",
        "Derm",
        "Dia",
        "Digi",
        "Endo",
        "Ergo",
        "Flex",
        "Gastro",
        "Geno",
        "Gyro",
        "Hemo",
        "Hydro",
        "Immuno",
        "Infra",
        "Inno",
        "Kine",
        "Lase",
        "Lumi",
        "Magna",
        "Medi",
        "Micro",
        "Multi",
        "Nano",
        "Neuro",
        "Omni",
        "Opti",
        "Ortho",
        "Oxy",
        "Pedi",
        "Phono",
        "Physio",
        "Pneumo",
        "Poly",
        "Pulmo",
        "Quant",
        "Radio",
        "Regen",
        "Rheo",
        "Sono",
        "Spec",
        "Stim",
        "Surg",
        "Techno",
        "Thermo",
        "Trans",
        "Ultra",
        "Uni",
        "Vaso",
        "Venti",
        "Vibra",
        "Vita",
        "Volu",
        "Wave",
        "Xeno",
        "Zeno",
    ]

    suffixes = [
        "Aide",
        "Assist",
        "Care",
        "Cath",
        "Corder",
        "Core",
        "Derm",
        "Device",
        "Dial",
        "Doc",
        "Dyne",
        "Flex",
        "Flow",
        "Form",
        "Fusion",
        "Gen",
        "Graph",
        "Guard",
        "Guide",
        "Jet",
        "Lens",
        "Life",
        "Line",
        "Link",
        "Lith",
        "Logic",
        "Lux",
        "Lyte",
        "Mate",
        "Matrix",
        "Max",
        "Meter",
        "Monitor",
        "Net",
        "Pace",
        "Path",
        "Probe",
        "Pulse",
        "Pump",
        "Scan",
        "Scope",
        "Screen",
        "Sense",
        "Sentry",
        "Stent",
        "Stim",
        "Support",
        "Sure",
        "System",
        "Tech",
        "Tek",
        "Therm",
        "Tone",
        "Track",
        "Trak",
        "Tron",
        "Valve",
        "Vent",
        "View",
        "Vision",
        "Wave",
        "Wire",
        "X",
        "Zen",
    ]

    # Generate a random device name
    prefix = random.choice(prefixes)
    suffix = random.choice(suffixes)

    # Add a condition-specific part if available
    if condition:
        # Take first 4 letters of condition and capitalize
        condition_part = condition[:4].title()
        return f"{prefix}{condition_part}{suffix}"
    else:
        return f"{prefix}{suffix}"


def generate_behavioral_name(condition: str) -> str:
    """Generate a realistic behavioral intervention name.

    Args:
        condition: The medical condition being treated

    Returns:
        A string representing the behavioral intervention name
    """
    # Generate a behavioral intervention name
    prefixes = [
        "Adaptive",
        "Advanced",
        "Behavioral",
        "Cognitive",
        "Comprehensive",
        "Enhanced",
        "Focused",
        "Guided",
        "Holistic",
        "Integrated",
        "Intensive",
        "Interactive",
        "Mindful",
        "Motivational",
        "Personalized",
        "Positive",
        "Progressive",
        "Psychosocial",
        "Structured",
        "Supportive",
        "Systematic",
        "Therapeutic",
    ]

    middle_terms = [
        "Acceptance",
        "Activation",
        "Adaptation",
        "Adherence",
        "Adjustment",
        "Awareness",
        "Coping",
        "Counseling",
        "Education",
        "Engagement",
        "Enhancement",
        "Exposure",
        "Lifestyle",
        "Management",
        "Modification",
        "Processing",
        "Reduction",
        "Regulation",
        "Rehabilitation",
        "Relaxation",
        "Restructuring",
        "Skills",
        "Support",
        "Therapy",
        "Training",
    ]

    # Generate a random behavioral intervention name
    prefix = random.choice(prefixes)
    middle = random.choice(middle_terms)

    # Add condition-specific part
    if condition:
        return f"{prefix} {middle} for {condition}"
    else:
        return f"{prefix} {middle} Intervention"


def generate_study_design() -> dict[str, str]:
    """Generate a study design for a clinical trial.

    Returns:
        A dictionary containing study design elements
    """
    # Study design elements
    allocation = random.choice(["Randomized", "Non-Randomized", "N/A"])
    intervention_model = random.choice(
        [
            "Parallel Assignment",
            "Crossover Assignment",
            "Factorial Assignment",
            "Sequential Assignment",
            "Single Group Assignment",
        ]
    )
    primary_purpose = random.choice(
        [
            "Treatment",
            "Prevention",
            "Diagnostic",
            "Supportive Care",
            "Screening",
            "Health Services Research",
            "Basic Science",
            "Device Feasibility",
        ]
    )
    masking = random.choice(["None (Open Label)", "Single", "Double", "Triple", "Quadruple"])

    return {
        "allocation": allocation,
        "intervention_model": intervention_model,
        "primary_purpose": primary_purpose,
        "masking": masking,
    }


def generate_study_type() -> str:
    """Generate a study type for a clinical trial.

    Returns:
        A string representing the study type
    """
    # Study types with weights
    study_types = [
        ("Interventional", 70),
        ("Observational", 25),
        ("Expanded Access", 5),
    ]
    return weighted_choice(study_types)


def generate_title(condition: str, intervention_type: str, intervention_name: str, phase: str) -> str:
    """Generate a title for a clinical trial.

    Args:
        condition: The medical condition being studied
        intervention_type: The type of intervention
        intervention_name: The name of the intervention
        phase: The phase of the trial

    Returns:
        A string representing the title
    """
    # Title templates
    templates = [
        "A {phase} Study of {intervention_name} for the Treatment of {condition}",
        "Efficacy and Safety of {intervention_name} in Patients With {condition}: A {phase} Trial",
        "{phase} Clinical Trial of {intervention_name} in {condition}",
        "{intervention_name} for {condition}: A {phase}, Randomized Controlled Trial",
        "Evaluation of {intervention_name} in the Management of {condition} ({phase})",
        "A {phase} Study to Evaluate {intervention_name} in Subjects With {condition}",
        "{phase} Assessment of {intervention_name} for {condition} Treatment",
        "Safety and Efficacy of {intervention_name} in {condition}: A {phase} Study",
        "{intervention_type} Intervention With {intervention_name} for {condition}: {phase} Trial",
        "A Randomized {phase} Trial of {intervention_name} Versus Standard of Care for {condition}",
    ]

    # Choose a random template
    template = random.choice(templates)

    # Format the template
    title = template.format(
        phase=phase,
        intervention_type=intervention_type,
        intervention_name=intervention_name,
        condition=condition,
    )

    return title


def generate_brief_summary(condition: str, intervention_type: str, intervention_name: str, phase: str) -> str:
    """Generate a brief summary for a clinical trial.

    Args:
        condition: The medical condition being studied
        intervention_type: The type of intervention
        intervention_name: The name of the intervention
        phase: The phase of the trial

    Returns:
        A string representing the brief summary
    """
    # Summary templates
    templates = [
        "This {phase} clinical trial aims to evaluate the safety and efficacy of {intervention_name} "
        "for the treatment of {condition}. The study will assess clinical outcomes, adverse events, "
        "and patient-reported measures to determine the potential benefits of this {intervention_type} intervention.",
        "A {phase} study investigating {intervention_name}, a novel {intervention_type} for {condition}. "
        "The trial will evaluate whether {intervention_name} improves symptoms and quality of life "
        "compared to standard treatment approaches.",
        "This research study is designed to test the effectiveness of {intervention_name} in treating "
        "{condition}. As a {phase} trial, it will focus on {focus_area} in patients receiving this "
        "{intervention_type} intervention.",
        "The purpose of this {phase} clinical trial is to determine if {intervention_name} is safe and "
        "effective for individuals with {condition}. The study will involve multiple assessments to "
        "evaluate the {intervention_type}'s impact on disease progression and symptom management.",
        "A {phase}, randomized controlled trial evaluating {intervention_name} for {condition}. "
        "This study aims to assess whether this {intervention_type} intervention can provide meaningful "
        "clinical benefits with an acceptable safety profile.",
    ]

    # Choose a random template
    template = random.choice(templates)

    # Determine focus area based on phase
    if phase == "Phase 1" or phase == "Early Phase 1":
        focus_area = "safety and dosing"
    elif phase == "Phase 2":
        focus_area = "preliminary efficacy and side effects"
    elif phase == "Phase 3":
        focus_area = "confirming effectiveness and monitoring adverse reactions"
    elif phase == "Phase 4":
        focus_area = "long-term safety and additional uses"
    else:
        focus_area = "safety and effectiveness"

    # Format the template
    summary = template.format(
        phase=phase,
        intervention_type=intervention_type.lower(),
        intervention_name=intervention_name,
        condition=condition,
        focus_area=focus_area,
    )

    return summary
