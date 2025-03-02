# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure generator utilities.

This module provides utility functions for generating medical procedure data.
"""

import random


def get_procedure_name(category: str, specialty: str, is_surgical: bool, is_diagnostic: bool) -> str:
    """Generate a procedure name based on category, specialty, and type.

    Args:
        category: The procedure category.
        specialty: The medical specialty.
        is_surgical: Whether the procedure is surgical.
        is_diagnostic: Whether the procedure is diagnostic.

    Returns:
        A procedure name.
    """
    # Define procedure name patterns by category
    category_patterns = {
        "Cardiovascular": [
            "{action} {location} {structure}",
            "{action} of {structure}",
            "{location} {structure} {action}",
        ],
        "Digestive": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Endocrine": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{structure} {action}",
        ],
        "Eye": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Female Genital": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Hemic and Lymphatic": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Integumentary": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Male Genital": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Maternity Care and Delivery": [
            "{action} {location} {structure}",
            "{action} {structure}",
            "{location} {action}",
        ],
        "Musculoskeletal": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Nervous": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Respiratory": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Urinary": [
            "{action} of {location} {structure}",
            "{location} {structure} {action}",
            "{action} {structure}",
        ],
        "Radiology": [
            "{location} {structure} {action}",
            "{action} of {location} {structure}",
            "{action} {structure}",
        ],
        "Pathology and Laboratory": [
            "{action} of {structure}",
            "{structure} {action}",
            "{action} {location} {structure}",
        ],
        "Medicine": [
            "{action} {structure}",
            "{action} of {location} {structure}",
            "{location} {action}",
        ],
        "Evaluation and Management": [
            "{action} {structure}",
            "{action} of {location}",
            "{location} {action}",
        ],
    }

    # Define actions by procedure type
    surgical_actions = [
        "Excision",
        "Resection",
        "Repair",
        "Reconstruction",
        "Transplantation",
        "Implantation",
        "Removal",
        "Replacement",
        "Revision",
        "Fusion",
        "Amputation",
        "Anastomosis",
        "Bypass",
        "Grafting",
        "Ligation",
    ]

    diagnostic_actions = [
        "Examination",
        "Evaluation",
        "Assessment",
        "Biopsy",
        "Aspiration",
        "Imaging",
        "Scanning",
        "Monitoring",
        "Testing",
        "Screening",
        "Analysis",
        "Measurement",
        "Endoscopy",
        "Arthroscopy",
        "Colonoscopy",
    ]

    general_actions = [
        "Treatment",
        "Therapy",
        "Management",
        "Administration",
        "Application",
        "Injection",
        "Infusion",
        "Drainage",
        "Dilation",
        "Manipulation",
    ]

    # Define structures by category
    category_structures = {
        "Cardiovascular": [
            "Artery",
            "Vein",
            "Heart",
            "Valve",
            "Pericardium",
            "Coronary Artery",
            "Aorta",
            "Ventricle",
            "Atrium",
            "Bypass Graft",
        ],
        "Digestive": [
            "Esophagus",
            "Stomach",
            "Intestine",
            "Colon",
            "Rectum",
            "Liver",
            "Gallbladder",
            "Pancreas",
            "Bile Duct",
            "Appendix",
        ],
        "Endocrine": [
            "Thyroid",
            "Parathyroid",
            "Adrenal Gland",
            "Pituitary Gland",
            "Pancreas",
            "Thymus",
            "Pineal Gland",
            "Hypothalamus",
            "Ovary",
            "Testis",
        ],
        "Eye": [
            "Cornea",
            "Lens",
            "Retina",
            "Iris",
            "Conjunctiva",
            "Eyelid",
            "Lacrimal Gland",
            "Optic Nerve",
            "Vitreous",
            "Sclera",
        ],
        "Female Genital": [
            "Uterus",
            "Ovary",
            "Fallopian Tube",
            "Cervix",
            "Vagina",
            "Vulva",
            "Endometrium",
            "Myometrium",
            "Perineum",
            "Hymen",
        ],
        "Hemic and Lymphatic": [
            "Lymph Node",
            "Spleen",
            "Bone Marrow",
            "Thymus",
            "Lymphatic Vessel",
            "Blood",
            "Plasma",
            "Lymph",
            "Lymphoid Tissue",
            "Immune System",
        ],
        "Integumentary": [
            "Skin",
            "Nail",
            "Hair",
            "Sweat Gland",
            "Sebaceous Gland",
            "Subcutaneous Tissue",
            "Dermis",
            "Epidermis",
            "Melanocyte",
            "Keratinocyte",
        ],
        "Male Genital": [
            "Prostate",
            "Testis",
            "Penis",
            "Scrotum",
            "Vas Deferens",
            "Seminal Vesicle",
            "Epididymis",
            "Urethra",
            "Foreskin",
            "Glans",
        ],
        "Maternity Care and Delivery": [
            "Fetus",
            "Placenta",
            "Umbilical Cord",
            "Amniotic Fluid",
            "Uterus",
            "Cervix",
            "Birth Canal",
            "Perineum",
            "Pregnancy",
            "Labor",
        ],
        "Musculoskeletal": [
            "Bone",
            "Joint",
            "Muscle",
            "Tendon",
            "Ligament",
            "Cartilage",
            "Fascia",
            "Vertebra",
            "Disc",
            "Meniscus",
        ],
        "Nervous": [
            "Brain",
            "Spinal Cord",
            "Nerve",
            "Ganglion",
            "Meninges",
            "Cerebrum",
            "Cerebellum",
            "Brainstem",
            "Neuron",
            "Synapse",
        ],
        "Respiratory": [
            "Lung",
            "Bronchus",
            "Trachea",
            "Larynx",
            "Pharynx",
            "Pleura",
            "Diaphragm",
            "Alveolus",
            "Nasal Cavity",
            "Sinus",
        ],
        "Urinary": [
            "Kidney",
            "Ureter",
            "Bladder",
            "Urethra",
            "Nephron",
            "Renal Pelvis",
            "Renal Artery",
            "Renal Vein",
            "Glomerulus",
            "Tubule",
        ],
        "Radiology": [
            "Image",
            "Scan",
            "Film",
            "Radiograph",
            "Tomogram",
            "Sonogram",
            "Angiogram",
            "Myelogram",
            "Mammogram",
            "Fluoroscopy",
        ],
        "Pathology and Laboratory": [
            "Specimen",
            "Sample",
            "Tissue",
            "Cell",
            "Fluid",
            "Blood",
            "Urine",
            "Serum",
            "Plasma",
            "Culture",
        ],
        "Medicine": [
            "System",
            "Function",
            "Condition",
            "Disorder",
            "Disease",
            "Therapy",
            "Treatment",
            "Medication",
            "Vaccine",
            "Procedure",
        ],
        "Evaluation and Management": [
            "Consultation",
            "Evaluation",
            "Assessment",
            "Examination",
            "History",
            "Physical",
            "Review",
            "Management",
            "Care",
            "Service",
        ],
    }

    # Define locations by category
    category_locations = {
        "Cardiovascular": [
            "Cardiac",
            "Coronary",
            "Aortic",
            "Venous",
            "Arterial",
            "Peripheral",
            "Pulmonary",
            "Carotid",
            "Femoral",
            "Iliac",
        ],
        "Digestive": [
            "Oral",
            "Esophageal",
            "Gastric",
            "Intestinal",
            "Colonic",
            "Rectal",
            "Anal",
            "Hepatic",
            "Biliary",
            "Pancreatic",
        ],
        "Endocrine": [
            "Thyroid",
            "Parathyroid",
            "Adrenal",
            "Pituitary",
            "Pancreatic",
            "Thymic",
            "Pineal",
            "Hypothalamic",
            "Ovarian",
            "Testicular",
        ],
        "Eye": [
            "Corneal",
            "Lenticular",
            "Retinal",
            "Iris",
            "Conjunctival",
            "Eyelid",
            "Lacrimal",
            "Optic",
            "Vitreous",
            "Scleral",
        ],
        "Female Genital": [
            "Uterine",
            "Ovarian",
            "Fallopian",
            "Cervical",
            "Vaginal",
            "Vulvar",
            "Endometrial",
            "Myometrial",
            "Perineal",
            "Hymenal",
        ],
        "Hemic and Lymphatic": [
            "Lymph Node",
            "Splenic",
            "Bone Marrow",
            "Thymic",
            "Lymphatic",
            "Blood",
            "Plasma",
            "Lymph",
            "Lymphoid",
            "Immune",
        ],
        "Integumentary": [
            "Skin",
            "Nail",
            "Hair",
            "Sweat Gland",
            "Sebaceous Gland",
            "Subcutaneous",
            "Dermal",
            "Epidermal",
            "Melanocyte",
            "Keratinocyte",
        ],
        "Male Genital": [
            "Prostatic",
            "Testicular",
            "Penile",
            "Scrotal",
            "Vas Deferens",
            "Seminal Vesicle",
            "Epididymal",
            "Urethral",
            "Foreskin",
            "Glans",
        ],
        "Maternity Care and Delivery": [
            "Fetal",
            "Placental",
            "Umbilical",
            "Amniotic",
            "Uterine",
            "Cervical",
            "Birth Canal",
            "Perineal",
            "Pregnancy",
            "Labor",
        ],
        "Musculoskeletal": [
            "Bone",
            "Joint",
            "Muscle",
            "Tendon",
            "Ligament",
            "Cartilage",
            "Fascial",
            "Vertebral",
            "Disc",
            "Meniscal",
        ],
        "Nervous": [
            "Brain",
            "Spinal",
            "Nerve",
            "Ganglionic",
            "Meningeal",
            "Cerebral",
            "Cerebellar",
            "Brainstem",
            "Neuronal",
            "Synaptic",
        ],
        "Respiratory": [
            "Lung",
            "Bronchial",
            "Tracheal",
            "Laryngeal",
            "Pharyngeal",
            "Pleural",
            "Diaphragmatic",
            "Alveolar",
            "Nasal",
            "Sinus",
        ],
        "Urinary": [
            "Kidney",
            "Ureteral",
            "Bladder",
            "Urethral",
            "Nephron",
            "Renal Pelvis",
            "Renal",
            "Glomerular",
            "Tubular",
            "Urinary",
        ],
        "Radiology": [
            "Chest",
            "Abdominal",
            "Pelvic",
            "Cranial",
            "Spinal",
            "Extremity",
            "Thoracic",
            "Cervical",
            "Lumbar",
            "Skeletal",
        ],
        "Pathology and Laboratory": [
            "Blood",
            "Urine",
            "Tissue",
            "Cellular",
            "Fluid",
            "Serum",
            "Plasma",
            "Culture",
            "Biopsy",
            "Cytology",
        ],
        "Medicine": [
            "Systemic",
            "Functional",
            "Therapeutic",
            "Diagnostic",
            "Preventive",
            "Curative",
            "Palliative",
            "Chronic",
            "Acute",
            "Interventional",
        ],
        "Evaluation and Management": [
            "Initial",
            "Follow-up",
            "Comprehensive",
            "Detailed",
            "Problem-focused",
            "Preventive",
            "Emergency",
            "Critical",
            "Inpatient",
            "Outpatient",
        ],
    }

    # Select appropriate actions based on procedure type
    if is_surgical:
        actions = surgical_actions
    elif is_diagnostic:
        actions = diagnostic_actions
    else:
        actions = general_actions

    # Get structures and locations for the category
    structures = category_structures.get(category, category_structures["Medicine"])
    locations = category_locations.get(category, category_locations["Medicine"])

    # Get patterns for the category
    patterns = category_patterns.get(category, ["{action} of {location} {structure}"])

    # Select random components
    action = random.choice(actions)
    structure = random.choice(structures)
    location = random.choice(locations)
    pattern = random.choice(patterns)

    # Generate the procedure name
    procedure_name = pattern.format(action=action, structure=structure, location=location)

    # Add specialty-specific prefix for some specialties
    specialty_prefixes = {
        "Cardiology": "Cardiac",
        "Neurology": "Neurological",
        "Orthopedic Surgery": "Orthopedic",
        "Gastroenterology": "Gastrointestinal",
        "Urology": "Urological",
        "Pulmonology": "Pulmonary",
        "Ophthalmology": "Ophthalmic",
        "Dermatology": "Dermatological",
    }

    if specialty in specialty_prefixes and random.random() < 0.5:
        procedure_name = f"{specialty_prefixes[specialty]} {procedure_name}"

    return procedure_name


def generate_procedure_description(
    name: str,
    category: str,
    is_surgical: bool,
    is_diagnostic: bool,
    is_preventive: bool,
    requires_anesthesia: bool,
) -> str:
    """Generate a procedure description.

    Args:
        name: The procedure name.
        category: The procedure category.
        is_surgical: Whether the procedure is surgical.
        is_diagnostic: Whether the procedure is diagnostic.
        is_preventive: Whether the procedure is preventive.
        requires_anesthesia: Whether the procedure requires anesthesia.

    Returns:
        A procedure description.
    """
    # Define description templates by procedure type
    surgical_templates = [
        "A surgical procedure involving {action} of the {structure} to {purpose}.",
        "A {category} surgery that {action} the {structure} to {purpose}.",
        "A surgical {action} of the {structure} performed to {purpose}.",
        "An operative procedure to {action} the {structure}, which helps to {purpose}.",
    ]

    diagnostic_templates = [
        "A diagnostic procedure to {action} the {structure} and {purpose}.",
        "A {category} examination that {action} the {structure} to {purpose}.",
        "A diagnostic {action} of the {structure} performed to {purpose}.",
        "A procedure to {action} the {structure}, which helps to {purpose}.",
    ]

    preventive_templates = [
        "A preventive procedure to {action} the {structure} and {purpose}.",
        "A {category} intervention that {action} the {structure} to {purpose}.",
        "A preventive {action} of the {structure} performed to {purpose}.",
        "A procedure to {action} the {structure}, which helps to {purpose}.",
    ]

    general_templates = [
        "A medical procedure involving {action} of the {structure} to {purpose}.",
        "A {category} procedure that {action} the {structure} to {purpose}.",
        "A therapeutic {action} of the {structure} performed to {purpose}.",
        "A procedure to {action} the {structure}, which helps to {purpose}.",
    ]

    # Define actions by procedure type
    surgical_actions = [
        "surgical removal",
        "resection",
        "repair",
        "reconstruction",
        "transplantation",
        "implantation",
        "removal",
        "replacement",
        "revision",
        "fusion",
    ]

    diagnostic_actions = [
        "examination",
        "evaluation",
        "assessment",
        "biopsy",
        "aspiration",
        "imaging",
        "scanning",
        "monitoring",
        "testing",
        "screening",
    ]

    preventive_actions = [
        "preventive treatment",
        "prophylactic therapy",
        "preventive management",
        "screening",
        "immunization",
        "vaccination",
        "prophylaxis",
    ]

    general_actions = [
        "treatment",
        "therapy",
        "management",
        "administration",
        "application",
        "injection",
        "infusion",
        "drainage",
        "dilation",
        "manipulation",
    ]

    # Define purposes by procedure type
    surgical_purposes = [
        "treat a medical condition",
        "remove diseased tissue",
        "repair damaged structures",
        "restore normal function",
        "alleviate symptoms",
        "correct anatomical abnormalities",
        "improve quality of life",
        "prevent complications",
        "address underlying pathology",
    ]

    diagnostic_purposes = [
        "diagnose a medical condition",
        "identify abnormalities",
        "assess organ function",
        "evaluate disease progression",
        "guide treatment decisions",
        "monitor response to therapy",
        "screen for disease",
        "determine the cause of symptoms",
        "stage a disease",
    ]

    preventive_purposes = [
        "prevent disease",
        "reduce risk factors",
        "maintain health",
        "prevent complications",
        "promote wellness",
        "screen for early disease",
        "identify risk factors",
        "prevent disease progression",
        "maintain normal function",
    ]

    general_purposes = [
        "address medical issues",
        "improve patient outcomes",
        "manage symptoms",
        "treat underlying conditions",
        "restore health",
        "improve function",
        "alleviate discomfort",
        "manage disease",
        "improve quality of life",
    ]

    # Extract structure from name
    words = name.split()
    structure = words[-1] if len(words) > 0 else "structure"

    # Select appropriate templates and components based on procedure type
    if is_surgical:
        templates = surgical_templates
        actions = surgical_actions
        purposes = surgical_purposes
    elif is_diagnostic:
        templates = diagnostic_templates
        actions = diagnostic_actions
        purposes = diagnostic_purposes
    elif is_preventive:
        templates = preventive_templates
        actions = preventive_actions
        purposes = preventive_purposes
    else:
        templates = general_templates
        actions = general_actions
        purposes = general_purposes

    # Select random components
    template = random.choice(templates)
    action = random.choice(actions)
    purpose = random.choice(purposes)

    # Generate the base description
    description = template.format(
        action=action,
        structure=structure,
        category=category.lower(),
        purpose=purpose,
    )

    # Add information about anesthesia if required
    if requires_anesthesia:
        anesthesia_notes = [
            " The procedure requires anesthesia.",
            " Anesthesia is administered during this procedure.",
            " This procedure is performed under anesthesia.",
            " Anesthesia is required for patient comfort during this procedure.",
        ]
        description += random.choice(anesthesia_notes)

    return description


def generate_procedure_equipment(is_surgical: bool, category: str) -> list[str]:
    """Generate a list of equipment required for a procedure.

    Args:
        is_surgical: Whether the procedure is surgical.
        category: The procedure category.

    Returns:
        A list of required equipment.
    """
    # Define common equipment for all procedures
    common_equipment = [
        "Examination table",
        "Medical gloves",
        "Antiseptic solution",
        "Sterile drapes",
        "Vital signs monitor",
    ]

    # Define surgical equipment
    surgical_equipment = [
        "Surgical instruments",
        "Scalpel",
        "Forceps",
        "Retractors",
        "Sutures",
        "Surgical scissors",
        "Electrocautery device",
        "Surgical masks",
        "Surgical gowns",
        "Anesthesia machine",
        "Suction device",
    ]

    # Define diagnostic equipment
    diagnostic_equipment = [
        "Diagnostic imaging equipment",
        "Ultrasound machine",
        "X-ray machine",
        "CT scanner",
        "MRI machine",
        "Endoscope",
        "Microscope",
        "Laboratory equipment",
        "Biopsy needles",
        "Specimen containers",
    ]

    # Define category-specific equipment
    category_equipment = {
        "Cardiovascular": [
            "ECG machine",
            "Cardiac monitor",
            "Defibrillator",
            "Blood pressure monitor",
            "Stethoscope",
            "Cardiac catheterization equipment",
        ],
        "Digestive": [
            "Endoscope",
            "Colonoscope",
            "Gastroscope",
            "Biopsy forceps",
            "Specimen containers",
        ],
        "Respiratory": [
            "Bronchoscope",
            "Spirometer",
            "Oxygen delivery system",
            "Ventilator",
            "Nebulizer",
        ],
        "Musculoskeletal": [
            "Orthopedic instruments",
            "Bone saw",
            "Drill",
            "Implants",
            "Casting materials",
        ],
        "Nervous": [
            "Neurosurgical instruments",
            "Microscope",
            "Stereotactic frame",
            "Nerve stimulator",
            "EEG machine",
        ],
        "Eye": [
            "Ophthalmoscope",
            "Slit lamp",
            "Tonometer",
            "Eye speculum",
            "Ophthalmic surgical microscope",
        ],
        "Urinary": [
            "Cystoscope",
            "Urethral catheters",
            "Urine collection system",
            "Lithotripter",
        ],
        "Radiology": [
            "X-ray machine",
            "CT scanner",
            "MRI machine",
            "Ultrasound machine",
            "Fluoroscope",
            "PACS system",
        ],
    }

    # Select equipment based on procedure type and category
    selected_equipment = common_equipment.copy()

    if is_surgical:
        selected_equipment.extend(random.sample(surgical_equipment, min(5, len(surgical_equipment))))
    else:
        selected_equipment.extend(random.sample(diagnostic_equipment, min(3, len(diagnostic_equipment))))

    # Add category-specific equipment if available
    if category in category_equipment:
        selected_equipment.extend(
            random.sample(category_equipment[category], min(3, len(category_equipment[category])))
        )

    # Remove duplicates and return a random subset
    unique_equipment = list(set(selected_equipment))
    num_equipment = random.randint(3, min(8, len(unique_equipment)))

    return random.sample(unique_equipment, num_equipment)


def generate_procedure_complications(is_surgical: bool, category: str) -> list[str]:
    """Generate a list of potential complications for a procedure.

    Args:
        is_surgical: Whether the procedure is surgical.
        category: The procedure category.

    Returns:
        A list of potential complications.
    """
    # Define common complications for all procedures
    common_complications = [
        "Infection",
        "Bleeding",
        "Pain",
        "Allergic reaction",
        "Nausea",
    ]

    # Define surgical complications
    surgical_complications = [
        "Wound dehiscence",
        "Surgical site infection",
        "Excessive bleeding",
        "Blood clots",
        "Reaction to anesthesia",
        "Damage to surrounding tissues",
        "Scarring",
        "Delayed healing",
        "Nerve damage",
        "Post-operative pain",
    ]

    # Define non-surgical complications
    non_surgical_complications = [
        "Discomfort",
        "Bruising",
        "Dizziness",
        "Allergic reaction",
        "Skin irritation",
        "Temporary pain",
        "Nausea",
    ]

    # Define category-specific complications
    category_complications = {
        "Cardiovascular": [
            "Arrhythmia",
            "Myocardial infarction",
            "Stroke",
            "Cardiac tamponade",
            "Vascular damage",
        ],
        "Digestive": [
            "Perforation",
            "Bleeding",
            "Infection",
            "Ileus",
            "Anastomotic leak",
        ],
        "Respiratory": [
            "Pneumonia",
            "Respiratory depression",
            "Bronchospasm",
            "Pneumothorax",
            "Aspiration",
        ],
        "Musculoskeletal": [
            "Joint stiffness",
            "Implant failure",
            "Non-union",
            "Compartment syndrome",
            "Osteomyelitis",
        ],
        "Nervous": [
            "Neurological deficit",
            "Seizure",
            "Intracranial hemorrhage",
            "Spinal cord injury",
            "Meningitis",
        ],
        "Eye": [
            "Vision loss",
            "Infection",
            "Increased intraocular pressure",
            "Retinal detachment",
            "Corneal abrasion",
        ],
        "Urinary": [
            "Urinary retention",
            "Urinary tract infection",
            "Hematuria",
            "Ureteral injury",
            "Bladder perforation",
        ],
    }

    # Select complications based on procedure type and category
    selected_complications = common_complications.copy()

    if is_surgical:
        selected_complications.extend(random.sample(surgical_complications, min(3, len(surgical_complications))))
    else:
        selected_complications.extend(
            random.sample(non_surgical_complications, min(2, len(non_surgical_complications)))
        )

    # Add category-specific complications if available
    if category in category_complications:
        selected_complications.extend(
            random.sample(category_complications[category], min(2, len(category_complications[category])))
        )

    # Remove duplicates and return a random subset
    unique_complications = list(set(selected_complications))
    num_complications = random.randint(2, min(5, len(unique_complications)))

    return random.sample(unique_complications, num_complications)
