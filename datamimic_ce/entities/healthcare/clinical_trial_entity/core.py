# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Core implementation of the Clinical Trial Entity.

This module provides the ClinicalTrialEntity class for generating realistic clinical trial data.
"""

import random
from datetime import datetime, timedelta
from typing import Any

from datamimic_ce.entities.healthcare.clinical_trial_entity.data_loader import ClinicalTrialDataLoader
from datamimic_ce.entities.healthcare.clinical_trial_entity.date_generators import generate_date_range
from datamimic_ce.entities.healthcare.clinical_trial_entity.id_generators import (
    generate_eudract_number,
    generate_irb_number,
    generate_nct_id,
    generate_protocol_id,
)
from datamimic_ce.entities.healthcare.clinical_trial_entity.location_generators import (
    determine_num_locations,
    generate_locations,
)
from datamimic_ce.entities.healthcare.clinical_trial_entity.participant_generators import (
    generate_age_range,
    generate_eligibility_criteria,
    generate_enrollment_count,
    generate_gender_eligibility,
)
from datamimic_ce.entities.healthcare.clinical_trial_entity.study_generators import (
    generate_brief_summary,
    generate_condition,
    generate_intervention_name,
    generate_intervention_type,
    generate_phase,
    generate_sponsor,
    generate_status,
    generate_study_design,
    generate_study_type,
    generate_title,
)
from datamimic_ce.entities.healthcare.healthcare_entity import HealthcareEntity
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ClinicalTrialEntity(HealthcareEntity):
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

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil | None = None,
        locale: str = "en",
        country_code: str = "US",
        dataset: str | None = None,
    ) -> None:
        """
        Initialize a new ClinicalTrialEntity.

        Args:
            class_factory_util: Utility for creating related entities
            locale: Locale code for generating localized data
            country_code: Country code for location-specific data
            dataset: Optional dataset name for consistent data generation
        """
        super().__init__(class_factory_util, locale, country_code, dataset)

    def _initialize_data_loader(self) -> None:
        """Initialize the data loader for this entity."""
        self._data_loader = ClinicalTrialDataLoader()

    @property
    def trial_id(self) -> str:
        """Get the trial ID."""
        return self.get_cached_property("trial_id", lambda: self.nct_id)

    @property
    def nct_id(self) -> str:
        """Get the NCT ID."""
        return self.get_cached_property("nct_id", lambda: generate_nct_id())

    @property
    def irb_number(self) -> str:
        """Get the IRB number."""
        return self.get_cached_property("irb_number", lambda: generate_irb_number())

    @property
    def protocol_id(self) -> str:
        """Get the protocol ID."""
        return self.get_cached_property("protocol_id", lambda: generate_protocol_id())

    @property
    def eudract_number(self) -> str | None:
        """Get the EudraCT number."""
        return self.get_cached_property(
            "eudract_number",
            lambda: generate_eudract_number(),
        )

    @property
    def phase(self) -> str:
        """Get the trial phase."""
        return self.get_cached_property("phase", lambda: generate_phase(self._data_loader, self._country_code))

    @property
    def status(self) -> str:
        """Get the trial status."""
        return self.get_cached_property("status", lambda: generate_status(self._data_loader, self._country_code))

    @property
    def sponsor(self) -> str:
        """Get the trial sponsor."""
        return self.get_cached_property("sponsor", lambda: generate_sponsor(self._data_loader, self._country_code))

    @property
    def condition(self) -> str:
        """Get the trial condition."""
        return self.get_cached_property("condition", lambda: generate_condition(self._data_loader, self._country_code))

    @property
    def conditions(self) -> list[str]:
        """Get the trial conditions as a list."""
        return self.get_cached_property("conditions", lambda: [self.condition])

    @property
    def intervention_type(self) -> str:
        """Get the intervention type."""
        return self.get_cached_property(
            "intervention_type", lambda: generate_intervention_type(self._data_loader, self._country_code)
        )

    @property
    def intervention_name(self) -> str:
        """Get the intervention name."""
        return self.get_cached_property(
            "intervention_name",
            lambda: generate_intervention_name(self.intervention_type, self.condition),
        )

    @property
    def interventions(self) -> list[dict[str, str]]:
        """Get the trial interventions as a list of dictionaries."""
        return self.get_cached_property(
            "interventions",
            lambda: [
                {
                    "type": self.intervention_type,
                    "name": self.intervention_name,
                    "description": f"A {self.intervention_type.lower()} intervention for {self.condition}",
                }
            ],
        )

    @property
    def study_design(self) -> dict[str, str]:
        """Get the study design."""
        return self.get_cached_property("study_design", lambda: generate_study_design())

    @property
    def study_type(self) -> str:
        """Get the study type."""
        return self.get_cached_property("study_type", lambda: generate_study_type())

    @property
    def title(self) -> str:
        """Get the trial title."""
        return self.get_cached_property(
            "title",
            lambda: generate_title(self.condition, self.intervention_type, self.intervention_name, self.phase),
        )

    @property
    def description(self) -> str:
        """Get the trial description."""
        return self.get_cached_property("description", lambda: self.brief_summary)

    @property
    def brief_summary(self) -> str:
        """Get the brief summary."""
        return self.get_cached_property(
            "brief_summary",
            lambda: generate_brief_summary(self.condition, self.intervention_type, self.intervention_name, self.phase),
        )

    @property
    def dates(self) -> dict[str, datetime | None]:
        """Get the trial dates."""
        return self.get_cached_property("dates", lambda: generate_date_range(self.status))

    @property
    def start_date(self) -> str:
        """Get the trial start date."""
        dates = self.dates
        if dates["start_date"]:
            return dates["start_date"].strftime("%Y-%m-%d")
        return datetime.now().strftime("%Y-%m-%d")

    @property
    def end_date(self) -> str:
        """Get the trial end date."""
        dates = self.dates
        if dates["end_date"]:
            return dates["end_date"].strftime("%Y-%m-%d")
        return (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

    @property
    def enrollment(self) -> int:
        """Get the enrollment count."""
        return self.get_cached_property(
            "enrollment",
            lambda: generate_enrollment_count(
                self.status,
                self.phase,
            ),
        )

    @property
    def enrollment_target(self) -> int:
        """Get the target enrollment."""
        return self.get_cached_property("enrollment_target", lambda: self.enrollment)

    @property
    def current_enrollment(self) -> int:
        """Get the current enrollment."""
        return self.get_cached_property(
            "current_enrollment",
            lambda: (
                self.enrollment
                if self.status in ["Completed", "Active, not recruiting", "Terminated", "Unknown status"]
                else max(1, int(self.enrollment * random.uniform(0.1, 0.9)))
                if self.status in ["Recruiting", "Enrolling by invitation"]
                else 0
            ),
        )

    @property
    def eligibility_criteria(self) -> dict[str, list[str]]:
        """Get the eligibility criteria."""
        return self.get_cached_property(
            "eligibility_criteria",
            lambda: generate_eligibility_criteria(
                self.condition,
                self._data_loader,
                self._country_code,
            ),
        )

    @property
    def age_range(self) -> dict[str, int | None]:
        """Get the age range."""
        return self.get_cached_property("age_range", lambda: generate_age_range())

    @property
    def gender(self) -> str:
        """Get the gender eligibility."""
        return self.get_cached_property("gender", lambda: generate_gender_eligibility())

    @property
    def locations(self) -> list[dict[str, Any]]:
        """Get the trial locations."""

        def _generate_locations() -> list[dict[str, Any]]:
            # Determine the number of locations based on the phase and status
            num_locations = determine_num_locations(self.phase, self.status)

            # Generate the locations
            return generate_locations(
                num_locations,
                [self._country_code],
                self._class_factory_util,
            )

        return self.get_cached_property("locations", _generate_locations)

    @property
    def lead_investigator(self) -> str:
        """Get the lead investigator."""
        return self.get_cached_property("lead_investigator", self._generate_lead_investigator)

    def _generate_lead_investigator(self) -> str:
        """Generate a lead investigator name."""
        # Use person entity to generate a name if available, otherwise use a simple approach
        if self._class_factory_util:
            person_entity = self._class_factory_util.create_person_entity(self._locale, self._dataset)
            # 75% chance of a male investigator (reflecting current demographic realities)
            gender = "M" if random.random() < 0.75 else "F"
            investigator_name = f"Dr. {person_entity.first_name(gender)} {person_entity.last_name()}"
            return investigator_name
        else:
            # Fallback to a basic implementation if no factory is available
            first_names_male = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas"]
            first_names_female = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Susan", "Jessica", "Sarah"]
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
            ]

            # 75% chance of a male investigator
            if random.random() < 0.75:
                first_name = random.choice(first_names_male)
            else:
                first_name = random.choice(first_names_female)

            last_name = random.choice(last_names)
            return f"Dr. {first_name} {last_name}"

    @property
    def primary_outcomes(self) -> list[dict[str, str]]:
        """Get the primary outcomes."""
        return self.get_cached_property("primary_outcomes", self._generate_primary_outcomes)

    def _generate_primary_outcomes(self) -> list[dict[str, str]]:
        """Generate primary outcomes for the trial."""
        # Common outcome templates based on intervention type and condition
        outcome_templates = {
            "Drug": [
                "Change in {condition} symptoms from baseline to week {week}",
                "Reduction in {condition} severity as measured by {scale}",
                "Time to {condition} resolution after treatment initiation",
                "Number of patients achieving complete remission of {condition}",
                "Change in biomarker levels associated with {condition}",
            ],
            "Device": [
                "Efficacy of {device} in treating {condition} compared to standard care",
                "Safety profile of {device} for {condition} management",
                "Patient-reported outcomes after {device} intervention for {condition}",
                "Functional improvement in {condition} after {device} use",
                "Rate of adverse events associated with {device} for {condition}",
            ],
            "Behavioral": [
                "Improvement in {condition} symptoms following {intervention} program",
                "Adherence to {intervention} protocol for {condition} management",
                "Quality of life changes after completion of {intervention} for {condition}",
                "Sustained behavior change {weeks} weeks after {intervention} for {condition}",
                "Reduction in {condition}-related disability after {intervention}",
            ],
        }

        # Get templates for the intervention type, or use a generic set
        templates = outcome_templates.get(
            self.intervention_type, ["Efficacy of {intervention} for treating {condition}"]
        )

        # Number of primary outcomes (usually 1-3)
        num_outcomes = random.randint(1, 3)
        selected_templates = random.sample(templates, min(num_outcomes, len(templates)))

        outcomes = []
        for template in selected_templates:
            # Format the template with trial-specific information
            outcome_text = template.format(
                condition=self.condition.lower(),
                intervention=self.intervention_name,
                device=self.intervention_name,
                scale=random.choice(
                    ["standard clinical assessment", "patient-reported outcome measures", "validated scale"]
                ),
                week=random.choice([4, 8, 12, 24, 48]),
                weeks=random.choice([4, 8, 12, 24, 48]),
            )

            # Add a time frame
            time_frame = f"{random.choice([4, 8, 12, 24, 48])} weeks"

            # Add a description
            description = f"This outcome measures the effectiveness of {self.intervention_name} for {self.condition} over {time_frame}."

            outcomes.append({"measure": outcome_text, "time_frame": time_frame, "description": description})

        return outcomes

    @property
    def secondary_outcomes(self) -> list[dict[str, str]]:
        """Get the secondary outcomes."""
        return self.get_cached_property("secondary_outcomes", self._generate_secondary_outcomes)

    def _generate_secondary_outcomes(self) -> list[dict[str, str]]:
        """Generate secondary outcomes for the trial."""
        # Common secondary outcome templates
        outcome_templates = [
            "Safety and tolerability of {intervention} in patients with {condition}",
            "Patient-reported quality of life changes after {intervention} for {condition}",
            "Healthcare resource utilization associated with {intervention} for {condition}",
            "Long-term efficacy of {intervention} for {condition} at {month}-month follow-up",
            "Rate of {condition} recurrence after completion of {intervention}",
            "Change in concomitant medication use during {intervention} for {condition}",
            "Caregiver burden assessment during {intervention} for {condition}",
            "Correlation between biomarker changes and clinical improvement in {condition}",
            "Time to hospital discharge after initiation of {intervention} for {condition}",
            "Cost-effectiveness of {intervention} compared to standard of care for {condition}",
        ]

        # Number of secondary outcomes (usually 2-5)
        num_outcomes = random.randint(2, 5)
        selected_templates = random.sample(outcome_templates, min(num_outcomes, len(outcome_templates)))

        outcomes = []
        for template in selected_templates:
            # Format the template with trial-specific information
            outcome_text = template.format(
                condition=self.condition.lower(),
                intervention=self.intervention_name,
                month=random.choice([3, 6, 12, 24, 36]),
            )

            # Add a time frame
            time_frame = f"{random.choice([3, 6, 12, 24, 36])} months"

            # Add a description
            description = f"This secondary outcome assesses additional effects of {self.intervention_name} for {self.condition} over {time_frame}."

            outcomes.append({"measure": outcome_text, "time_frame": time_frame, "description": description})

        return outcomes

    @property
    def results_summary(self) -> str:
        """Get the results summary."""
        return self.get_cached_property("results_summary", self._generate_results_summary)

    def _generate_results_summary(self) -> str:
        """Generate a summary of the trial results."""
        # Only completed trials have results
        if self.status != "Completed":
            return "Results not yet available."

        # Templates for different outcomes
        positive_templates = [
            "The trial demonstrated significant improvement in patients receiving {intervention} compared to control group.",
            "Treatment with {intervention} showed statistically significant benefits for patients with {condition}.",
            "{intervention} was associated with a {percent}% reduction in {condition} symptoms compared to baseline.",
            "Patients in the {intervention} group showed improved outcomes on primary measures compared to standard care.",
            "The study met its primary endpoint, showing efficacy of {intervention} for {condition}.",
        ]

        negative_templates = [
            "The trial did not meet its primary endpoint of improved outcomes with {intervention}.",
            "No statistically significant difference was observed between {intervention} and control groups.",
            "{intervention} failed to demonstrate superior efficacy compared to existing treatments for {condition}.",
            "The study showed limited clinical benefit of {intervention} in patients with {condition}.",
            "Results did not support the hypothesis that {intervention} would improve outcomes in {condition}.",
        ]

        mixed_templates = [
            "While {intervention} showed promise in secondary endpoints, it did not meet the primary outcome measures.",
            "{intervention} demonstrated benefit in a subset of patients with {condition}, but not in the overall population.",
            "The trial showed modest improvements with {intervention}, but further studies are needed to confirm efficacy.",
            "Some measures improved with {intervention}, but others showed no significant difference from control.",
            "{intervention} was well-tolerated but showed only marginal clinical improvement for {condition}.",
        ]

        # Randomly determine the outcome, weighted toward positive results
        outcome_type = random.choices(["positive", "negative", "mixed"], weights=[0.5, 0.2, 0.3], k=1)[0]

        if outcome_type == "positive":
            template = random.choice(positive_templates)
        elif outcome_type == "negative":
            template = random.choice(negative_templates)
        else:
            template = random.choice(mixed_templates)

        # Format the template with trial-specific information
        result = template.format(
            intervention=self.intervention_name,
            condition=self.condition.lower(),
            percent=random.randint(20, 75),
        )

        # Add some details about safety
        safety_templates = [
            " The safety profile was consistent with previous studies.",
            " No unexpected safety concerns were identified.",
            " Adverse events were generally mild to moderate in severity, ",
            f" with {random.randint(1, 10)}% of patients experiencing serious adverse events.",
            " The intervention was well-tolerated by most participants.",
            f" Discontinuation rate due to adverse events was {random.randint(1, 15)}%.",
        ]

        result += random.choice(safety_templates)

        # Add a conclusion
        conclusion_templates = [
            " These results support further development of this intervention.",
            " The findings suggest this approach may benefit selected patients.",
            " Additional studies are planned to further evaluate efficacy and safety.",
            " Results will be used to inform future clinical practice.",
            " The data provide valuable insights for future research directions.",
        ]

        result += random.choice(conclusion_templates)

        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert the clinical trial entity to a dictionary.

        Returns:
            A dictionary containing all properties of the clinical trial entity
        """
        return {
            "trial_id": self.trial_id,
            "nct_id": self.nct_id,
            "irb_number": self.irb_number,
            "protocol_id": self.protocol_id,
            "eudract_number": self.eudract_number,
            "title": self.title,
            "description": self.description,
            "brief_summary": self.brief_summary,
            "phase": self.phase,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "sponsor": self.sponsor,
            "lead_investigator": self.lead_investigator,
            "condition": self.condition,
            "conditions": self.conditions,
            "intervention_type": self.intervention_type,
            "intervention_name": self.intervention_name,
            "interventions": self.interventions,
            "study_design": self.study_design,
            "study_type": self.study_type,
            "eligibility_criteria": self.eligibility_criteria,
            "age_range": self.age_range,
            "gender": self.gender,
            "enrollment_target": self.enrollment_target,
            "current_enrollment": self.current_enrollment,
            "locations": self.locations,
            "primary_outcomes": self.primary_outcomes,
            "secondary_outcomes": self.secondary_outcomes,
            "results_summary": self.results_summary,
        }
