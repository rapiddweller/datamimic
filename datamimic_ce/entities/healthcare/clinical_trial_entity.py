# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Clinical Trial Entity implementation.

This module provides the ClinicalTrialEntity class for generating realistic clinical trial data.
"""

import random
from datetime import datetime, timedelta
from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class ClinicalTrialEntity(Entity):
    """
    Entity representing a clinical trial.

    This class generates realistic clinical trial data including trial ID, title,
    description, phase, status, dates, sponsor, investigators, conditions,
    interventions, eligibility criteria, locations, enrollment information,
    outcomes, and results.
    """

    # Class constants for valid phases and statuses
    PHASES = [
        "Phase 1",
        "Phase 2",
        "Phase 3",
        "Phase 4",
        "Phase 1/Phase 2",
        "Phase 2/Phase 3",
        "Not Applicable",
        "Early Phase 1",
    ]

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

    def __init__(self, class_factory_util: ClassFactoryCEUtil, locale: str = "en", dataset: str | None = None):
        """
        Initialize a new ClinicalTrialEntity.

        Args:
            class_factory_util: Utility for creating related entities
            locale: Locale code for generating localized data
            dataset: Optional dataset name for consistent data generation
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._property_cache = {}

        # Initialize field generators
        self._reset_generators()

    def _reset_generators(self):
        """Reset all generators used by this entity."""
        self._generators = {
            "trial_id": self._generate_trial_id,
            "title": self._generate_title,
            "description": self._generate_description,
            "phase": self._generate_phase,
            "status": self._generate_status,
            "start_date": self._generate_start_date,
            "end_date": self._generate_end_date,
            "sponsor": self._generate_sponsor,
            "lead_investigator": self._generate_lead_investigator,
            "conditions": self._generate_conditions,
            "interventions": self._generate_interventions,
            "eligibility_criteria": self._generate_eligibility_criteria,
            "locations": self._generate_locations,
            "enrollment_target": self._generate_enrollment_target,
            "current_enrollment": self._generate_current_enrollment,
            "primary_outcomes": self._generate_primary_outcomes,
            "secondary_outcomes": self._generate_secondary_outcomes,
            "results_summary": self._generate_results_summary,
        }

    def _generate_trial_id(self) -> str:
        """
        Generate a realistic clinical trial ID.

        Returns:
            A string in the format "NCT" followed by 8 digits
        """
        return f"NCT{random.randint(10000000, 99999999)}"

    def _generate_title(self) -> str:
        """
        Generate a clinical trial title.

        Returns:
            A string representing the trial title
        """
        phases = self.phase
        conditions = self.conditions[0] if self.conditions else "Various Conditions"
        interventions = self.interventions[0]["name"] if self.interventions else "Treatment"

        return f"{phases} Clinical Trial of {interventions} in Patients With {conditions}"

    def _generate_description(self) -> str:
        """
        Generate a clinical trial description.

        Returns:
            A string describing the trial
        """
        phase = self.phase
        condition = self.conditions[0] if self.conditions else "the target condition"
        intervention = self.interventions[0]["name"] if self.interventions else "the treatment"

        return (
            f"This clinical trial will investigate the use of {intervention} as a "
            f"potential treatment for {condition}. The {phase} study will evaluate "
            f"clinical outcomes and safety according to established clinical guidelines."
        )

    def _generate_phase(self) -> str:
        """
        Generate a clinical trial phase.

        Returns:
            A string representing the trial phase
        """
        return random.choice(self.PHASES)

    def _generate_status(self) -> str:
        """
        Generate a clinical trial status.

        Returns:
            A string representing the trial status
        """
        return random.choice(self.STATUSES)

    def _generate_start_date(self) -> str:
        """
        Generate a start date for the clinical trial.

        Returns:
            A string in the format "YYYY-MM-DD"
        """
        # Generate a date within the last 3 years
        days_ago = random.randint(0, 3 * 365)
        start_date = datetime.now() - timedelta(days=days_ago)
        return start_date.strftime("%Y-%m-%d")

    def _generate_end_date(self) -> str:
        """
        Generate an end date for the clinical trial.

        Returns:
            A string in the format "YYYY-MM-DD"
        """
        # Parse the start date
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")

        # Generate an end date 1-5 years after the start date
        days_after = random.randint(365, 5 * 365)
        end_date = start_date + timedelta(days=days_after)
        return end_date.strftime("%Y-%m-%d")

    def _generate_sponsor(self) -> str:
        """
        Generate a sponsor for the clinical trial.

        Returns:
            A string representing the sponsor organization
        """
        sponsors = [
            "Pfizer Inc.",
            "Novartis Pharmaceuticals",
            "Merck & Co., Inc.",
            "Johnson & Johnson",
            "GlaxoSmithKline",
            "AstraZeneca",
            "Roche Holding AG",
            "Sanofi",
            "Eli Lilly and Company",
            "Bristol-Myers Squibb",
            "Amgen Inc.",
            "Gilead Sciences, Inc.",
            "Takeda Pharmaceutical Company",
            "National Institutes of Health",
            "Mayo Clinic",
            "Cleveland Clinic",
            "Johns Hopkins University",
            "Stanford University",
            "Harvard Medical School",
            "University of California",
        ]
        return random.choice(sponsors)

    def _generate_lead_investigator(self) -> str:
        """
        Generate a lead investigator for the clinical trial.

        Returns:
            A string representing the lead investigator's name
        """
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
        titles = ["Dr.", "Prof.", "Assoc. Prof."]

        title = random.choice(titles)
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

        return f"{title} {first_name} {last_name}"

    def _generate_conditions(self) -> list[str]:
        """
        Generate a list of medical conditions for the clinical trial.

        Returns:
            A list of strings representing medical conditions
        """
        all_conditions = [
            "Alzheimer's Disease",
            "Arthritis",
            "Asthma",
            "Atrial Fibrillation",
            "Autism Spectrum Disorder",
            "Breast Cancer",
            "COPD",
            "COVID-19",
            "Crohn's Disease",
            "Depression",
            "Diabetes Type 1",
            "Diabetes Type 2",
            "Heart Failure",
            "Hepatitis C",
            "HIV/AIDS",
            "Hypertension",
            "Lung Cancer",
            "Multiple Sclerosis",
            "Obesity",
            "Parkinson's Disease",
            "Prostate Cancer",
            "Psoriasis",
            "Rheumatoid Arthritis",
            "Schizophrenia",
            "Stroke",
        ]

        # Select 1-3 conditions
        num_conditions = random.randint(1, 3)
        return random.sample(all_conditions, min(num_conditions, len(all_conditions)))

    def _generate_interventions(self) -> list[dict[str, str]]:
        """
        Generate a list of interventions for the clinical trial.

        Returns:
            A list of dictionaries with intervention details
        """
        intervention_types = [
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

        drug_names = [
            "Abatacept",
            "Bevacizumab",
            "Cetuximab",
            "Dabigatran",
            "Etanercept",
            "Fingolimod",
            "Golimumab",
            "Humira",
            "Infliximab",
            "Januvia",
            "Keytruda",
            "Lenalidomide",
            "Metformin",
            "Nivolumab",
            "Omalizumab",
            "Pembrolizumab",
            "Rituximab",
            "Sitagliptin",
            "Trastuzumab",
            "Ustekinumab",
        ]

        device_names = [
            "CardioMonitor",
            "DiabetesAssist",
            "EchoScan",
            "FlexStent",
            "GlucoTrack",
            "HeartValve",
            "InsulinPump",
            "JointReplacement",
            "KneeImplant",
            "LungVent",
            "MRI-Compatible Pacemaker",
            "NeuroStimulator",
            "OxygenConcentrator",
            "PainRelief",
            "Respirator",
        ]

        procedure_names = [
            "Angioplasty",
            "Biopsy",
            "Catheterization",
            "Dialysis",
            "Endoscopy",
            "Focused Ultrasound",
            "Gastric Bypass",
            "Hysterectomy",
            "Immunotherapy",
            "Joint Replacement",
            "Kidney Transplant",
            "Laparoscopy",
            "Mastectomy",
            "Neurosurgery",
            "Organ Transplantation",
        ]

        behavioral_names = [
            "Cognitive Behavioral Therapy",
            "Dialectical Behavior Therapy",
            "Exercise Program",
            "Family Therapy",
            "Group Therapy",
            "Hypnotherapy",
            "Individual Counseling",
            "Mindfulness Training",
            "Nutritional Counseling",
            "Occupational Therapy",
            "Physical Therapy",
            "Psychoeducation",
            "Relaxation Techniques",
            "Sleep Hygiene",
            "Stress Management",
        ]

        # Select 1-2 interventions
        num_interventions = random.randint(1, 2)
        interventions = []

        for _ in range(num_interventions):
            intervention_type = random.choice(intervention_types)

            if intervention_type == "Drug":
                name = random.choice(drug_names)
                description = f"Administration of {name} to evaluate efficacy and safety"
            elif intervention_type == "Device":
                name = random.choice(device_names)
                description = f"Use of {name} to monitor or treat the condition"
            elif intervention_type == "Procedure":
                name = random.choice(procedure_names)
                description = f"{name} procedure to address the condition"
            elif intervention_type == "Behavioral":
                name = random.choice(behavioral_names)
                description = f"{name} to improve patient outcomes"
            else:
                # For other intervention types
                name = f"{intervention_type}-Based Approach"
                description = f"Standard {intervention_type.lower()} approach for the condition"

            interventions.append({"type": intervention_type, "name": name, "description": description})

        return interventions

    def _generate_eligibility_criteria(self) -> dict[str, list[str]]:
        """
        Generate eligibility criteria for the clinical trial.

        Returns:
            A dictionary with inclusion and exclusion criteria
        """
        inclusion_criteria = [
            "Age 18 years or older",
            "Able to provide written informed consent",
            "Diagnosis of the condition under study",
            "Adequate organ function",
            "Eastern Cooperative Oncology Group (ECOG) performance status of 0-1",
            "Life expectancy of at least 12 months",
            "Body Mass Index (BMI) between 18.5 and 35 kg/m²",
            "No major surgery within 8 weeks prior to enrollment",
            "Adequate bone marrow function",
            "Normal kidney function",
            "No significant medical history that could interfere with the study",
            "No history of substance abuse within the past year",
        ]

        exclusion_criteria = [
            "Pregnant or breastfeeding",
            "Participation in another clinical trial within 30 days",
            "Known hypersensitivity to study medication",
            "History of malignancy within the past 5 years",
            "Unstable medical condition requiring immediate treatment",
            "Psychiatric disorder that would interfere with study compliance",
            "QTc interval prolongation on ECG",
            "History of organ transplantation",
            "History of seizures or epilepsy",
            "Planning to become pregnant during the study period",
            "Prior treatment with similar agents",
        ]

        # Select 3-6 inclusion criteria
        num_inclusion = random.randint(3, 6)
        selected_inclusion = random.sample(inclusion_criteria, min(num_inclusion, len(inclusion_criteria)))

        # Select 3-5 exclusion criteria
        num_exclusion = random.randint(3, 5)
        selected_exclusion = random.sample(exclusion_criteria, min(num_exclusion, len(exclusion_criteria)))

        return {"inclusion": selected_inclusion, "exclusion": selected_exclusion}

    def _generate_locations(self) -> list[dict[str, Any]]:
        """
        Generate a list of locations for the clinical trial.

        Returns:
            A list of dictionaries with location details
        """
        cities = [
            "New York",
            "Los Angeles",
            "Chicago",
            "Houston",
            "Phoenix",
            "Philadelphia",
            "San Antonio",
            "San Diego",
            "Dallas",
            "San Jose",
            "Boston",
            "Seattle",
            "Denver",
            "Atlanta",
            "Miami",
        ]

        states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA", "MA", "WA", "CO", "GA", "FL"]

        facility_types = ["Hospital", "Medical Center", "Clinic", "Research Institute", "University"]

        # Generate 1-7 locations
        num_locations = random.randint(1, 7)
        locations = []

        for i in range(num_locations):
            city_idx = random.randint(0, len(cities) - 1)
            city = cities[city_idx]
            state = states[city_idx]
            facility_type = random.choice(facility_types)

            location = {
                "name": f"{facility_type} of {city}",
                "address": {
                    "street": f"{random.randint(100, 9999)} Main St",
                    "city": city,
                    "state": state,
                    "zip": f"{random.randint(10000, 99999)}",
                    "country": "United States",
                },
                "contact": {
                    "name": f"Contact Person {i + 1}",
                    "phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    "email": f"contact{i + 1}@example.com",
                },
            }

            locations.append(location)

        return locations

    def _generate_enrollment_target(self) -> int:
        """
        Generate an enrollment target for the clinical trial.

        Returns:
            An integer representing the target enrollment
        """
        # Most trials have between 10 and 1000 participants
        return random.randint(10, 1000)

    def _generate_current_enrollment(self) -> int:
        """
        Generate current enrollment for the clinical trial.

        Returns:
            An integer representing the current enrollment
        """
        target = self.enrollment_target
        status = self.status

        if status == "Not yet recruiting":
            return 0
        elif status == "Completed" or status == "Terminated":
            # For completed trials, enrollment might be slightly less than target
            return random.randint(int(target * 0.8), target)
        else:
            # For ongoing trials, enrollment is between 0 and target
            return random.randint(0, target)

    def _generate_primary_outcomes(self) -> list[dict[str, str]]:
        """
        Generate primary outcomes for the clinical trial.

        Returns:
            A list of dictionaries with outcome details
        """
        outcome_measures = [
            "Overall Survival",
            "Progression-Free Survival",
            "Disease-Free Survival",
            "Objective Response Rate",
            "Complete Response Rate",
            "Partial Response Rate",
            "Time to Progression",
            "Duration of Response",
            "Quality of Life Score",
            "Adverse Event Rate",
            "Serious Adverse Event Rate",
            "Treatment Discontinuation Rate",
            "Change in Biomarker Levels",
            "Change in Tumor Size",
            "Change in Symptom Score",
        ]

        time_frames = [
            "12 weeks",
            "24 weeks",
            "36 weeks",
            "48 weeks",
            "1 year",
            "18 months",
            "2 years",
            "3 years",
            "5 years",
        ]

        # Generate 1-3 primary outcomes
        num_outcomes = random.randint(1, 3)
        outcomes = []

        for _ in range(num_outcomes):
            measure = random.choice(outcome_measures)
            time_frame = random.choice(time_frames)

            outcome = {
                "measure": measure,
                "time_frame": time_frame,
                "description": f"Assessment of {measure.lower()} at {time_frame} after treatment initiation",
            }

            outcomes.append(outcome)

        return outcomes

    def _generate_secondary_outcomes(self) -> list[dict[str, str]]:
        """
        Generate secondary outcomes for the clinical trial.

        Returns:
            A list of dictionaries with outcome details
        """
        outcome_measures = [
            "Safety Profile",
            "Tolerability Assessment",
            "Pharmacokinetic Parameters",
            "Pharmacodynamic Effects",
            "Patient-Reported Outcomes",
            "Health-Related Quality of Life",
            "Functional Status",
            "Biomarker Changes",
            "Imaging Response",
            "Cost-Effectiveness",
            "Resource Utilization",
            "Treatment Adherence",
            "Patient Satisfaction",
            "Caregiver Burden",
            "Long-term Follow-up",
        ]

        time_frames = [
            "4 weeks",
            "8 weeks",
            "12 weeks",
            "24 weeks",
            "36 weeks",
            "48 weeks",
            "1 year",
            "18 months",
            "2 years",
        ]

        # Generate 0-5 secondary outcomes
        num_outcomes = random.randint(0, 5)
        outcomes = []

        for _ in range(num_outcomes):
            measure = random.choice(outcome_measures)
            time_frame = random.choice(time_frames)

            outcome = {
                "measure": measure,
                "time_frame": time_frame,
                "description": f"Evaluation of {measure.lower()} at {time_frame} after treatment initiation",
            }

            outcomes.append(outcome)

        return outcomes

    def _generate_results_summary(self) -> str:
        """
        Generate a results summary for the clinical trial.

        Returns:
            A string summarizing the results, or empty if trial not completed
        """
        status = self.status

        if status != "Completed":
            return ""

        positive_results = [
            "The study met its primary endpoint with statistical significance.",
            "Results showed a significant improvement in the treatment group compared to control.",
            "The intervention demonstrated efficacy with an acceptable safety profile.",
            "Positive outcomes were observed across all predefined endpoints.",
            "The trial showed promising results that warrant further investigation.",
        ]

        negative_results = [
            "The study did not meet its primary endpoint.",
            "No significant difference was observed between treatment and control groups.",
            "The intervention failed to demonstrate the expected clinical benefit.",
            "Results did not support the continued development of this approach.",
            "The trial was terminated early due to lack of efficacy.",
        ]

        mixed_results = [
            "The study showed mixed results with some endpoints met and others not reached.",
            "While some patients showed benefit, the overall population did not meet significance.",
            "The intervention showed activity but with a higher than expected adverse event profile.",
            "Results varied across different subgroups of patients.",
            "The trial demonstrated some positive signals that require confirmation in larger studies.",
        ]

        result_type = random.choice(["positive", "negative", "mixed"])

        if result_type == "positive":
            summary = random.choice(positive_results)
        elif result_type == "negative":
            summary = random.choice(negative_results)
        else:
            summary = random.choice(mixed_results)

        return summary

    def reset(self):
        """Reset the entity, clearing all cached values."""
        self._property_cache = {}
        self._reset_generators()

    @property
    def trial_id(self) -> str:
        """Get the trial ID."""
        if "trial_id" not in self._property_cache:
            self._property_cache["trial_id"] = self._generators["trial_id"]()
        return self._property_cache["trial_id"]

    @property
    def title(self) -> str:
        """Get the trial title."""
        if "title" not in self._property_cache:
            self._property_cache["title"] = self._generators["title"]()
        return self._property_cache["title"]

    @property
    def description(self) -> str:
        """Get the trial description."""
        if "description" not in self._property_cache:
            self._property_cache["description"] = self._generators["description"]()
        return self._property_cache["description"]

    @property
    def phase(self) -> str:
        """Get the trial phase."""
        if "phase" not in self._property_cache:
            self._property_cache["phase"] = self._generators["phase"]()
        return self._property_cache["phase"]

    @property
    def status(self) -> str:
        """Get the trial status."""
        if "status" not in self._property_cache:
            self._property_cache["status"] = self._generators["status"]()
        return self._property_cache["status"]

    @property
    def start_date(self) -> str:
        """Get the trial start date."""
        if "start_date" not in self._property_cache:
            self._property_cache["start_date"] = self._generators["start_date"]()
        return self._property_cache["start_date"]

    @property
    def end_date(self) -> str:
        """Get the trial end date."""
        if "end_date" not in self._property_cache:
            self._property_cache["end_date"] = self._generators["end_date"]()
        return self._property_cache["end_date"]

    @property
    def sponsor(self) -> str:
        """Get the trial sponsor."""
        if "sponsor" not in self._property_cache:
            self._property_cache["sponsor"] = self._generators["sponsor"]()
        return self._property_cache["sponsor"]

    @property
    def lead_investigator(self) -> str:
        """Get the trial lead investigator."""
        if "lead_investigator" not in self._property_cache:
            self._property_cache["lead_investigator"] = self._generators["lead_investigator"]()
        return self._property_cache["lead_investigator"]

    @property
    def conditions(self) -> list[str]:
        """Get the trial conditions."""
        if "conditions" not in self._property_cache:
            self._property_cache["conditions"] = self._generators["conditions"]()
        return self._property_cache["conditions"]

    @property
    def interventions(self) -> list[dict[str, str]]:
        """Get the trial interventions."""
        if "interventions" not in self._property_cache:
            self._property_cache["interventions"] = self._generators["interventions"]()
        return self._property_cache["interventions"]

    @property
    def eligibility_criteria(self) -> dict[str, list[str]]:
        """Get the trial eligibility criteria."""
        if "eligibility_criteria" not in self._property_cache:
            self._property_cache["eligibility_criteria"] = self._generators["eligibility_criteria"]()
        return self._property_cache["eligibility_criteria"]

    @property
    def locations(self) -> list[dict[str, Any]]:
        """Get the trial locations."""
        if "locations" not in self._property_cache:
            self._property_cache["locations"] = self._generators["locations"]()
        return self._property_cache["locations"]

    @property
    def enrollment_target(self) -> int:
        """Get the trial enrollment target."""
        if "enrollment_target" not in self._property_cache:
            self._property_cache["enrollment_target"] = self._generators["enrollment_target"]()
        return self._property_cache["enrollment_target"]

    @property
    def current_enrollment(self) -> int:
        """Get the trial current enrollment."""
        if "current_enrollment" not in self._property_cache:
            self._property_cache["current_enrollment"] = self._generators["current_enrollment"]()
        return self._property_cache["current_enrollment"]

    @property
    def primary_outcomes(self) -> list[dict[str, str]]:
        """Get the trial primary outcomes."""
        if "primary_outcomes" not in self._property_cache:
            self._property_cache["primary_outcomes"] = self._generators["primary_outcomes"]()
        return self._property_cache["primary_outcomes"]

    @property
    def secondary_outcomes(self) -> list[dict[str, str]]:
        """Get the trial secondary outcomes."""
        if "secondary_outcomes" not in self._property_cache:
            self._property_cache["secondary_outcomes"] = self._generators["secondary_outcomes"]()
        return self._property_cache["secondary_outcomes"]

    @property
    def results_summary(self) -> str:
        """Get the trial results summary."""
        if "results_summary" not in self._property_cache:
            self._property_cache["results_summary"] = self._generators["results_summary"]()
        return self._property_cache["results_summary"]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the clinical trial entity to a dictionary.

        Returns:
            A dictionary representation of the clinical trial
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

    def generate_batch(self, batch_size: int) -> list[dict[str, Any]]:
        """
        Generate a batch of clinical trial entities.

        Args:
            batch_size: Number of entities to generate

        Returns:
            A list of dictionaries, each representing a clinical trial
        """
        batch = []
        for _ in range(batch_size):
            entity = ClinicalTrialEntity(self._class_factory_util, self._locale, self._dataset)
            batch.append(entity.to_dict())
        return batch
