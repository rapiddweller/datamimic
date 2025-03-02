# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Test script for the Clinical Trial Entity.

This script demonstrates the usage of the ClinicalTrialEntity class.
"""

import json
from typing import Any

from datamimic_ce.entities.healthcare.clinical_trial_entity.core import ClinicalTrialEntity


class MockClassFactory:
    """Mock class factory for testing."""
    
    def get_app_settings(self):
        """Get application settings."""
        return {}
    
    def get_data_generation_util(self):
        """Get data generation utility."""
        return None
    
    def get_entity_factory(self):
        """Get entity factory."""
        return None
    
    def get_entity_cache(self):
        """Get entity cache."""
        return None
        
    def create_person_entity(self, locale=None, dataset=None, **kwargs):
        """Create a simple person entity for testing.
        
        Args:
            locale: The locale (not used in this mock)
            dataset: The dataset (not used in this mock)
            **kwargs: Additional parameters (not used in this mock)
            
        Returns:
            A simple mock person with first_name and last_name methods
        """
        class MockPerson:
            def first_name(self, gender=None):
                return "John" if gender == "M" else "Jane"
                
            def last_name(self):
                return "Doe"
                
        return MockPerson()


def print_trial_details(trial: dict[str, Any]) -> None:
    """Print details of a clinical trial.
    
    Args:
        trial: Dictionary containing trial details
    """
    print("\n=== Clinical Trial Details ===")
    print(f"NCT ID: {trial['nct_id']}")
    print(f"Protocol ID: {trial['protocol_id']}")
    print(f"Title: {trial['title']}")
    print(f"Phase: {trial['phase']}")
    print(f"Status: {trial['status']}")
    print(f"Sponsor: {trial['sponsor']}")
    print(f"Condition: {trial['condition']}")
    print(f"Intervention: {trial['intervention_name']} ({trial['intervention_type']})")
    
    print("\nDates:")
    print(f"  Start Date: {trial['start_date']}")
    print(f"  End Date: {trial['end_date']}")
    
    print(f"\nEnrollment: {trial.get('enrollment_target', 'N/A')} participants")
    print(f"Gender: {trial['gender']}")
    print(f"Age Range: {trial['age_range']['min']} to {trial['age_range']['max'] if trial['age_range']['max'] else 'No upper limit'} years")
    
    print("\nStudy Design:")
    for key, value in trial['study_design'].items():
        print(f"  {key.capitalize()}: {value}")
    
    print("\nEligibility Criteria:")
    print("  Inclusion Criteria:")
    for criterion in trial['eligibility_criteria'].get('inclusion', []):
        print(f"    - {criterion}")
    print("  Exclusion Criteria:")
    for criterion in trial['eligibility_criteria'].get('exclusion', []):
        print(f"    - {criterion}")
    
    print("\nLocations:")
    for location in trial['locations']:
        print(f"  - {location['name']}, {location['address']}")
        if 'contact' in location:
            print(f"    Contact: {location['contact'].get('phone', 'N/A')}, {location['contact'].get('email', 'N/A')}")
    
    print("\nBrief Summary:")
    print(f"  {trial['brief_summary']}")
    print("==============================\n")


def test_clinical_trial() -> None:
    """Main function."""
    # Create a mock class factory
    mock_factory = MockClassFactory()
    
    # Create a US clinical trial
    print("Generating a US clinical trial...")
    us_trial = ClinicalTrialEntity(
        class_factory_util=mock_factory,
        locale="en_US",
        country_code="US",
    )
    us_trial_dict = us_trial.to_dict()
    print_trial_details(us_trial_dict)
    
    # Create a German clinical trial
    print("Generating a German clinical trial...")
    de_trial = ClinicalTrialEntity(
        class_factory_util=mock_factory,
        locale="de_DE",
        country_code="DE",
    )
    de_trial_dict = de_trial.to_dict()
    print_trial_details(de_trial_dict)
    
    # Generate a batch of trials
    print("Generating a batch of 2 clinical trials...")
    batch = ClinicalTrialEntity.generate_batch(
        count=2,
        class_factory_util=mock_factory,
        locale="en_US",
        country_code="US",
    )
    
    # Print the batch as JSON
    print("\n=== Batch of Clinical Trials (JSON) ===")
    print(json.dumps(batch, indent=2))
    print("======================================\n")