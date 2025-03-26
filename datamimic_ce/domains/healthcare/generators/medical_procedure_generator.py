# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure generator utilities.

This module provides utility functions for generating medical procedure data.
"""

import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_util import FileUtil


class MedicalProcedureGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None):
        self._dataset = dataset or "US"

    def get_procedure_name(self, category: str, specialty: str, is_surgical: bool, is_diagnostic: bool) -> str:
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
        self,
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

    def generate_specialty(self) -> str:
        """Generate a medical specialty.

        Returns:
            A medical specialty.
        """
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"specialties_{self._dataset}.csv"
        )
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        return random.choices(loaded_data, weights=wgt, k=1)[0]["specialty"]

    def generate_category(self) -> str:
        categories = [
            "Cardiovascular",
            "Digestive",
            "Endocrine",
            "Eye",
            "Female Genital",
            "Hemic and Lymphatic",
            "Integumentary",
            "Male Genital",
            "Maternity Care and Delivery",
            "Musculoskeletal",
            "Nervous",
            "Respiratory",
            "Urinary",
            "Radiology",
            "Pathology and Laboratory",
            "Medicine",
            "Evaluation and Management",
        ]
        return random.choice(categories)
