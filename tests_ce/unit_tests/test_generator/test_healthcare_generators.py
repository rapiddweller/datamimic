# import json
# import unittest

# from datamimic_ce.domains.common.literal_generators.healthcare_generators import (
#     AllergyGenerator,
#     DiagnosisGenerator,
#     ImmunizationGenerator,
#     LabResultGenerator,
#     MedicalAppointmentGenerator,
#     MedicalProcedureGenerator,
#     MedicationGenerator,
#     PatientHistoryGenerator,
#     SymptomGenerator,
#     VitalSignsGenerator,
# )


# class TestHealthcareGenerators(unittest.TestCase):
#     """Test suite for healthcare-related generators."""

#     def test_diagnosis_generator(self):
#         """Test medical diagnosis generation."""
#         # Test default generation
#         generator = DiagnosisGenerator()
#         diagnosis = generator.generate()
#         self.assertIsInstance(diagnosis, str)
#         self.assertTrue("-" in diagnosis)  # Should contain code and description

#         # Test code-only output
#         generator = DiagnosisGenerator(code_only=True)
#         code = generator.generate()
#         self.assertIsInstance(code, str)
#         self.assertFalse("-" in code)  # Should only contain the code

#         # Test specific category
#         categories = ["cardiac", "respiratory", "endocrine", "neurological", "musculoskeletal"]
#         for category in categories:
#             generator = DiagnosisGenerator(category=category)
#             diagnosis = generator.generate()
#             self.assertTrue(any(code in diagnosis for code, _ in generator._diagnoses[category]))

#     def test_vital_signs_generator(self):
#         """Test vital signs generation."""
#         # Test blood pressure
#         generator = VitalSignsGenerator(vital_type="bp")
#         bp = generator.generate()
#         self.assertIsInstance(bp, str)
#         self.assertTrue("/" in bp)  # Should contain systolic/diastolic
#         self.assertTrue("mmHg" in bp)

#         # Test temperature
#         generator = VitalSignsGenerator(vital_type="temp")
#         temp = generator.generate()
#         self.assertIsInstance(temp, str)
#         self.assertTrue("°C" in temp)

#         # Test other vitals
#         vital_types = ["pulse", "resp", "spo2"]
#         for vital_type in vital_types:
#             generator = VitalSignsGenerator(vital_type=vital_type)
#             vital = generator.generate()
#             self.assertIsInstance(vital, str)
#             self.assertTrue(any(unit in vital for unit in ["bpm", "breaths/min", "%"]))

#         # Test abnormal values
#         generator = VitalSignsGenerator(vital_type="bp", abnormal=True)
#         bp = generator.generate()
#         systolic, diastolic = map(int, bp.split()[0].split("/"))
#         self.assertTrue(70 <= systolic <= 200 and 40 <= diastolic <= 120)

#     def test_medication_generator(self):
#         """Test medication generation."""
#         # Test default generation with dosage
#         generator = MedicationGenerator()
#         medication = generator.generate()
#         self.assertIsInstance(medication, str)
#         self.assertTrue(any(word in medication for word in ["mg", "mcg", "daily", "twice", "puffs"]))

#         # Test without dosage
#         generator = MedicationGenerator(include_dosage=False)
#         medication = generator.generate()
#         self.assertIsInstance(medication, str)
#         self.assertFalse(any(word in medication for word in ["mg", "mcg", "daily", "twice", "puffs"]))

#         # Test specific categories
#         categories = ["cardiac", "antibiotic", "analgesic", "respiratory", "psychiatric"]
#         for category in categories:
#             generator = MedicationGenerator(category=category)
#             medication = generator.generate()
#             self.assertTrue(any(med[0] in medication for med in generator._medications[category]))

#     def test_lab_result_generator(self):
#         """Test laboratory result generation."""
#         # Test default generation
#         generator = LabResultGenerator()
#         result = generator.generate()
#         self.assertIsInstance(result, str)
#         self.assertTrue(":" in result)  # Should contain test name and value
#         self.assertTrue("(" in result)  # Should contain reference range

#         # Test specific test types
#         test_types = ["cbc", "metabolic", "lipids", "thyroid", "liver"]
#         for test_type in test_types:
#             generator = LabResultGenerator(test_type=test_type)
#             result = generator.generate()
#             self.assertTrue(any(test in result for test in generator._lab_tests[test_type].keys()))

#         # Test abnormal values
#         generator = LabResultGenerator(test_type="cbc", abnormal=True)
#         result = generator.generate()
#         value = float(result.split()[1])
#         test_name = result.split(":")[0]
#         test_info = generator._lab_tests["cbc"][test_name]
#         self.assertTrue(test_info["abnormal"][0] <= value <= test_info["abnormal"][1])

