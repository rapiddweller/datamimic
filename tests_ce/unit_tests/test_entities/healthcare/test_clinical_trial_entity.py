# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from datetime import datetime

from datamimic_ce.entities.healthcare.clinical_trial_entity import ClinicalTrialEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestClinicalTrialEntity(unittest.TestCase):
    """Test cases for the ClinicalTrialEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.clinical_trial_entity = ClinicalTrialEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of ClinicalTrialEntity."""
        self.assertEqual(self.clinical_trial_entity._locale, "en")
        self.assertIsNone(self.clinical_trial_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        clinical_trial_entity = ClinicalTrialEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(clinical_trial_entity._locale, "de")
        self.assertEqual(clinical_trial_entity._dataset, "test_dataset")

    def test_trial_id_generation(self):
        """Test trial_id generation."""
        trial_id = self.clinical_trial_entity.trial_id
        self.assertIsInstance(trial_id, str)
        self.assertTrue(len(trial_id) > 0)
        # Check if it follows the expected format (e.g., "NCT12345678")
        self.assertRegex(trial_id, r"NCT\d+")

    def test_title_generation(self):
        """Test title generation."""
        title = self.clinical_trial_entity.title
        self.assertIsInstance(title, str)
        self.assertTrue(len(title) > 0)

    def test_description_generation(self):
        """Test description generation."""
        description = self.clinical_trial_entity.description
        self.assertIsInstance(description, str)
        self.assertTrue(len(description) > 0)

    def test_phase_generation(self):
        """Test phase generation."""
        phase = self.clinical_trial_entity.phase
        self.assertIsInstance(phase, str)
        self.assertIn(phase, ClinicalTrialEntity.PHASES)

    def test_status_generation(self):
        """Test status generation."""
        status = self.clinical_trial_entity.status
        self.assertIsInstance(status, str)
        self.assertIn(status, ClinicalTrialEntity.STATUSES)

    def test_start_date_generation(self):
        """Test start_date generation."""
        start_date = self.clinical_trial_entity.start_date
        self.assertIsInstance(start_date, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(start_date, r"\d{4}-\d{2}-\d{2}")
        # Validate it's a real date
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            self.fail("start_date is not a valid date")

    def test_end_date_generation(self):
        """Test end_date generation."""
        end_date = self.clinical_trial_entity.end_date
        self.assertIsInstance(end_date, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(end_date, r"\d{4}-\d{2}-\d{2}")
        # Validate it's a real date
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            self.fail("end_date is not a valid date")
        # Check that end_date is after start_date
        self.assertGreater(
            datetime.strptime(end_date, "%Y-%m-%d"),
            datetime.strptime(self.clinical_trial_entity.start_date, "%Y-%m-%d")
        )

    def test_sponsor_generation(self):
        """Test sponsor generation."""
        sponsor = self.clinical_trial_entity.sponsor
        self.assertIsInstance(sponsor, str)
        self.assertTrue(len(sponsor) > 0)

    def test_lead_investigator_generation(self):
        """Test lead_investigator generation."""
        lead_investigator = self.clinical_trial_entity.lead_investigator
        self.assertIsInstance(lead_investigator, str)
        self.assertTrue(len(lead_investigator) > 0)

    def test_conditions_generation(self):
        """Test conditions generation."""
        conditions = self.clinical_trial_entity.conditions
        self.assertIsInstance(conditions, list)
        if conditions:  # If not empty
            for condition in conditions:
                self.assertIsInstance(condition, str)
                self.assertTrue(len(condition) > 0)

    def test_interventions_generation(self):
        """Test interventions generation."""
        interventions = self.clinical_trial_entity.interventions
        self.assertIsInstance(interventions, list)
        if interventions:  # If not empty
            for intervention in interventions:
                self.assertIsInstance(intervention, dict)
                self.assertIn("type", intervention)
                self.assertIn("name", intervention)
                self.assertIn("description", intervention)

    def test_eligibility_criteria_generation(self):
        """Test eligibility_criteria generation."""
        eligibility_criteria = self.clinical_trial_entity.eligibility_criteria
        self.assertIsInstance(eligibility_criteria, dict)
        self.assertIn("inclusion", eligibility_criteria)
        self.assertIn("exclusion", eligibility_criteria)
        self.assertIsInstance(eligibility_criteria["inclusion"], list)
        self.assertIsInstance(eligibility_criteria["exclusion"], list)

    def test_locations_generation(self):
        """Test locations generation."""
        locations = self.clinical_trial_entity.locations
        self.assertIsInstance(locations, list)
        if locations:  # If not empty
            for location in locations:
                self.assertIsInstance(location, dict)
                self.assertIn("name", location)
                self.assertIn("address", location)
                self.assertIn("contact", location)

    def test_enrollment_target_generation(self):
        """Test enrollment_target generation."""
        enrollment_target = self.clinical_trial_entity.enrollment_target
        self.assertIsInstance(enrollment_target, int)
        self.assertGreater(enrollment_target, 0)

    def test_current_enrollment_generation(self):
        """Test current_enrollment generation."""
        current_enrollment = self.clinical_trial_entity.current_enrollment
        self.assertIsInstance(current_enrollment, int)
        self.assertGreaterEqual(current_enrollment, 0)
        # Check that current_enrollment is less than or equal to enrollment_target
        self.assertLessEqual(current_enrollment, self.clinical_trial_entity.enrollment_target)

    def test_primary_outcomes_generation(self):
        """Test primary_outcomes generation."""
        primary_outcomes = self.clinical_trial_entity.primary_outcomes
        self.assertIsInstance(primary_outcomes, list)
        if primary_outcomes:  # If not empty
            for outcome in primary_outcomes:
                self.assertIsInstance(outcome, dict)
                self.assertIn("measure", outcome)
                self.assertIn("time_frame", outcome)
                self.assertIn("description", outcome)

    def test_secondary_outcomes_generation(self):
        """Test secondary_outcomes generation."""
        secondary_outcomes = self.clinical_trial_entity.secondary_outcomes
        self.assertIsInstance(secondary_outcomes, list)
        if secondary_outcomes:  # If not empty
            for outcome in secondary_outcomes:
                self.assertIsInstance(outcome, dict)
                self.assertIn("measure", outcome)
                self.assertIn("time_frame", outcome)
                self.assertIn("description", outcome)

    def test_results_summary_generation(self):
        """Test results_summary generation."""
        results_summary = self.clinical_trial_entity.results_summary
        self.assertIsInstance(results_summary, str)
        # Could be empty if trial is not completed

    def test_to_dict(self):
        """Test to_dict method."""
        trial_dict = self.clinical_trial_entity.to_dict()
        self.assertIsInstance(trial_dict, dict)
        self.assertIn("trial_id", trial_dict)
        self.assertIn("title", trial_dict)
        self.assertIn("description", trial_dict)
        self.assertIn("phase", trial_dict)
        self.assertIn("status", trial_dict)
        self.assertIn("start_date", trial_dict)
        self.assertIn("end_date", trial_dict)
        self.assertIn("sponsor", trial_dict)
        self.assertIn("lead_investigator", trial_dict)
        self.assertIn("conditions", trial_dict)
        self.assertIn("interventions", trial_dict)
        self.assertIn("eligibility_criteria", trial_dict)
        self.assertIn("locations", trial_dict)
        self.assertIn("enrollment_target", trial_dict)
        self.assertIn("current_enrollment", trial_dict)
        self.assertIn("primary_outcomes", trial_dict)
        self.assertIn("secondary_outcomes", trial_dict)
        self.assertIn("results_summary", trial_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.clinical_trial_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("trial_id", item)
            self.assertIn("title", item)
            self.assertIn("description", item)
            self.assertIn("phase", item)
            self.assertIn("status", item)
            self.assertIn("start_date", item)
            self.assertIn("end_date", item)
            self.assertIn("sponsor", item)
            self.assertIn("lead_investigator", item)
            self.assertIn("conditions", item)
            self.assertIn("interventions", item)
            self.assertIn("eligibility_criteria", item)
            self.assertIn("locations", item)
            self.assertIn("enrollment_target", item)
            self.assertIn("current_enrollment", item)
            self.assertIn("primary_outcomes", item)
            self.assertIn("secondary_outcomes", item)
            self.assertIn("results_summary", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_trial_id = self.clinical_trial_entity.trial_id
        initial_title = self.clinical_trial_entity.title
        
        # Reset the entity
        self.clinical_trial_entity.reset()
        
        # Get new values
        new_trial_id = self.clinical_trial_entity.trial_id
        new_title = self.clinical_trial_entity.title
        
        # Values should be different after reset
        self.assertNotEqual(initial_trial_id, new_trial_id)
        self.assertNotEqual(initial_title, new_title)

    def test_class_factory_integration(self):
        """Test integration with ClassFactoryCEUtil."""
        # This test will fail until we implement the get_clinical_trial_entity method in ClassFactoryCEUtil
        trial = self.class_factory_util.get_clinical_trial_entity(locale="en_US")
        self.assertIsInstance(trial, ClinicalTrialEntity)
        self.assertEqual(trial._locale, "en_US")


if __name__ == "__main__":
    unittest.main() 