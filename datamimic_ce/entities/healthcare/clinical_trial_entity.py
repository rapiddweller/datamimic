# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import string
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

from datamimic_ce.entities.entity import Entity

T = TypeVar("T")


class ClinicalTrialEntity(Entity):
    """Generate clinical trial data.

    This class generates realistic clinical trial data including trial IDs,
    titles, descriptions, phases, statuses, dates, sponsors, investigators,
    conditions, interventions, eligibility criteria, locations, enrollment
    information, outcomes, and results summaries.
    """

    # Clinical trial phases
    PHASES = ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Early Phase 1", "Not Applicable"]

    # Clinical trial statuses
    STATUSES = [
        "Not yet recruiting",
        "Recruiting",
        "Enrolling by invitation",
        "Active, not recruiting",
        "Suspended",
        "Terminated",
        "Completed",
        "Withdrawn",
        "Unknown status",
    ]

    # Intervention types
    INTERVENTION_TYPES = [
        "Drug",
        "Device",
        "Biological",
        "Procedure",
        "Radiation",
        "Behavioral",
        "Genetic",
        "Dietary Supplement",
        "Diagnostic Test",
        "Other",
    ]

    # Common medical conditions for trials
    MEDICAL_CONDITIONS = [
        "Diabetes Type 2",
        "Hypertension",
        "Asthma",
        "Alzheimer's Disease",
        "Parkinson's Disease",
        "Breast Cancer",
        "Lung Cancer",
        "Prostate Cancer",
        "Depression",
        "Anxiety Disorder",
        "Rheumatoid Arthritis",
        "Multiple Sclerosis",
        "Chronic Obstructive Pulmonary Disease",
        "Heart Failure",
        "Stroke",
        "Obesity",
        "HIV/AIDS",
        "Hepatitis C",
        "Crohn's Disease",
        "Ulcerative Colitis",
    ]

    # Common sponsors
    SPONSORS = [
        "National Institutes of Health",
        "Pfizer",
        "Novartis",
        "Roche",
        "Merck",
        "Johnson & Johnson",
        "GlaxoSmithKline",
        "AstraZeneca",
        "Sanofi",
        "Eli Lilly and Company",
        "Bristol-Myers Squibb",
        "Amgen",
        "Gilead Sciences",
        "Bayer",
        "Boehringer Ingelheim",
        "Takeda Pharmaceutical",
        "Novo Nordisk",
        "Biogen",
        "Regeneron Pharmaceuticals",
        "Vertex Pharmaceuticals",
    ]

    # Common inclusion criteria
    INCLUSION_CRITERIA = [
        "Age 18-65 years",
        "Confirmed diagnosis of the condition under study",
        "Ability to provide informed consent",
        "Willing to comply with all study procedures",
        "Stable medical condition",
        "Normal kidney function",
        "Normal liver function",
        "No contraindications to study medication",
        "Negative pregnancy test for women of childbearing potential",
        "Willing to use effective contraception during the study",
    ]

    # Common exclusion criteria
    EXCLUSION_CRITERIA = [
        "Participation in another clinical trial within the past 30 days",
        "Known hypersensitivity to study medication",
        "Severe comorbid conditions",
        "Pregnancy or breastfeeding",
        "History of non-compliance with medical regimens",
        "Substance abuse within the past year",
        "Psychiatric disorders that would interfere with study participation",
        "Use of prohibited medications",
        "Inability to attend scheduled visits",
        "Legal incapacity or limited legal capacity",
    ]

    # Module-level cache for data to reduce file I/O
    _DATA_CACHE: dict[str, list[Any]] = {}

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the ClinicalTrialEntity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._dataset = dataset

        # Initialize field generators
        self._trial_id = None
        self._title = None
        self._description = None
        self._phase = None
        self._status = None
        self._start_date = None
        self._end_date = None
        self._sponsor = None
        self._lead_investigator = None
        self._conditions = None
        self._interventions = None
        self._eligibility_criteria = None
        self._locations = None
        self._enrollment_target = None
        self._current_enrollment = None
        self._primary_outcomes = None
        self._secondary_outcomes = None
        self._results_summary = None

        # Load data from CSV files if available
        self._load_data()

    @classmethod
    def _load_data(cls):
        """Load data from CSV files and cache it to reduce file I/O."""
        # Define the base directory for data files
        base_dir = Path(__file__).resolve().parent / "data" / "clinical_trials"

        # Create the directory if it doesn't exist
        base_dir.mkdir(parents=True, exist_ok=True)

        # Define file paths for various data files
        # We'll use the hardcoded lists for now, but this allows for future expansion
        # with CSV files

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load a simple CSV file with one value per line.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of values from the CSV file.
        """
        if not file_path.exists():
            return []

        with open(file_path, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def _get_cached_property(self, property_name: str, generator_func: Callable[[], T]) -> T:
        """Get a cached property or generate and cache it if not present.

        Args:
            property_name: The name of the property to get.
            generator_func: The function to generate the property value.

        Returns:
            The cached or newly generated property value.
        """
        # Check if the property is already cached
        if not hasattr(self, property_name) or getattr(self, property_name) is None:
            # Generate and cache the property
            setattr(self, property_name, generator_func())

        # Return the cached property
        return getattr(self, property_name)

    def _generate_trial_id(self) -> str:
        """Generate a unique trial ID.

        Returns:
            A unique trial ID in the format "NCT" followed by 8 digits.
        """
        # Generate a random 8-digit number
        digits = "".join(random.choices(string.digits, k=8))

        # Return the trial ID in the format "NCT" followed by the digits
        return f"NCT{digits}"

    def _generate_title(self) -> str:
        """Generate a trial title.

        Returns:
            A realistic clinical trial title.
        """
        # Define common prefixes for trial titles
        prefixes = [
            "A Study of",
            "Evaluation of",
            "Investigation of",
            "Assessment of",
            "Efficacy and Safety of",
            "Safety and Tolerability of",
            "Phase {} Study of".format(random.choice(["1", "2", "3", "4"])),
            "Randomized Trial of",
            "Double-Blind Study of",
            "Open-Label Study of",
        ]

        # Define common middle parts for trial titles
        middle_parts = [
            "Treatment with",
            "Therapy Using",
            "Intervention with",
            "Administration of",
            "Combination of",
            "Monotherapy with",
            "Adjuvant Therapy with",
            "Maintenance Treatment with",
            "Prophylactic Use of",
            "Rescue Therapy with",
        ]

        # Define common drug/intervention name patterns
        drug_patterns = [
            "{}{}mab".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["li", "tu", "ki", "zo", "ma", "ni", "pi", "ri", "si", "ti"]),
            ),
            "{}{}nib".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["li", "tu", "ki", "zo", "ma", "ni", "pi", "ri", "si", "ti"]),
            ),
            "{}{}stat".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["va", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
            "{}{}pril".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["la", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
            "{}{}sartan".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["la", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
        ]

        # Define common suffixes for trial titles
        suffixes = [
            f"in Patients with {random.choice(self.MEDICAL_CONDITIONS)}",
            f"for the Treatment of {random.choice(self.MEDICAL_CONDITIONS)}",
            f"in Adults with {random.choice(self.MEDICAL_CONDITIONS)}",
            f"in Pediatric Patients with {random.choice(self.MEDICAL_CONDITIONS)}",
            f"in Subjects with {random.choice(self.MEDICAL_CONDITIONS)}",
            f"for {random.choice(self.MEDICAL_CONDITIONS)}",
            f"in the Management of {random.choice(self.MEDICAL_CONDITIONS)}",
            f"for Prevention of {random.choice(self.MEDICAL_CONDITIONS)}",
            f"in Newly Diagnosed {random.choice(self.MEDICAL_CONDITIONS)}",
            f"in Refractory {random.choice(self.MEDICAL_CONDITIONS)}",
        ]

        # Generate a random drug name
        drug_name = random.choice(drug_patterns)

        # Generate a random title
        title = f"{random.choice(prefixes)} {random.choice(middle_parts)} {drug_name} {random.choice(suffixes)}"

        return title

    def _generate_description(self) -> str:
        """Generate a trial description.

        Returns:
            A realistic clinical trial description.
        """
        # Define common description templates
        templates = [
            "This study aims to evaluate the safety and efficacy of {drug} in patients with {condition}. "
            "The primary objective is to assess {objective}. "
            "Secondary objectives include {secondary_objective}. "
            "This is a {study_type} study with an estimated enrollment of {enrollment} participants.",
            "The purpose of this research is to determine if {drug} is effective for treating {condition}. "
            "Participants will receive {treatment_description}. "
            "The study will measure {measurement}. "
            "This {phase} trial will enroll approximately {enrollment} patients.",
            "This clinical trial will investigate the use of {drug} for {condition}. "
            "The study hypothesis is that {hypothesis}. "
            "Participants will be followed for {duration} to evaluate {evaluation}. "
            "The trial design is {design} with {enrollment} subjects.",
            "A {phase} clinical trial to study {drug} in the treatment of {condition}. "
            "The main goal is to determine {goal}. "
            "The study will involve {enrollment} participants who will be monitored for {duration}. "
            "Outcomes will be measured by {measurement}.",
        ]

        # Define common objectives
        objectives = [
            "the maximum tolerated dose",
            "the safety profile",
            "the efficacy compared to standard of care",
            "the pharmacokinetic properties",
            "the optimal dosing regimen",
            "the response rate",
            "the progression-free survival",
            "the overall survival",
            "the quality of life improvements",
            "the reduction in symptoms",
        ]

        # Define common secondary objectives
        secondary_objectives = [
            "evaluating adverse events",
            "measuring biomarker changes",
            "assessing patient-reported outcomes",
            "determining time to progression",
            "evaluating duration of response",
            "assessing pharmacodynamic effects",
            "measuring changes in disease markers",
            "evaluating treatment adherence",
            "assessing quality of life metrics",
            "determining long-term safety",
        ]

        # Define common study types
        study_types = [
            "randomized, double-blind, placebo-controlled",
            "open-label, single-arm",
            "non-randomized, observational",
            "randomized, open-label",
            "single-center, prospective",
            "multi-center, retrospective",
            "crossover, double-blind",
            "parallel-group, randomized",
            "dose-escalation, safety",
            "adaptive design",
        ]

        # Define common treatment descriptions
        treatment_descriptions = [
            "the study drug or placebo according to the randomization schedule",
            "different doses of the investigational product to determine the optimal dose",
            "the study medication in addition to standard of care",
            "either the new treatment or the current standard treatment",
            "the study drug administered orally once daily",
            "the investigational product administered intravenously every two weeks",
            "the study medication or an active comparator",
            "a fixed dose of the study drug for the duration of the trial",
            "the study treatment according to a predefined dose escalation protocol",
            "the investigational product followed by standard therapy",
        ]

        # Define common measurements
        measurements = [
            "changes in disease biomarkers",
            "improvement in clinical symptoms",
            "reduction in disease progression",
            "changes in quality of life scores",
            "time to event outcomes",
            "safety and tolerability parameters",
            "pharmacokinetic and pharmacodynamic endpoints",
            "patient-reported outcomes",
            "imaging-based assessments",
            "functional capacity improvements",
        ]

        # Define common hypotheses
        hypotheses = [
            "the treatment will significantly improve outcomes compared to standard care",
            "the drug will demonstrate a favorable safety profile",
            "the intervention will reduce the frequency of adverse events",
            "the treatment will show superior efficacy to current therapies",
            "the drug will be well-tolerated at the proposed dose",
            "the intervention will delay disease progression",
            "the treatment will improve quality of life metrics",
            "the drug will demonstrate activity against the target condition",
            "the intervention will reduce hospitalization rates",
            "the treatment will show a positive benefit-risk profile",
        ]

        # Define common durations
        durations = [
            "6 months",
            "1 year",
            "2 years",
            "30 days",
            "12 weeks",
            "24 weeks",
            "5 years",
            "3 months",
            "18 months",
            "the treatment period and 30 days follow-up",
        ]

        # Define common designs
        designs = [
            "randomized and controlled",
            "open-label and single-arm",
            "blinded and placebo-controlled",
            "adaptive and multi-stage",
            "crossover with washout periods",
            "parallel-group and multi-center",
            "dose-finding and sequential",
            "basket trial for multiple indications",
            "pragmatic and real-world",
            "factorial with multiple interventions",
        ]

        # Define common goals
        goals = [
            "if the treatment is safe and effective",
            "the optimal dose for future studies",
            "if the drug improves disease outcomes",
            "the treatment's effect on quality of life",
            "if the intervention reduces complications",
            "the drug's mechanism of action in humans",
            "if the treatment extends survival",
            "the drug's effect on disease biomarkers",
            "if the intervention prevents disease progression",
            "the treatment's impact on functional status",
        ]

        # Define common drug/intervention name patterns (same as in _generate_title)
        drug_patterns = [
            "{}{}mab".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["li", "tu", "ki", "zo", "ma", "ni", "pi", "ri", "si", "ti"]),
            ),
            "{}{}nib".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["li", "tu", "ki", "zo", "ma", "ni", "pi", "ri", "si", "ti"]),
            ),
            "{}{}stat".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["va", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
            "{}{}pril".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["la", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
            "{}{}sartan".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["la", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
        ]

        # Generate random values for the template
        template = random.choice(templates)
        drug = random.choice(drug_patterns)
        condition = random.choice(self.MEDICAL_CONDITIONS)
        objective = random.choice(objectives)
        secondary_objective = random.choice(secondary_objectives)
        study_type = random.choice(study_types)
        enrollment = random.randint(20, 1000)
        treatment_description = random.choice(treatment_descriptions)
        measurement = random.choice(measurements)
        phase = random.choice(self.PHASES)
        hypothesis = random.choice(hypotheses)
        duration = random.choice(durations)
        evaluation = random.choice(measurements)
        design = random.choice(designs)
        goal = random.choice(goals)

        # Fill in the template
        description = template.format(
            drug=drug,
            condition=condition,
            objective=objective,
            secondary_objective=secondary_objective,
            study_type=study_type,
            enrollment=enrollment,
            treatment_description=treatment_description,
            measurement=measurement,
            phase=phase,
            hypothesis=hypothesis,
            duration=duration,
            evaluation=evaluation,
            design=design,
            goal=goal,
        )

        return description

    def _generate_phase(self) -> str:
        """Generate a trial phase.

        Returns:
            A clinical trial phase.
        """
        return random.choice(self.PHASES)

    def _generate_status(self) -> str:
        """Generate a trial status.

        Returns:
            A clinical trial status.
        """
        return random.choice(self.STATUSES)

    def _generate_start_date(self) -> str:
        """Generate a start date for the trial.

        Returns:
            A start date in the format YYYY-MM-DD.
        """
        # Generate a random date within the last 5 years
        today = datetime.now()
        days_ago = random.randint(0, 5 * 365)  # Up to 5 years ago
        start_date = today - timedelta(days=days_ago)

        # Format the date as YYYY-MM-DD
        return start_date.strftime("%Y-%m-%d")

    def _generate_end_date(self) -> str:
        """Generate an end date for the trial.

        Returns:
            An end date in the format YYYY-MM-DD that is after the start date.
        """
        # Parse the start date
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")

        # Generate a random duration between 6 months and 5 years
        min_duration = 180  # 6 months in days
        max_duration = 5 * 365  # 5 years in days
        duration = random.randint(min_duration, max_duration)

        # Calculate the end date
        end_date = start_date + timedelta(days=duration)

        # Format the date as YYYY-MM-DD
        return end_date.strftime("%Y-%m-%d")

    def _generate_sponsor(self) -> str:
        """Generate a trial sponsor.

        Returns:
            A clinical trial sponsor.
        """
        return random.choice(self.SPONSORS)

    def _generate_lead_investigator(self) -> str:
        """Generate a lead investigator name.

        Returns:
            A lead investigator name.
        """
        # Define common first names
        first_names = [
            "James",
            "John",
            "Robert",
            "Michael",
            "William",
            "David",
            "Richard",
            "Joseph",
            "Thomas",
            "Charles",
            "Mary",
            "Patricia",
            "Jennifer",
            "Linda",
            "Elizabeth",
            "Barbara",
            "Susan",
            "Jessica",
            "Sarah",
            "Karen",
        ]

        # Define common last names
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Jones",
            "Brown",
            "Davis",
            "Miller",
            "Wilson",
            "Moore",
            "Taylor",
            "Anderson",
            "Thomas",
            "Jackson",
            "White",
            "Harris",
            "Martin",
            "Thompson",
            "Garcia",
            "Martinez",
            "Robinson",
        ]

        # Define common titles
        titles = ["Dr.", "Prof.", "Assoc. Prof.", "MD", "PhD", "MD, PhD", "MBBS", "FRCP", "FACS"]

        # Generate a random name with title
        name = f"{random.choice(titles)} {random.choice(first_names)} {random.choice(last_names)}"

        return name

    def _generate_conditions(self) -> list[str]:
        """Generate a list of medical conditions for the trial.

        Returns:
            A list of medical conditions.
        """
        # Determine the number of conditions (usually 1-3)
        num_conditions = random.randint(1, 3)

        # Select random conditions without replacement
        conditions = random.sample(self.MEDICAL_CONDITIONS, num_conditions)

        return conditions

    def _generate_interventions(self) -> list[dict[str, str]]:
        """Generate a list of interventions for the trial.

        Returns:
            A list of interventions, each with type, name, and description.
        """
        # Determine the number of interventions (usually 1-3)
        num_interventions = random.randint(1, 3)

        # Define common drug/intervention name patterns
        drug_patterns = [
            "{}{}mab".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["li", "tu", "ki", "zo", "ma", "ni", "pi", "ri", "si", "ti"]),
            ),
            "{}{}nib".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["li", "tu", "ki", "zo", "ma", "ni", "pi", "ri", "si", "ti"]),
            ),
            "{}{}stat".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["va", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
            "{}{}pril".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["la", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
            "{}{}sartan".format(
                random.choice(["A", "Be", "Ce", "Du", "E", "Fa", "Gi", "Ha", "I", "Ju"]),
                random.choice(["la", "to", "ka", "zo", "ma", "na", "pa", "ra", "sa", "ta"]),
            ),
        ]

        # Define common device names
        device_names = [
            "Smart Infusion Pump",
            "Continuous Glucose Monitor",
            "Implantable Cardioverter Defibrillator",
            "Robotic Surgical System",
            "Wearable ECG Monitor",
            "Portable Oxygen Concentrator",
            "Insulin Pump",
            "Deep Brain Stimulator",
            "Artificial Heart Valve",
            "Orthopedic Implant",
        ]

        # Define common biological intervention names
        biological_names = [
            "Stem Cell Therapy",
            "Gene Therapy",
            "Monoclonal Antibody",
            "Vaccine",
            "Recombinant Protein",
            "Cellular Immunotherapy",
            "Tissue Engineered Product",
            "Blood Product",
            "Plasma Derivative",
            "Microbiome Therapy",
        ]

        # Define common procedure names
        procedure_names = [
            "Minimally Invasive Surgery",
            "Endoscopic Procedure",
            "Catheter-based Intervention",
            "Laser Therapy",
            "Radiation Therapy",
            "Ultrasound Therapy",
            "Physical Therapy Protocol",
            "Cognitive Behavioral Therapy",
            "Acupuncture",
            "Rehabilitation Protocol",
        ]

        # Define common description templates
        description_templates = [
            "A {adjective} {type} designed to {action} in patients with {condition}.",
            "This {type} works by {mechanism} to {outcome}.",
            "A novel {type} that targets {target} to {effect}.",
            "Standard {type} modified to {modification} for improved {improvement}.",
            "Experimental {type} with potential to {potential}.",
        ]

        # Define common adjectives
        adjectives = [
            "novel",
            "innovative",
            "advanced",
            "experimental",
            "next-generation",
            "targeted",
            "specialized",
            "proprietary",
            "customized",
            "optimized",
        ]

        # Define common actions
        actions = [
            "reduce symptoms",
            "improve outcomes",
            "enhance quality of life",
            "decrease progression",
            "prevent complications",
            "restore function",
            "manage symptoms",
            "extend survival",
            "minimize side effects",
            "increase efficacy",
        ]

        # Define common mechanisms
        mechanisms = [
            "inhibiting key enzymes",
            "blocking specific receptors",
            "modulating immune response",
            "targeting disease pathways",
            "enhancing cellular function",
            "promoting tissue regeneration",
            "reducing inflammation",
            "improving metabolic processes",
            "correcting genetic defects",
            "restoring physiological balance",
        ]

        # Define common outcomes
        outcomes = [
            "improve patient outcomes",
            "reduce disease burden",
            "enhance quality of life",
            "extend survival",
            "minimize complications",
            "restore normal function",
            "prevent disease progression",
            "alleviate symptoms",
            "improve treatment response",
            "reduce healthcare utilization",
        ]

        # Define common targets
        targets = [
            "specific cellular pathways",
            "disease-causing proteins",
            "inflammatory mediators",
            "abnormal cell growth",
            "metabolic processes",
            "genetic mutations",
            "immune system components",
            "neural circuits",
            "vascular structures",
            "tissue damage",
        ]

        # Define common effects
        effects = [
            "reduce disease progression",
            "alleviate symptoms",
            "improve functional status",
            "enhance quality of life",
            "extend survival",
            "prevent complications",
            "restore normal physiology",
            "correct underlying defects",
            "modify disease course",
            "improve treatment response",
        ]

        # Define common modifications
        modifications = [
            "improve delivery",
            "enhance targeting",
            "reduce side effects",
            "increase potency",
            "extend duration of action",
            "improve bioavailability",
            "optimize dosing",
            "enhance safety profile",
            "improve patient adherence",
            "facilitate administration",
        ]

        # Define common improvements
        improvements = [
            "efficacy",
            "safety",
            "tolerability",
            "patient acceptance",
            "treatment outcomes",
            "quality of life",
            "convenience",
            "cost-effectiveness",
            "accessibility",
            "clinical utility",
        ]

        # Define common potentials
        potentials = [
            "revolutionize treatment approaches",
            "address unmet medical needs",
            "overcome treatment resistance",
            "provide personalized therapy",
            "reduce treatment burden",
            "improve long-term outcomes",
            "transform standard of care",
            "enable early intervention",
            "prevent disease recurrence",
            "facilitate recovery",
        ]

        interventions = []
        for _ in range(num_interventions):
            # Select a random intervention type
            intervention_type = random.choice(self.INTERVENTION_TYPES)

            # Generate a name based on the type
            if intervention_type == "Drug":
                name = random.choice(drug_patterns)
            elif intervention_type == "Device":
                name = random.choice(device_names)
            elif intervention_type == "Biological":
                name = random.choice(biological_names)
            elif intervention_type == "Procedure":
                name = random.choice(procedure_names)
            else:
                # For other types, generate a generic name
                name = f"{random.choice(adjectives)} {intervention_type}"

            # Generate a description
            template = random.choice(description_templates)
            condition = random.choice(self.MEDICAL_CONDITIONS)

            description = template.format(
                adjective=random.choice(adjectives),
                type=intervention_type.lower(),
                action=random.choice(actions),
                condition=condition,
                mechanism=random.choice(mechanisms),
                outcome=random.choice(outcomes),
                target=random.choice(targets),
                effect=random.choice(effects),
                modification=random.choice(modifications),
                improvement=random.choice(improvements),
                potential=random.choice(potentials),
            )

            # Add the intervention to the list
            interventions.append({"type": intervention_type, "name": name, "description": description})

        return interventions

    def _generate_eligibility_criteria(self) -> dict[str, list[str]]:
        """Generate eligibility criteria for the trial.

        Returns:
            A dictionary with inclusion and exclusion criteria.
        """
        # Determine the number of inclusion criteria (usually 3-7)
        num_inclusion = random.randint(3, 7)

        # Determine the number of exclusion criteria (usually 3-7)
        num_exclusion = random.randint(3, 7)

        # Select random inclusion criteria without replacement
        inclusion = random.sample(self.INCLUSION_CRITERIA, min(num_inclusion, len(self.INCLUSION_CRITERIA)))

        # Select random exclusion criteria without replacement
        exclusion = random.sample(self.EXCLUSION_CRITERIA, min(num_exclusion, len(self.EXCLUSION_CRITERIA)))

        return {"inclusion": inclusion, "exclusion": exclusion}

    def _generate_locations(self) -> list[dict[str, str]]:
        """Generate locations for the trial.

        Returns:
            A list of locations, each with name, address, and contact information.
        """
        # Determine the number of locations (usually 1-5)
        num_locations = random.randint(1, 5)

        # Define common institution names
        institution_names = [
            "University Medical Center",
            "General Hospital",
            "Medical Research Institute",
            "Regional Medical Center",
            "Memorial Hospital",
            "Community Health Center",
            "Specialized Treatment Center",
            "Academic Medical Center",
            "Clinical Research Center",
            "Health Sciences Center",
        ]

        # Define common city names
        cities = [
            "Boston",
            "New York",
            "Chicago",
            "Los Angeles",
            "San Francisco",
            "Houston",
            "Philadelphia",
            "Baltimore",
            "Seattle",
            "Atlanta",
            "Miami",
            "Denver",
            "Phoenix",
            "Minneapolis",
            "Cleveland",
            "Portland",
            "San Diego",
            "Dallas",
            "Pittsburgh",
            "St. Louis",
        ]

        # Define common state abbreviations
        states = [
            "MA",
            "NY",
            "IL",
            "CA",
            "CA",
            "TX",
            "PA",
            "MD",
            "WA",
            "GA",
            "FL",
            "CO",
            "AZ",
            "MN",
            "OH",
            "OR",
            "CA",
            "TX",
            "PA",
            "MO",
        ]

        # Define common street names
        street_names = [
            "Main Street",
            "Park Avenue",
            "Oak Street",
            "Maple Avenue",
            "Cedar Road",
            "Washington Boulevard",
            "University Drive",
            "Medical Center Drive",
            "Research Way",
            "Health Sciences Parkway",
            "Clinical Center Road",
            "Hospital Drive",
            "Physician's Way",
            "Treatment Center Boulevard",
            "Wellness Avenue",
        ]

        # Define common contact titles
        contact_titles = [
            "Study Coordinator",
            "Principal Investigator",
            "Research Nurse",
            "Clinical Research Associate",
            "Site Manager",
            "Research Director",
            "Clinical Trial Manager",
            "Study Physician",
            "Recruitment Coordinator",
            "Research Assistant",
        ]

        locations = []
        for i in range(num_locations):
            # Generate a random institution name
            institution = f"{random.choice(cities)} {random.choice(institution_names)}"

            # Generate a random address
            street_number = random.randint(100, 9999)
            street = random.choice(street_names)
            city = cities[i % len(cities)]  # Ensure each location has a different city
            state = states[i % len(states)]  # Corresponding state
            zip_code = f"{random.randint(10000, 99999)}"

            address = f"{street_number} {street}, {city}, {state} {zip_code}"

            # Generate a random contact
            first_names = [
                "James",
                "John",
                "Robert",
                "Michael",
                "William",
                "David",
                "Richard",
                "Joseph",
                "Thomas",
                "Charles",
                "Mary",
                "Patricia",
                "Jennifer",
                "Linda",
                "Elizabeth",
                "Barbara",
                "Susan",
                "Jessica",
                "Sarah",
                "Karen",
            ]

            last_names = [
                "Smith",
                "Johnson",
                "Williams",
                "Jones",
                "Brown",
                "Davis",
                "Miller",
                "Wilson",
                "Moore",
                "Taylor",
                "Anderson",
                "Thomas",
                "Jackson",
                "White",
                "Harris",
                "Martin",
                "Thompson",
                "Garcia",
                "Martinez",
                "Robinson",
            ]

            contact_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            contact_title = random.choice(contact_titles)
            contact_phone = f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
            contact_email = f"{contact_name.lower().replace(' ', '.')}@{institution.lower().replace(' ', '')}.edu"

            contact = f"{contact_name}, {contact_title}, {contact_phone}, {contact_email}"

            # Add the location to the list
            locations.append({"name": institution, "address": address, "contact": contact})

        return locations

    def _generate_enrollment_target(self) -> int:
        """Generate an enrollment target for the trial.

        Returns:
            An enrollment target (number of participants).
        """
        # Generate a random enrollment target
        # Small trials: 20-100 participants
        # Medium trials: 100-500 participants
        # Large trials: 500-2000 participants

        trial_size = random.choices(
            ["small", "medium", "large"],
            weights=[0.4, 0.4, 0.2],  # More small and medium trials than large ones
            k=1,
        )[0]

        if trial_size == "small":
            return random.randint(20, 100)
        elif trial_size == "medium":
            return random.randint(100, 500)
        else:  # large
            return random.randint(500, 2000)

    def _generate_current_enrollment(self) -> int:
        """Generate a current enrollment count for the trial.

        Returns:
            A current enrollment count that is less than or equal to the enrollment target.
        """
        # Get the enrollment target
        target = self.enrollment_target

        # Generate a random current enrollment based on the trial status
        status = self.status

        if status == "Not yet recruiting":
            return 0
        elif status == "Recruiting" or status == "Enrolling by invitation":
            # Partially enrolled (10-70% of target)
            return random.randint(int(target * 0.1), int(target * 0.7))
        elif status == "Active, not recruiting" or status == "Suspended" or status == "Terminated":
            # Mostly or fully enrolled (70-100% of target)
            return random.randint(int(target * 0.7), target)
        elif status == "Completed" or status == "Withdrawn":
            # Fully enrolled or slightly under (90-100% of target)
            return random.randint(int(target * 0.9), target)
        else:  # "Unknown status"
            # Random enrollment (0-100% of target)
            return random.randint(0, target)

    def _generate_primary_outcomes(self) -> list[dict[str, str]]:
        """Generate primary outcomes for the trial.

        Returns:
            A list of primary outcomes, each with measure, time frame, and description.
        """
        # Determine the number of primary outcomes (usually 1-3)
        num_outcomes = random.randint(1, 3)

        # Define common outcome measures
        measures = [
            "Overall Survival",
            "Progression-Free Survival",
            "Disease-Free Survival",
            "Objective Response Rate",
            "Complete Response Rate",
            "Time to Progression",
            "Duration of Response",
            "Change in Biomarker Levels",
            "Change in Symptom Score",
            "Incidence of Adverse Events",
            "Quality of Life Score",
            "Functional Status Assessment",
            "Pain Score",
            "Hospitalization Rate",
            "Treatment Adherence Rate",
        ]

        # Define common time frames
        time_frames = [
            "12 weeks",
            "24 weeks",
            "6 months",
            "1 year",
            "2 years",
            "5 years",
            "30 days post-treatment",
            "90 days post-treatment",
            "Throughout study duration",
            "Baseline to end of treatment",
            "Every 3 months for 2 years",
            "Weekly during treatment phase",
            "At time of disease progression",
            "Up to 3 years",
            "From baseline to week 52",
        ]

        # Define common descriptions
        descriptions = [
            "Time from randomization to death from any cause",
            "Time from randomization to disease progression or death",
            "Percentage of participants achieving complete or partial response",
            "Change from baseline in laboratory values",
            "Incidence and severity of treatment-emergent adverse events",
            "Patient-reported outcomes using validated questionnaires",
            "Proportion of participants with clinical improvement",
            "Time to first documented disease progression",
            "Duration of sustained clinical benefit",
            "Change in functional capacity as measured by standardized tests",
            "Frequency of hospitalizations related to the condition",
            "Proportion of participants requiring rescue medication",
            "Change in imaging parameters from baseline",
            "Rate of treatment discontinuation due to adverse events",
            "Time to symptom resolution",
        ]

        # Generate the outcomes
        outcomes = []
        for _ in range(num_outcomes):
            outcomes.append(
                {
                    "measure": random.choice(measures),
                    "time_frame": random.choice(time_frames),
                    "description": random.choice(descriptions),
                }
            )

        return outcomes

    def _generate_secondary_outcomes(self) -> list[dict[str, str]]:
        """Generate secondary outcomes for the trial.

        Returns:
            A list of secondary outcomes, each with measure, time frame, and description.
        """
        # Determine the number of secondary outcomes (usually 2-5)
        num_outcomes = random.randint(2, 5)

        # Define common outcome measures (different from primary outcomes)
        measures = [
            "Safety Profile",
            "Pharmacokinetic Parameters",
            "Pharmacodynamic Effects",
            "Patient Satisfaction",
            "Caregiver Burden",
            "Healthcare Resource Utilization",
            "Work Productivity",
            "Cognitive Function",
            "Physical Function",
            "Emotional Well-being",
            "Treatment Compliance",
            "Biomarker Response",
            "Imaging Response",
            "Symptom Burden",
            "Quality-Adjusted Life Years",
        ]

        # Define common time frames
        time_frames = [
            "12 weeks",
            "24 weeks",
            "6 months",
            "1 year",
            "2 years",
            "5 years",
            "30 days post-treatment",
            "90 days post-treatment",
            "Throughout study duration",
            "Baseline to end of treatment",
            "Every 3 months for 2 years",
            "Weekly during treatment phase",
            "At time of disease progression",
            "Up to 3 years",
            "From baseline to week 52",
        ]

        # Define common descriptions
        descriptions = [
            "Assessment of treatment tolerability using standardized criteria",
            "Measurement of drug concentration in plasma over time",
            "Evaluation of target engagement using biomarker analysis",
            "Assessment using validated patient satisfaction questionnaire",
            "Measurement of impact on daily activities and quality of life",
            "Tracking of healthcare visits, procedures, and hospitalizations",
            "Evaluation of ability to maintain employment and productivity",
            "Assessment using standardized cognitive function tests",
            "Measurement of physical capabilities using performance tests",
            "Evaluation using validated psychological assessment tools",
            "Tracking of medication adherence throughout the study",
            "Quantification of changes in disease-specific biomarkers",
            "Evaluation of anatomical or functional changes via imaging",
            "Assessment using symptom inventory questionnaires",
            "Calculation of quality-adjusted survival benefit",
        ]

        # Generate the outcomes
        outcomes = []
        for _ in range(num_outcomes):
            outcomes.append(
                {
                    "measure": random.choice(measures),
                    "time_frame": random.choice(time_frames),
                    "description": random.choice(descriptions),
                }
            )

        return outcomes

    def _generate_results_summary(self) -> str:
        """Generate a results summary for the trial.

        Returns:
            A results summary or an empty string if the trial is not completed.
        """
        # Only generate results if the trial is completed
        if self.status != "Completed":
            return ""

        # Define common result templates
        templates = [
            "The study met its primary endpoint, demonstrating {outcome} in the {intervention} group compared to {control}. "
            "Secondary endpoints showed {secondary_outcome}. "
            "Safety analysis revealed {safety_profile}.",
            "Results showed {outcome} with {intervention} treatment. "
            "The study {endpoint_status} its primary endpoint. "
            "Secondary analyses indicated {secondary_outcome}. "
            "The safety profile was {safety_description}.",
            "The trial demonstrated that {intervention} {effect} compared to {control}. "
            "Statistical significance was {significance} for the primary endpoint. "
            "Key secondary findings included {secondary_outcome}. "
            "Adverse events were {adverse_events}.",
            "Analysis of the primary endpoint showed {outcome} in the {intervention} arm. "
            "This represents {clinical_significance} for patients with {condition}. "
            "Notable secondary findings included {secondary_outcome}. "
            "The treatment was {tolerability}.",
        ]

        # Define common outcomes
        outcomes = [
            "a significant improvement",
            "a modest benefit",
            "a substantial reduction in risk",
            "a clinically meaningful improvement",
            "a statistically significant difference",
            "a trend toward improvement",
            "a marked reduction in symptoms",
            "an increase in response rate",
            "a prolongation of survival",
            "a decrease in disease progression",
        ]

        # Define common interventions
        interventions = [
            "treatment",
            "experimental",
            "investigational",
            "active treatment",
            "intervention",
            "study drug",
            "therapeutic",
            "test article",
            "experimental therapy",
            "novel agent",
        ]

        # Define common controls
        controls = [
            "placebo",
            "standard of care",
            "control",
            "comparator",
            "active control",
            "conventional therapy",
            "usual care",
            "best supportive care",
            "historical control",
            "baseline",
        ]

        # Define common secondary outcomes
        secondary_outcomes = [
            "consistent improvements across multiple parameters",
            "benefits in quality of life measures",
            "positive trends in most secondary endpoints",
            "mixed results with some positive findings",
            "improvements in patient-reported outcomes",
            "reductions in healthcare utilization",
            "favorable changes in biomarker levels",
            "enhanced functional status in treated patients",
            "prolonged time to subsequent therapy",
            "durable responses in a subset of patients",
        ]

        # Define common safety profiles
        safety_profiles = [
            "a favorable safety profile with no new safety signals",
            "generally well-tolerated adverse events",
            "an acceptable safety profile consistent with previous studies",
            "manageable toxicities that rarely led to discontinuation",
            "expected adverse events that were mostly mild to moderate",
            "a safety profile that supports further development",
            "some treatment-related adverse events requiring monitoring",
            "a predictable safety profile with few serious adverse events",
            "adverse events consistent with the known mechanism of action",
            "a reasonable benefit-risk profile",
        ]

        # Define common endpoint statuses
        endpoint_statuses = [
            "successfully met",
            "achieved",
            "did not meet",
            "narrowly missed",
            "exceeded expectations for",
            "showed positive trends for",
            "demonstrated significance for",
            "failed to reach significance for",
            "showed promising results for",
            "provided supportive evidence for",
        ]

        # Define common safety descriptions
        safety_descriptions = [
            "generally favorable",
            "consistent with previous reports",
            "acceptable for the patient population",
            "characterized by manageable adverse events",
            "notable for low discontinuation rates",
            "indicative of good tolerability",
            "marked by few serious adverse events",
            "supportive of continued development",
            "comparable to standard treatments",
            "appropriate for the clinical context",
        ]

        # Define common effects
        effects = [
            "significantly improved outcomes",
            "showed superior efficacy",
            "demonstrated clinical benefit",
            "reduced the risk of adverse outcomes",
            "improved quality of life",
            "extended survival",
            "delayed disease progression",
            "alleviated symptoms",
            "provided therapeutic advantage",
            "showed promising activity",
        ]

        # Define common significance levels
        significances = [
            "achieved (p<0.001)",
            "demonstrated (p<0.01)",
            "established (p<0.05)",
            "borderline (p=0.06)",
            "not achieved (p>0.05)",
            "strongly established (p<0.0001)",
            "marginally achieved (p=0.049)",
            "clearly demonstrated (p=0.002)",
            "not reached (p=0.12)",
            "convincingly shown (p=0.003)",
        ]

        # Define common adverse event descriptions
        adverse_events = [
            "generally mild and manageable",
            "consistent with the known safety profile",
            "mostly grade 1-2 in severity",
            "rarely led to treatment discontinuation",
            "comparable between treatment arms",
            "as expected for this class of agent",
            "manageable with standard interventions",
            "not associated with unexpected toxicities",
            "acceptable in the context of clinical benefit",
            "monitored closely throughout the study",
        ]

        # Define common clinical significance descriptions
        clinical_significances = [
            "an important advance",
            "a meaningful improvement",
            "a potential new option",
            "a significant breakthrough",
            "an incremental benefit",
            "a modest but important gain",
            "a clinically relevant improvement",
            "a promising development",
            "a substantial clinical benefit",
            "a noteworthy therapeutic advance",
        ]

        # Define common conditions
        conditions = self.MEDICAL_CONDITIONS

        # Define common tolerability descriptions
        tolerabilities = [
            "generally well-tolerated",
            "associated with manageable side effects",
            "demonstrated an acceptable safety profile",
            "tolerated by most patients",
            "associated with few treatment discontinuations",
            "shown to have predictable and manageable toxicities",
            "well-tolerated at the recommended dose",
            "associated with expected and manageable adverse events",
            "demonstrated a favorable benefit-risk profile",
            "tolerated with appropriate supportive care",
        ]

        # Select a random template
        template = random.choice(templates)

        # Fill in the template
        summary = template.format(
            outcome=random.choice(outcomes),
            intervention=random.choice(interventions),
            control=random.choice(controls),
            secondary_outcome=random.choice(secondary_outcomes),
            safety_profile=random.choice(safety_profiles),
            endpoint_status=random.choice(endpoint_statuses),
            safety_description=random.choice(safety_descriptions),
            effect=random.choice(effects),
            significance=random.choice(significances),
            adverse_events=random.choice(adverse_events),
            clinical_significance=random.choice(clinical_significances),
            condition=random.choice(conditions),
            tolerability=random.choice(tolerabilities),
        )

        return summary

    # Property getters
    @property
    def trial_id(self) -> str:
        """Get the trial ID.

        Returns:
            The trial ID.
        """
        return self._get_cached_property("_trial_id", self._generate_trial_id)

    @property
    def title(self) -> str:
        """Get the trial title.

        Returns:
            The trial title.
        """
        return self._get_cached_property("_title", self._generate_title)

    @property
    def description(self) -> str:
        """Get the trial description.

        Returns:
            The trial description.
        """
        return self._get_cached_property("_description", self._generate_description)

    @property
    def phase(self) -> str:
        """Get the trial phase.

        Returns:
            The trial phase.
        """
        return self._get_cached_property("_phase", self._generate_phase)

    @property
    def status(self) -> str:
        """Get the trial status.

        Returns:
            The trial status.
        """
        return self._get_cached_property("_status", self._generate_status)

    @property
    def start_date(self) -> str:
        """Get the trial start date.

        Returns:
            The trial start date in ISO format (YYYY-MM-DD).
        """
        return self._get_cached_property("_start_date", self._generate_start_date)

    @property
    def end_date(self) -> str:
        """Get the trial end date.

        Returns:
            The trial end date in ISO format (YYYY-MM-DD).
        """
        return self._get_cached_property("_end_date", self._generate_end_date)

    @property
    def sponsor(self) -> str:
        """Get the trial sponsor.

        Returns:
            The trial sponsor.
        """
        return self._get_cached_property("_sponsor", self._generate_sponsor)

    @property
    def lead_investigator(self) -> str:
        """Get the trial lead investigator.

        Returns:
            The trial lead investigator.
        """
        return self._get_cached_property("_lead_investigator", self._generate_lead_investigator)

    @property
    def conditions(self) -> list[str]:
        """Get the trial conditions.

        Returns:
            A list of medical conditions being studied.
        """
        return self._get_cached_property("_conditions", self._generate_conditions)

    @property
    def interventions(self) -> list[dict[str, str]]:
        """Get the trial interventions.

        Returns:
            A list of interventions, each with type, name, and description.
        """
        return self._get_cached_property("_interventions", self._generate_interventions)

    @property
    def eligibility_criteria(self) -> dict[str, list[str]]:
        """Get the trial eligibility criteria.

        Returns:
            A dictionary with inclusion and exclusion criteria.
        """
        return self._get_cached_property("_eligibility_criteria", self._generate_eligibility_criteria)

    @property
    def locations(self) -> list[dict[str, str]]:
        """Get the trial locations.

        Returns:
            A list of locations, each with name, address, and contact information.
        """
        return self._get_cached_property("_locations", self._generate_locations)

    @property
    def enrollment_target(self) -> int:
        """Get the trial enrollment target.

        Returns:
            The enrollment target (number of participants).
        """
        return self._get_cached_property("_enrollment_target", self._generate_enrollment_target)

    @property
    def current_enrollment(self) -> int:
        """Get the trial current enrollment.

        Returns:
            The current enrollment count.
        """
        return self._get_cached_property("_current_enrollment", self._generate_current_enrollment)

    @property
    def primary_outcomes(self) -> list[dict[str, str]]:
        """Get the trial primary outcomes.

        Returns:
            A list of primary outcomes, each with measure, time frame, and description.
        """
        return self._get_cached_property("_primary_outcomes", self._generate_primary_outcomes)

    @property
    def secondary_outcomes(self) -> list[dict[str, str]]:
        """Get the trial secondary outcomes.

        Returns:
            A list of secondary outcomes, each with measure, time frame, and description.
        """
        return self._get_cached_property("_secondary_outcomes", self._generate_secondary_outcomes)

    @property
    def results_summary(self) -> str:
        """Get the trial results summary.

        Returns:
            A results summary or an empty string if the trial is not completed.
        """
        return self._get_cached_property("_results_summary", self._generate_results_summary)

    def to_dict(self) -> dict:
        """Convert the clinical trial entity to a dictionary.

        Returns:
            A dictionary representation of the clinical trial.
        """
        return {
            "trial_id": self.trial_id,
            "title": self.title,
            "description": self.description,
            "phase": self.phase,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "sponsor": self.sponsor,
            "lead_investigator": self.lead_investigator,
            "conditions": self.conditions,
            "interventions": self.interventions,
            "eligibility_criteria": self.eligibility_criteria,
            "locations": self.locations,
            "enrollment_target": self.enrollment_target,
            "current_enrollment": self.current_enrollment,
            "primary_outcomes": self.primary_outcomes,
            "secondary_outcomes": self.secondary_outcomes,
            "results_summary": self.results_summary,
        }

    def reset(self) -> None:
        """Reset all generated data."""
        # Reset all cached properties
        self._trial_id = None
        self._title = None
        self._description = None
        self._phase = None
        self._status = None
        self._start_date = None
        self._end_date = None
        self._sponsor = None
        self._lead_investigator = None
        self._conditions = None
        self._interventions = None
        self._eligibility_criteria = None
        self._locations = None
        self._enrollment_target = None
        self._current_enrollment = None
        self._primary_outcomes = None
        self._secondary_outcomes = None
        self._results_summary = None

    @classmethod
    def generate_batch(
        cls, batch_size: int, locale: str = "en_US", dataset: str = None, class_factory_util=None
    ) -> list[dict]:
        """Generate a batch of clinical trial entities.

        Args:
            batch_size: The number of entities to generate.
            locale: The locale to use for generation.
            dataset: The dataset to use for generation.
            class_factory_util: The class factory utility to use.

        Returns:
            A list of dictionaries, each representing a clinical trial.
        """
        batch = []
        for _ in range(batch_size):
            trial = cls(class_factory_util=class_factory_util, locale=locale, dataset=dataset)
            batch.append(trial.to_dict())

        return batch
