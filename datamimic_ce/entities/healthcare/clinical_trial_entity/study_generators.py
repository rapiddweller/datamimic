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
            # Fall through to the default phases

    # Default phases with weights
    default_phases = (
        ("Phase 1", 20),
        ("Phase 2", 30),
        ("Phase 3", 30),
        ("Phase 4", 10),
        ("Early Phase 1", 5),
        ("Not Applicable", 5),
    )
    return weighted_choice(default_phases)


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
            # Fall through to the default statuses

    # Default statuses with weights
    default_statuses = (
        ("Recruiting", 30),
        ("Active, not recruiting", 20),
        ("Completed", 25),
        ("Not yet recruiting", 10),
        ("Terminated", 5),
        ("Withdrawn", 3),
        ("Suspended", 2),
        ("Unknown status", 5),
    )
    return weighted_choice(default_statuses)


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
            # Fall through to the default sponsors

    # Default sponsors with weights
    default_sponsors = (
        ("National Institutes of Health", 15),
        ("Pfizer", 10),
        ("Novartis", 10),
        ("Merck", 10),
        ("GlaxoSmithKline", 10),
        ("AstraZeneca", 10),
        ("Roche", 10),
        ("Johnson & Johnson", 10),
        ("Sanofi", 10),
        ("Eli Lilly and Company", 5),
    )
    return weighted_choice(default_sponsors)


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
            # Fall through to the default conditions

    # Default conditions with weights
    default_conditions = (
        ("Diabetes", 10),
        ("Hypertension", 10),
        ("Cancer", 10),
        ("Alzheimer's Disease", 5),
        ("Parkinson's Disease", 5),
        ("Multiple Sclerosis", 5),
        ("Rheumatoid Arthritis", 5),
        ("Asthma", 5),
        ("COPD", 5),
        ("Depression", 5),
        ("Anxiety", 5),
        ("Schizophrenia", 5),
        ("Bipolar Disorder", 5),
        ("HIV/AIDS", 5),
        ("Hepatitis", 5),
        ("Tuberculosis", 5),
        ("Malaria", 5),
    )
    return weighted_choice(default_conditions)


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
            # Fall through to the default intervention types

    # Default intervention types with weights
    default_intervention_types = (
        ("Drug", 40),
        ("Device", 15),
        ("Biological", 10),
        ("Procedure", 10),
        ("Radiation", 5),
        ("Behavioral", 10),
        ("Genetic", 5),
        ("Dietary Supplement", 5),
    )
    return weighted_choice(default_intervention_types)


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
        prefixes = [
            "Ab", "Ac", "Ad", "Al", "Am", "An", "Ar", "As", "At", "Ax", "Az", 
            "Bi", "Bo", "Bu", "Ca", "Ce", "Ci", "Co", "Cr", "Cu", "Cy", 
            "Da", "De", "Di", "Do", "Dr", "Du", "Ec", "Ed", "Ef", "El", 
            "Em", "En", "Ep", "Er", "Es", "Et", "Ev", "Ex", "Fa", "Fe", 
            "Fi", "Fl", "Fo", "Fu", "Ga", "Ge", "Gi", "Gl", "Go", "Gr", 
            "Gu", "Ha", "He", "Hi", "Ho", "Hu", "Hy", "Ib", "Ic", "Id", 
            "Il", "Im", "In", "Io", "Ip", "Ir", "Is", "It", "Iv", "Ja", 
            "Je", "Ji", "Jo", "Ju", "Ka", "Ke", "Ki", "Kl", "Ko", "Kr", 
            "Ku", "La", "Le", "Li", "Lo", "Lu", "Ly", "Ma", "Me", "Mi", 
            "Mo", "Mu", "My", "Na", "Ne", "Ni", "No", "Nu", "Ny", "Ob", 
            "Oc", "Od", "Of", "Ol", "Om", "On", "Op", "Or", "Os", "Ov", 
            "Ox", "Pa", "Pe", "Ph", "Pi", "Pl", "Po", "Pr", "Ps", "Pu", 
            "Qu", "Ra", "Re", "Rh", "Ri", "Ro", "Ru", "Sa", "Sc", "Se", 
            "Sh", "Si", "Sl", "So", "Sp", "St", "Su", "Sy", "Ta", "Te", 
            "Th", "Ti", "To", "Tr", "Tu", "Ty", "Ul", "Um", "Un", "Up", 
            "Ur", "Us", "Ut", "Va", "Ve", "Vi", "Vo", "Vu", "Wa", "We", 
            "Wi", "Wo", "Xa", "Xe", "Xi", "Xy", "Ya", "Ye", "Yi", "Yo", 
            "Yu", "Za", "Ze", "Zi", "Zo", "Zu"
        ]
        suffixes = [
            "bam", "ban", "bar", "ben", "bin", "bon", "cam", "can", "car", 
            "cen", "cin", "cir", "com", "con", "cor", "dam", "dan", "dar", 
            "den", "din", "dir", "dom", "don", "dor", "fam", "fan", "far", 
            "fen", "fin", "fir", "gam", "gan", "gar", "gen", "gin", "gir", 
            "ham", "han", "har", "hen", "hin", "hir", "jam", "jan", "jar", 
            "jen", "jin", "jir", "kam", "kan", "kar", "ken", "kin", "kir", 
            "lam", "lan", "lar", "len", "lin", "lir", "mab", "mac", "man", 
            "mar", "men", "min", "mir", "nam", "nan", "nar", "nem", "nin", 
            "nir", "pam", "pan", "par", "pen", "pin", "pir", "ram", "ran", 
            "rar", "rem", "rin", "rir", "sam", "san", "sar", "sem", "sin", 
            "sir", "tam", "tan", "tar", "tem", "tin", "tir", "vam", "van", 
            "var", "ven", "vin", "vir", "xam", "xan", "xar", "xen", "xin", 
            "xir", "zam", "zan", "zar", "zen", "zin", "zir"
        ]

        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix}{suffix}"

    elif intervention_type.lower() == "behavioral":
        # Generate a behavioral intervention name
        adjectives = [
            "Cognitive", "Behavioral", "Mindfulness", "Stress", "Relaxation", 
            "Coping", "Emotional", "Social", "Physical", "Dietary"
        ]
        nouns = [
            "Therapy", "Intervention", "Training", "Education", "Counseling", 
            "Management", "Modification", "Support", "Program", "Treatment"
        ]

        adjective = random.choice(adjectives)
        noun = random.choice(nouns)

        return f"{adjective} {noun} for {condition}"

    elif intervention_type.lower() == "device":
        # Generate a device name
        prefixes = ["Med", "Bio", "Tech", "Health", "Care", "Life", "Smart", "Vital", "Neuro", "Cardio"]
        suffixes = [
            "Scan", "Monitor", "Device", "System", "Tracker", "Sensor", 
            "Meter", "Tester", "Analyzer", "Assistant"
        ]

        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix}{suffix}"

    elif intervention_type.lower() == "procedure":
        # Generate a procedure name
        adjectives = [
            "Minimally Invasive", "Robotic", "Laparoscopic", "Endoscopic", 
            "Percutaneous", "Transcatheter", "Image-Guided", "Ultrasound-Guided", 
            "Laser-Assisted", "Computer-Assisted"
        ]
        nouns = [
            "Surgery", "Procedure", "Intervention", "Technique", "Approach", 
            "Method", "Treatment", "Therapy", "Operation", "Resection"
        ]

        adjective = random.choice(adjectives)
        noun = random.choice(nouns)

        return f"{adjective} {noun} for {condition}"

    elif intervention_type.lower() == "diagnostic test":
        # Generate a diagnostic test name
        prefixes = [
            "Rapid", "Advanced", "Comprehensive", "Precision", "Next-Generation", 
            "High-Sensitivity", "Automated", "Digital", "Molecular", "Genetic"
        ]
        nouns = [
            "Test", "Assay", "Panel", "Screen", "Scan", "Analysis", "Assessment", 
            "Evaluation", "Examination", "Diagnostic"
        ]

        prefix = random.choice(prefixes)
        noun = random.choice(nouns)

        return f"{prefix} {noun} for {condition}"

    elif intervention_type.lower() == "biological":
        # Generate a biological intervention name
        prefixes = ["Mono", "Poly", "Multi", "Omni", "Uni", "Bi", "Tri", "Quad", "Penta", "Hexa"]
        roots = [
            "clonal", "valent", "specific", "genic", "cellular", "molecular", 
            "peptide", "protein", "antibody", "immune"
        ]

        prefix = random.choice(prefixes)
        root = random.choice(roots)

        return f"{prefix}{root} Therapy"

    elif intervention_type.lower() == "dietary supplement":
        # Generate a dietary supplement name
        prefixes = ["Vita", "Nutri", "Opti", "Mega", "Ultra", "Super", "Pro", "Bio", "Eco", "Natur"]
        suffixes = ["min", "max", "plus", "complex", "blend", "formula", "boost", "support", "health", "life"]

        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix}{suffix}"

    else:
        # Generic intervention name
        return f"Intervention for {condition}"


