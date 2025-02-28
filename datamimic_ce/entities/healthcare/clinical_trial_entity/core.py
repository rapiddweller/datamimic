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
from datamimic_ce.entities.healthcare.clinical_trial_entity.utils import PropertyCache
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ClinicalTrialEntity:
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
        "Early Phase 1"
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
        "Unknown status"
    ]
    
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil | None = None,
        locale: str = "en",
        country_code: str = "US",
        dataset: str | None = None
    ) -> None:
        """
        Initialize a new ClinicalTrialEntity.
        
        Args:
            class_factory_util: Utility for creating related entities
            locale: Locale code for generating localized data
            country_code: Country code for location-specific data
            dataset: Optional dataset name for consistent data generation
        """
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._country_code = country_code
        self._dataset = dataset
        
        # Initialize data loader
        self._data_loader = ClinicalTrialDataLoader()
        
        # Initialize property cache
        self._property_cache = PropertyCache()
    
    @property
    def trial_id(self) -> str:
        """Get the trial ID."""
        return self._property_cache.get_or_create("trial_id", lambda: self.nct_id)
    
    @property
    def nct_id(self) -> str:
        """Get the NCT ID."""
        return self._property_cache.get_or_create(
            "nct_id", lambda: generate_nct_id()
        )
    
    @property
    def irb_number(self) -> str:
        """Get the IRB number."""
        return self._property_cache.get_or_create(
            "irb_number", lambda: generate_irb_number()
        )
    
    @property
    def protocol_id(self) -> str:
        """Get the protocol ID."""
        return self._property_cache.get_or_create(
            "protocol_id", lambda: generate_protocol_id()
        )
    
    @property
    def eudract_number(self) -> str | None:
        """Get the EudraCT number."""
        return self._property_cache.get_or_create(
            "eudract_number",
            lambda: generate_eudract_number(),
        )
    
    @property
    def phase(self) -> str:
        """Get the trial phase."""
        return self._property_cache.get_or_create(
            "phase", lambda: generate_phase(self._data_loader, self._country_code)
        )
    
    @property
    def status(self) -> str:
        """Get the trial status."""
        return self._property_cache.get_or_create(
            "status", lambda: generate_status(self._data_loader, self._country_code)
        )
    
    @property
    def sponsor(self) -> str:
        """Get the trial sponsor."""
        return self._property_cache.get_or_create(
            "sponsor", lambda: generate_sponsor(self._data_loader, self._country_code)
        )
    
    @property
    def condition(self) -> str:
        """Get the trial condition."""
        return self._property_cache.get_or_create(
            "condition", lambda: generate_condition(self._data_loader, self._country_code)
        )
    
    @property
    def conditions(self) -> list[str]:
        """Get the trial conditions as a list."""
        return self._property_cache.get_or_create(
            "conditions", lambda: [self.condition]
        )
    
    @property
    def intervention_type(self) -> str:
        """Get the intervention type."""
        return self._property_cache.get_or_create(
            "intervention_type", lambda: generate_intervention_type(self._data_loader, self._country_code)
        )
    
    @property
    def intervention_name(self) -> str:
        """Get the intervention name."""
        return self._property_cache.get_or_create(
            "intervention_name",
            lambda: generate_intervention_name(self.intervention_type, self.condition),
        )
    
    @property
    def interventions(self) -> list[dict[str, str]]:
        """Get the trial interventions as a list of dictionaries."""
        return self._property_cache.get_or_create(
            "interventions",
            lambda: [{
                "type": self.intervention_type,
                "name": self.intervention_name,
                "description": f"A {self.intervention_type.lower()} intervention for {self.condition}"
            }]
        )
    
    @property
    def study_design(self) -> dict[str, str]:
        """Get the study design."""
        return self._property_cache.get_or_create(
            "study_design", lambda: generate_study_design()
        )
    
    @property
    def study_type(self) -> str:
        """Get the study type."""
        return self._property_cache.get_or_create(
            "study_type", lambda: generate_study_type()
        )
    
    @property
    def title(self) -> str:
        """Get the trial title."""
        return self._property_cache.get_or_create(
            "title",
            lambda: generate_title(
                self.condition, self.intervention_type, self.intervention_name, self.phase
            ),
        )
    
    @property
    def description(self) -> str:
        """Get the trial description."""
        return self._property_cache.get_or_create(
            "description", lambda: self.brief_summary
        )
    
    @property
    def brief_summary(self) -> str:
        """Get the brief summary."""
        return self._property_cache.get_or_create(
            "brief_summary",
            lambda: generate_brief_summary(
                self.condition, self.intervention_type, self.intervention_name, self.phase
            ),
        )
    
    @property
    def dates(self) -> dict[str, datetime | None]:
        """Get the trial dates."""
        return self._property_cache.get_or_create(
            "dates", lambda: generate_date_range(self.status)
        )
    
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
        
        # If no end date in the implementation, generate one based on start date
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        days_to_add = random.randint(180, 1095)  # 6 months to 3 years
        return (start_date + timedelta(days=days_to_add)).strftime("%Y-%m-%d")
    
    @property
    def enrollment(self) -> int:
        """Get the enrollment count."""
        return self._property_cache.get_or_create(
            "enrollment",
            lambda: generate_enrollment_count(self.status, self.phase),
        )
    
    @property
    def enrollment_target(self) -> int:
        """Get the enrollment target."""
        return self._property_cache.get_or_create(
            "enrollment_target", lambda: max(1, self.enrollment)
        )
    
    @property
    def current_enrollment(self) -> int:
        """Get the current enrollment."""
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
    
    @property
    def eligibility_criteria(self) -> dict[str, list[str]]:
        """Get the eligibility criteria."""
        raw_criteria = self._property_cache.get_or_create(
            "raw_eligibility_criteria",
            lambda: generate_eligibility_criteria(self.condition, self._data_loader, self._country_code),
        )
        
        # Rename keys to match test expectations
        return {
            "inclusion": raw_criteria["inclusion_criteria"],
            "exclusion": raw_criteria["exclusion_criteria"]
        }
    
    @property
    def age_range(self) -> dict[str, int | None]:
        """Get the age range."""
        return self._property_cache.get_or_create(
            "age_range", lambda: generate_age_range(self.condition, self._data_loader)
        )
    
    @property
    def gender(self) -> str:
        """Get the gender eligibility."""
        return self._property_cache.get_or_create(
            "gender", lambda: generate_gender_eligibility(self.condition, self._data_loader)
        )
    
    @property
    def locations(self) -> list[dict[str, Any]]:
        """Get the trial locations."""
        raw_locations = self._property_cache.get_or_create(
            "raw_locations",
            lambda: generate_locations(
                determine_num_locations(self.phase, self.status),
                [self._country_code],
                self._class_factory_util,
            ),
        )
        
        # Ensure locations have the expected keys
        for loc in raw_locations:
            if "zip_code" in loc and "zip" not in loc:
                loc["zip"] = loc["zip_code"]
            # Add name key if it doesn't exist (set to same value as facility)
            if "name" not in loc and "facility" in loc:
                loc["name"] = loc["facility"]
            # Add address key if it doesn't exist
            if "address" not in loc:
                address_parts = []
                if "city" in loc:
                    address_parts.append(loc["city"])
                if "state" in loc:
                    address_parts.append(loc["state"])
                if "country" in loc:
                    address_parts.append(loc["country"])
                loc["address"] = ", ".join(address_parts)
            # Add contact key if it doesn't exist
            if "contact" not in loc:
                # Generate a random contact person
                first_names = ["John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Emily"]
                last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson"]
                titles = ["Dr.", "Prof.", "Mr.", "Ms.", "Mrs."]
                
                title = random.choice(titles)
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                
                phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                email = (
                    f"{first_name.lower()}.{last_name.lower()}@"
                    f"{loc.get('facility', 'example').lower().replace(' ', '')}.com"
                )
                
                loc["contact"] = {
                    "name": f"{title} {first_name} {last_name}",
                    "phone": phone,
                    "email": email
                }
        
        return raw_locations
    
    @property
    def lead_investigator(self) -> str:
        """Get the lead investigator."""
        return self._property_cache.get_or_create(
            "lead_investigator",
            lambda: self._generate_lead_investigator()
        )
    
    def _generate_lead_investigator(self) -> str:
        """Generate a lead investigator name."""
        first_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
            "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
            "Barbara", "Susan", "Jessica", "Sarah", "Karen"
        ]
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
            "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris",
            "Martin", "Thompson", "Garcia", "Martinez", "Robinson"
        ]
        titles = ["Dr.", "Prof.", "Assoc. Prof."]
        
        title = random.choice(titles)
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        return f"{title} {first_name} {last_name}"
    
    @property
    def primary_outcomes(self) -> list[dict[str, str]]:
        """Get the primary outcomes."""
        return self._property_cache.get_or_create(
            "primary_outcomes",
            lambda: self._generate_primary_outcomes()
        )
    
    def _generate_primary_outcomes(self) -> list[dict[str, str]]:
        """Generate primary outcomes."""
        outcome_measures = [
            "Overall Survival", "Progression-Free Survival", "Disease-Free Survival",
            "Objective Response Rate", "Complete Response Rate", "Partial Response Rate",
            "Time to Progression", "Duration of Response", "Quality of Life Score",
            "Adverse Event Rate", "Serious Adverse Event Rate", "Treatment Discontinuation Rate",
            "Change in Biomarker Levels", "Change in Tumor Size", "Change in Symptom Score"
        ]
        
        time_frames = [
            "12 weeks", "24 weeks", "36 weeks", "48 weeks", "1 year",
            "18 months", "2 years", "3 years", "5 years"
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
                "description": f"Assessment of {measure.lower()} at {time_frame} after treatment initiation"
            }
            
            outcomes.append(outcome)
        
        return outcomes
    
    @property
    def secondary_outcomes(self) -> list[dict[str, str]]:
        """Get the secondary outcomes."""
        return self._property_cache.get_or_create(
            "secondary_outcomes",
            lambda: self._generate_secondary_outcomes()
        )
    
    def _generate_secondary_outcomes(self) -> list[dict[str, str]]:
        """Generate secondary outcomes."""
        outcome_measures = [
            "Safety Profile", "Tolerability Assessment", "Pharmacokinetic Parameters",
            "Pharmacodynamic Effects", "Patient-Reported Outcomes", "Health-Related Quality of Life",
            "Functional Status", "Biomarker Changes", "Imaging Response", "Cost-Effectiveness",
            "Resource Utilization", "Treatment Adherence", "Patient Satisfaction",
            "Caregiver Burden", "Long-term Follow-up"
        ]
        
        time_frames = [
            "4 weeks", "8 weeks", "12 weeks", "24 weeks", "36 weeks",
            "48 weeks", "1 year", "18 months", "2 years"
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
                "description": f"Evaluation of {measure.lower()} at {time_frame} after treatment initiation"
            }
            
            outcomes.append(outcome)
        
        return outcomes
    
    @property
    def results_summary(self) -> str:
        """Get the results summary."""
        return self._property_cache.get_or_create(
            "results_summary",
            lambda: self._generate_results_summary()
        )
    
    def _generate_results_summary(self) -> str:
        """Generate a results summary."""
        status = self.status
        
        if status != "Completed":
            return ""
        
        positive_results = [
            "The study met its primary endpoint with statistical significance.",
            "Results showed a significant improvement in the treatment group compared to control.",
            "The intervention demonstrated efficacy with an acceptable safety profile.",
            "Positive outcomes were observed across all predefined endpoints.",
            "The trial showed promising results that warrant further investigation."
        ]
        
        negative_results = [
            "The study did not meet its primary endpoint.",
            "No significant difference was observed between treatment and control groups.",
            "The intervention failed to demonstrate the expected clinical benefit.",
            "Results did not support the continued development of this approach.",
            "The trial was terminated early due to lack of efficacy."
        ]
        
        mixed_results = [
            "The study showed mixed results with some endpoints met and others not reached.",
            "While some patients showed benefit, the overall population did not meet significance.",
            "The intervention showed activity but with a higher than expected adverse event profile.",
            "Results varied across different subgroups of patients.",
            "The trial demonstrated some positive signals that require confirmation in larger studies."
        ]
        
        result_type = random.choice(["positive", "negative", "mixed"])
        
        if result_type == "positive":
            summary = random.choice(positive_results)
        elif result_type == "negative":
            summary = random.choice(negative_results)
        else:
            summary = random.choice(mixed_results)
        
        return summary
    
    def reset(self) -> None:
        """Reset all cached properties."""
        self._property_cache.clear()
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the clinical trial entity to a dictionary.
        
        Returns:
            A dictionary representation of the clinical trial
        """
        # Create the dates dictionary
        dates_dict = {}
        if hasattr(self, 'dates') and isinstance(self.dates, dict):
            # Convert datetime objects to strings
            start_date = self.dates.get("start_date")
            primary_completion_date = self.dates.get("primary_completion_date")
            end_date = self.dates.get("end_date")
            
            dates_dict = {
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
                "primary_completion_date": (
                    primary_completion_date.strftime("%Y-%m-%d") if primary_completion_date else None
                ),
                "end_date": end_date.strftime("%Y-%m-%d") if end_date else None
            }
        else:
            # Fallback to using the start_date and end_date properties
            dates_dict = {
                "start_date": self.start_date,
                "primary_completion_date": None,
                "end_date": self.end_date
            }
        
        # Get eligibility criteria and ensure it has both new and old keys for backward compatibility
        eligibility = self.eligibility_criteria
        eligibility_with_compat = {
            **eligibility,  # Include the new keys (inclusion, exclusion)
            "inclusion_criteria": eligibility["inclusion"],  # Add old key for backward compatibility
            "exclusion_criteria": eligibility["exclusion"]   # Add old key for backward compatibility
        }
        
        return {
            "trial_id": self.trial_id,
            "nct_id": self.nct_id,
            "protocol_id": self.protocol_id,
            "irb_number": self.irb_number,
            "eudract_number": self.eudract_number,
            "title": self.title,
            "description": self.description,
            "brief_summary": self.brief_summary,
            "phase": self.phase,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "dates": dates_dict,
            "sponsor": self.sponsor,
            "lead_investigator": self.lead_investigator,
            "condition": self.condition,
            "conditions": self.conditions,
            "intervention_type": self.intervention_type,
            "intervention_name": self.intervention_name,
            "interventions": self.interventions,
            "study_design": self.study_design,
            "study_type": self.study_type,
            "eligibility_criteria": eligibility_with_compat,
            "gender": self.gender,
            "age_range": self.age_range,
            "locations": self.locations,
            "enrollment": self.enrollment,
            "enrollment_target": self.enrollment_target,
            "current_enrollment": self.current_enrollment,
            "primary_outcomes": self.primary_outcomes,
            "secondary_outcomes": self.secondary_outcomes,
            "results_summary": self.results_summary
        }
    
    @classmethod
    def generate_batch(
        cls,
        count: int,
        class_factory_util: BaseClassFactoryUtil | None = None,
        locale: str = "en",
        country_code: str = "US",
        dataset: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate a batch of clinical trial entities.
        
        Args:
            count: Number of entities to generate
            class_factory_util: Optional class factory utility
            locale: Locale for generating data
            country_code: Country code for location-specific data
            dataset: Optional dataset name
            
        Returns:
            A list of dictionaries, each representing a clinical trial
        """
        trials = []
        
        for _ in range(count):
            trial = cls(
                class_factory_util=class_factory_util,
                locale=locale,
                country_code=country_code,
                dataset=dataset,
            )
            trials.append(trial.to_dict())
        
        return trials
