# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from datetime import datetime

from datamimic_ce.entities.healthcare.medical_record_entity import MedicalRecordEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestMedicalRecordEntity(unittest.TestCase):
    """Test cases for the MedicalRecordEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.medical_record_entity = MedicalRecordEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of MedicalRecordEntity."""
        self.assertEqual(self.medical_record_entity._locale, "en")
        self.assertIsNone(self.medical_record_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        medical_record_entity = MedicalRecordEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(medical_record_entity._locale, "de")
        self.assertEqual(medical_record_entity._dataset, "test_dataset")

    def test_record_id_generation(self):
        """Test record_id generation."""
        record_id = self.medical_record_entity.record_id
        self.assertIsInstance(record_id, str)
        self.assertTrue(len(record_id) > 0)
        # Check if it follows the expected format (e.g., "MR-12345678")
        self.assertRegex(record_id, r"MR-\d+")

    def test_patient_id_generation(self):
        """Test patient_id generation."""
        patient_id = self.medical_record_entity.patient_id
        self.assertIsInstance(patient_id, str)
        self.assertTrue(len(patient_id) > 0)
        # Check if it follows the expected format (e.g., "P-12345678")
        self.assertRegex(patient_id, r"P-\d+")

    def test_doctor_id_generation(self):
        """Test doctor_id generation."""
        doctor_id = self.medical_record_entity.doctor_id
        self.assertIsInstance(doctor_id, str)
        self.assertTrue(len(doctor_id) > 0)
        # Check if it follows the expected format (e.g., "DR-12345678")
        self.assertRegex(doctor_id, r"DR-\d+")

    def test_date_generation(self):
        """Test date generation."""
        date = self.medical_record_entity.date
        self.assertIsInstance(date, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(date, r"\d{4}-\d{2}-\d{2}")
        # Validate it's a real date
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            self.fail("date is not a valid date")

    def test_visit_type_generation(self):
        """Test visit_type generation."""
        visit_type = self.medical_record_entity.visit_type
        self.assertIsInstance(visit_type, str)
        self.assertTrue(len(visit_type) > 0)

    def test_chief_complaint_generation(self):
        """Test chief_complaint generation."""
        chief_complaint = self.medical_record_entity.chief_complaint
        self.assertIsInstance(chief_complaint, str)
        self.assertTrue(len(chief_complaint) > 0)

    def test_vital_signs_generation(self):
        """Test vital_signs generation."""
        vital_signs = self.medical_record_entity.vital_signs
        self.assertIsInstance(vital_signs, dict)
        self.assertIn("temperature", vital_signs)
        self.assertIn("blood_pressure", vital_signs)
        self.assertIn("heart_rate", vital_signs)
        self.assertIn("respiratory_rate", vital_signs)
        self.assertIn("oxygen_saturation", vital_signs)
        self.assertIn("height", vital_signs)
        self.assertIn("weight", vital_signs)
        self.assertIn("bmi", vital_signs)

    def test_diagnosis_generation(self):
        """Test diagnosis generation."""
        diagnosis = self.medical_record_entity.diagnosis
        self.assertIsInstance(diagnosis, list)
        if diagnosis:  # If not empty
            for diag in diagnosis:
                self.assertIsInstance(diag, dict)
                self.assertIn("code", diag)
                self.assertIn("description", diag)
                self.assertIn("type", diag)

    def test_procedures_generation(self):
        """Test procedures generation."""
        procedures = self.medical_record_entity.procedures
        self.assertIsInstance(procedures, list)
        if procedures:  # If not empty
            for proc in procedures:
                self.assertIsInstance(proc, dict)
                self.assertIn("code", proc)
                self.assertIn("description", proc)
                self.assertIn("date", proc)

    def test_medications_generation(self):
        """Test medications generation."""
        medications = self.medical_record_entity.medications
        self.assertIsInstance(medications, list)
        if medications:  # If not empty
            for med in medications:
                self.assertIsInstance(med, dict)
                self.assertIn("name", med)
                self.assertIn("dosage", med)
                self.assertIn("frequency", med)
                self.assertIn("route", med)
                self.assertIn("start_date", med)
                self.assertIn("end_date", med)

    def test_lab_results_generation(self):
        """Test lab_results generation."""
        lab_results = self.medical_record_entity.lab_results
        self.assertIsInstance(lab_results, list)
        if lab_results:  # If not empty
            for lab in lab_results:
                self.assertIsInstance(lab, dict)
                self.assertIn("test_name", lab)
                self.assertIn("result", lab)
                self.assertIn("unit", lab)
                self.assertIn("reference_range", lab)
                self.assertIn("date", lab)

    def test_allergies_generation(self):
        """Test allergies generation."""
        allergies = self.medical_record_entity.allergies
        self.assertIsInstance(allergies, list)
        if allergies:  # If not empty
            for allergy in allergies:
                self.assertIsInstance(allergy, dict)
                self.assertIn("allergen", allergy)
                self.assertIn("reaction", allergy)
                self.assertIn("severity", allergy)

    def test_assessment_generation(self):
        """Test assessment generation."""
        assessment = self.medical_record_entity.assessment
        self.assertIsInstance(assessment, str)
        self.assertTrue(len(assessment) > 0)

    def test_plan_generation(self):
        """Test plan generation."""
        plan = self.medical_record_entity.plan
        self.assertIsInstance(plan, str)
        self.assertTrue(len(plan) > 0)

    def test_follow_up_generation(self):
        """Test follow_up generation."""
        follow_up = self.medical_record_entity.follow_up
        self.assertIsInstance(follow_up, dict)
        self.assertIn("date", follow_up)
        self.assertIn("instructions", follow_up)

    def test_notes_generation(self):
        """Test notes generation."""
        notes = self.medical_record_entity.notes
        self.assertIsInstance(notes, str)

    def test_to_dict(self):
        """Test to_dict method."""
        record_dict = self.medical_record_entity.to_dict()
        self.assertIsInstance(record_dict, dict)
        self.assertIn("record_id", record_dict)
        self.assertIn("patient_id", record_dict)
        self.assertIn("doctor_id", record_dict)
        self.assertIn("date", record_dict)
        self.assertIn("visit_type", record_dict)
        self.assertIn("chief_complaint", record_dict)
        self.assertIn("vital_signs", record_dict)
        self.assertIn("diagnosis", record_dict)
        self.assertIn("procedures", record_dict)
        self.assertIn("medications", record_dict)
        self.assertIn("lab_results", record_dict)
        self.assertIn("allergies", record_dict)
        self.assertIn("assessment", record_dict)
        self.assertIn("plan", record_dict)
        self.assertIn("follow_up", record_dict)
        self.assertIn("notes", record_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.medical_record_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("record_id", item)
            self.assertIn("patient_id", item)
            self.assertIn("doctor_id", item)
            self.assertIn("date", item)
            self.assertIn("visit_type", item)
            self.assertIn("chief_complaint", item)
            self.assertIn("vital_signs", item)
            self.assertIn("diagnosis", item)
            self.assertIn("procedures", item)
            self.assertIn("medications", item)
            self.assertIn("lab_results", item)
            self.assertIn("allergies", item)
            self.assertIn("assessment", item)
            self.assertIn("plan", item)
            self.assertIn("follow_up", item)
            self.assertIn("notes", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_record_id = self.medical_record_entity.record_id
        initial_patient_id = self.medical_record_entity.patient_id
        
        # Reset the entity
        self.medical_record_entity.reset()
        
        # Get new values
        new_record_id = self.medical_record_entity.record_id
        new_patient_id = self.medical_record_entity.patient_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_record_id, new_record_id)
        self.assertNotEqual(initial_patient_id, new_patient_id)

    def test_class_factory_integration(self):
        """Test integration with ClassFactoryCEUtil."""
        # This test will fail until we implement the get_medical_record_entity method in ClassFactoryCEUtil
        record = self.class_factory_util.get_medical_record_entity(locale="en_US")
        self.assertIsInstance(record, MedicalRecordEntity)
        # The locale is stored as the base language code
        self.assertEqual(record._locale.split('_')[0], "en")


if __name__ == "__main__":
    unittest.main() 