#     def test_medical_procedure_generator(self):
#         """Test medical procedure generation."""
#         # Test default generation
#         generator = MedicalProcedureGenerator()
#         procedure = generator.generate()
#         self.assertIsInstance(procedure, str)
#         self.assertTrue("-" in procedure)  # Should contain code and description

#         # Test code-only output
#         generator = MedicalProcedureGenerator(code_only=True)
#         code = generator.generate()
#         self.assertIsInstance(code, str)
#         self.assertFalse("-" in code)  # Should only contain the code
#         self.assertTrue(code.isdigit())  # CPT codes are numeric

#         # Test specific categories
#         categories = ["evaluation", "surgical", "diagnostic", "therapeutic"]
#         for category in categories:
#             generator = MedicalProcedureGenerator(category=category)
#             procedure = generator.generate()
#             self.assertTrue(any(code in procedure for code, _ in generator._procedures[category]))

#     def test_allergy_generator_with_reaction(self):
#         """Test that AllergyGenerator returns allergen with reaction."""
#         generator = AllergyGenerator(include_reaction=True)
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         # Expect output format to have a dash separating allergen and reaction
#         self.assertIn(" - ", output)

#     def test_allergy_generator_without_reaction(self):
#         """Test that AllergyGenerator returns only allergen when reaction is disabled."""
#         generator = AllergyGenerator(include_reaction=False)
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         self.assertNotIn(" - ", output)

#     def test_immunization_generator_default(self):
#         """Test ImmunizationGenerator with default settings includes date info."""
#         generator = ImmunizationGenerator(include_date=True, include_booster=True)
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         # Check if output contains administered date string
#         self.assertRegex(output, r"Administered on \d{4}-\d{2}-\d{2}")
#         # Check if booster info might be present (optional)
#         booster_keywords = ["First Dose", "Second Dose", "Booster"]
#         if any(b in output for b in booster_keywords):
#             self.assertTrue(any(b in output for b in booster_keywords))

#     def test_immunization_generator_no_date(self):
#         """Test ImmunizationGenerator with date excluded."""
#         generator = ImmunizationGenerator(include_date=False, include_booster=False)
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         self.assertNotRegex(output, r"Administered on")

#     def test_medical_appointment_generator_with_time(self):
#         """Test MedicalAppointmentGenerator output includes time when enabled."""
#         generator = MedicalAppointmentGenerator(include_time=True)
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         self.assertIn("Appointment on", output)
#         # Check that there is a time formatted as HH:MM
#         self.assertRegex(output, r"\d{2}:\d{2}")
#         # Check department is included
#         departments = [
#             "Cardiology",
#             "Dermatology",
#             "Neurology",
#             "Orthopedics",
#             "Pediatrics",
#             "General Medicine",
#             "Oncology",
#             "Gynecology",
#         ]
#         self.assertTrue(any(dept in output for dept in departments))

#     def test_medical_appointment_generator_without_time(self):
#         """Test MedicalAppointmentGenerator output without time when disabled."""
#         generator = MedicalAppointmentGenerator(include_time=False)
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         self.assertIn("Appointment on", output)
#         # Ensure no time appears (look for pattern HH:MM should not match)
#         self.assertNotRegex(output, r"\d{2}:\d{2}")

#     def test_symptom_generator_default(self):
#         """Test SymptomGenerator returns a comma-separated list of symptoms."""
#         # Default category should be 'general'
#         generator = SymptomGenerator()
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         symptoms = [sym.strip() for sym in output.split(",")]
#         # Default number of symptoms is 3
#         self.assertEqual(len(symptoms), 3)

#     def test_symptom_generator_specific_category(self):
#         """Test SymptomGenerator with a specified disease category."""
#         generator = SymptomGenerator(disease_category="cardiac", number_of_symptoms=2)
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         symptoms = [sym.strip() for sym in output.split(",")]
#         self.assertEqual(len(symptoms), 2)
#         # Check that selected symptoms are in a known set for cardiac if possible
#         cardiac_symptoms = ["chest pain", "palpitations", "shortness of breath", "dizziness"]
#         # At least one symptom should be in our defined list
#         self.assertTrue(any(sym in cardiac_symptoms for sym in symptoms))

#     def test_patient_history_generator(self):
#         """Test PatientHistoryGenerator returns a valid JSON record containing key sections."""
#         generator = PatientHistoryGenerator(
#             include_allergies=True, include_immunizations=True, include_appointments=True
#         )
#         output = generator.generate()
#         self.assertIsInstance(output, str)
#         # Try to parse as JSON
#         try:
#             history = json.loads(output)
#         except Exception as e:
#             self.fail(f"Output is not valid JSON: {e}")

#         # Check for required keys
#         self.assertIn("Diagnosis", history)
#         self.assertIn("Medications", history)
#         self.assertIn("Lab Results", history)
#         self.assertIn("Allergies", history)
#         self.assertIn("Immunizations", history)
#         self.assertIn("Next Appointment", history)


# if __name__ == "__main__":
#     unittest.main()