def generate_study_design() -> dict[str, str]:
    """Generate a study design for a clinical trial.

    Returns:
        A dictionary containing study design details
    """
    # Define possible values for each aspect of the study design
    allocation_options = ["Randomized", "Non-Randomized", "N/A"]
    intervention_model_options = [
        "Parallel Assignment", "Crossover Assignment", "Factorial Assignment", 
        "Sequential Assignment", "Single Group Assignment"
    ]
    primary_purpose_options = [
        "Treatment", "Prevention", "Diagnostic", "Supportive Care", "Screening", 
        "Health Services Research", "Basic Science", "Device Feasibility"
    ]
    masking_options = ["None (Open Label)", "Single", "Double", "Triple", "Quadruple"]

    # Choose random values for each aspect
    allocation = random.choice(allocation_options)
    intervention_model = random.choice(intervention_model_options)
    primary_purpose = random.choice(primary_purpose_options)
    masking = random.choice(masking_options)

    # Return the study design as a dictionary
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
    # Define possible study types with weights
    study_types = (
        ("Interventional", 70),
        ("Observational", 25),
        ("Expanded Access", 5),
    )
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
    # Define possible title templates
    templates = [
        f"A {phase} Study of {intervention_name} for {condition}",
        f"{phase} Clinical Trial of {intervention_name} in Patients With {condition}",
        f"Efficacy and Safety of {intervention_name} in {condition}: A {phase} Study",
        f"{intervention_name} for the Treatment of {condition}: A {phase} Clinical Trial",
        f"A {phase}, Randomized Study of {intervention_name} in {condition}",
    ]

    # Choose a random template
    return random.choice(templates)


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
    # Define possible summary templates
    templates = [
        f"This {phase} clinical trial aims to evaluate the safety and efficacy of {intervention_name} "
        f"for the treatment of {condition}. The study will assess clinical outcomes and adverse events "
        f"in patients receiving the intervention.",
        
        f"The purpose of this {phase} study is to determine if {intervention_name} is effective in treating "
        f"{condition}. The trial will evaluate the safety profile and therapeutic benefits of the intervention "
        f"in eligible participants.",
        
        f"This research study is designed to test the effectiveness of {intervention_name} in patients with "
        f"{condition}. As a {phase} trial, it will focus on {get_phase_focus(phase)} in a controlled clinical setting.",
        
        f"A {phase} clinical investigation of {intervention_name} for patients diagnosed with {condition}. "
        f"The study aims to assess {get_phase_focus(phase)} through a structured protocol with appropriate endpoints.",
        
        f"This clinical trial will investigate the use of {intervention_name} as a potential treatment for "
        f"{condition}. The {phase} study will evaluate {get_phase_focus(phase)} according to established "
        f"clinical guidelines.",
    ]

    # Choose a random template
    return random.choice(templates)


def get_phase_focus(phase: str) -> str:
    """Get the focus of a clinical trial based on its phase.

    Args:
        phase: The phase of the trial

    Returns:
        A string describing the focus of the phase
    """
    if phase == "Phase 1" or phase == "Early Phase 1":
        return "safety, tolerability, and pharmacokinetics"
    elif phase == "Phase 2":
        return "efficacy and side effects"
    elif phase == "Phase 3":
        return "efficacy in a larger population and monitoring of adverse reactions"
    elif phase == "Phase 4":
        return "long-term safety and effectiveness in the general population"
    else:
        return "clinical outcomes and safety"
