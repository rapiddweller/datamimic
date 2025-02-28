"""Integration tests for weighted medical data."""

import unittest
from pathlib import Path

from datamimic_ce.entities.lab_entity import LabEntity
from datamimic_ce.entities.lab_test_entity import LabTestEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestWeightedMedicalData(unittest.TestCase):
    """Integration tests for weighted medical data."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        
        # Clear any cached data
        LabEntity._DATA_CACHE = {}
        LabTestEntity._DATA_CACHE = {}

    def test_specimen_types_US_weighted_distribution(self):
        """Test that US specimen types are distributed according to their weights."""
        # Skip if the file doesn't exist
        specimen_types_file = Path("Core/datamimic_ce/entities/data/medical/specimen_types_US.csv")
        if not specimen_types_file.exists():
            self.skipTest(f"File {specimen_types_file} does not exist")
        
        # Create a LabTestEntity with US dataset
        lab_test_entity = LabTestEntity(self.class_factory_util, dataset="US")
        
        # Generate a large batch of lab tests
        lab_tests = lab_test_entity.generate_batch(500)
        
        # Count the specimen types
        specimen_types = {}
        for test in lab_tests:
            specimen_type = test["specimen_type"]
            if specimen_type in specimen_types:
                specimen_types[specimen_type] += 1
            else:
                specimen_types[specimen_type] = 1
        
        # Sort by frequency
        sorted_types = sorted(specimen_types.items(), key=lambda x: x[1], reverse=True)
        
        # Check that Blood, Urine, Serum, and Plasma are among the most common types
        top_types = [t[0] for t in sorted_types[:10]]
        self.assertIn("Blood", top_types)
        self.assertIn("Urine", top_types)
        self.assertIn("Serum", top_types)
        self.assertIn("Plasma", top_types)
        
        # Blood should be more common than Urine
        blood_count = specimen_types.get("Blood", 0)
        urine_count = specimen_types.get("Urine", 0)
        self.assertGreater(blood_count, urine_count)

    def test_specimen_types_DE_weighted_distribution(self):
        """Test that German specimen types are distributed according to their weights."""
        # Skip if the file doesn't exist
        specimen_types_file = Path("Core/datamimic_ce/entities/data/medical/specimen_types_DE.csv")
        if not specimen_types_file.exists():
            self.skipTest(f"File {specimen_types_file} does not exist")
        
        # Create a LabTestEntity with DE dataset
        lab_test_entity = LabTestEntity(self.class_factory_util, dataset="DE")
        
        # Generate a large batch of lab tests
        lab_tests = lab_test_entity.generate_batch(500)
        
        # Count the specimen types
        specimen_types = {}
        for test in lab_tests:
            specimen_type = test["specimen_type"]
            if specimen_type in specimen_types:
                specimen_types[specimen_type] += 1
            else:
                specimen_types[specimen_type] = 1
        
        # Sort by frequency
        sorted_types = sorted(specimen_types.items(), key=lambda x: x[1], reverse=True)
        
        # Check that Blut, Urin, Serum, and Plasma are among the most common types
        top_types = [t[0] for t in sorted_types[:10]]
        self.assertIn("Blut", top_types)
        self.assertIn("Urin", top_types)
        self.assertIn("Serum", top_types)
        self.assertIn("Plasma", top_types)
        
        # Blut should be more common than Urin
        blut_count = specimen_types.get("Blut", 0)
        urin_count = specimen_types.get("Urin", 0)
        self.assertGreater(blut_count, urin_count)

    def test_labs_US_weighted_distribution(self):
        """Test that US labs are distributed according to their weights."""
        # Skip if the file doesn't exist
        labs_file = Path("Core/datamimic_ce/entities/data/medical/labs_US.csv")
        if not labs_file.exists():
            self.skipTest(f"File {labs_file} does not exist")
        
        # Create a LabEntity with US dataset
        lab_entity = LabEntity(self.class_factory_util, dataset="US")
        
        # Generate a large batch of labs
        labs = lab_entity.generate_batch(500)
        
        # Count the lab names
        lab_names = {}
        for lab in labs:
            name = lab["name"]
            if name in lab_names:
                lab_names[name] += 1
            else:
                lab_names[name] = 1
        
        # Sort by frequency
        sorted_labs = sorted(lab_names.items(), key=lambda x: x[1], reverse=True)
        
        # Check that Quest Diagnostics and LabCorp are among the most common labs
        top_labs = [l[0] for l in sorted_labs[:5]]
        self.assertIn("Quest Diagnostics", top_labs)
        self.assertIn("LabCorp", top_labs)
        
        # Quest Diagnostics should be more common than LabCorp
        quest_count = lab_names.get("Quest Diagnostics", 0)
        labcorp_count = lab_names.get("LabCorp", 0)
        self.assertGreater(quest_count, labcorp_count)

    def test_labs_DE_weighted_distribution(self):
        """Test that German labs are distributed according to their weights."""
        # Skip if the file doesn't exist
        labs_file = Path("Core/datamimic_ce/entities/data/medical/labs_DE.csv")
        if not labs_file.exists():
            self.skipTest(f"File {labs_file} does not exist")
        
        # Create a LabEntity with DE dataset
        lab_entity = LabEntity(self.class_factory_util, dataset="DE")
        
        # Generate a large batch of labs
        labs = lab_entity.generate_batch(500)
        
        # Count the lab names
        lab_names = {}
        for lab in labs:
            name = lab["name"]
            if name in lab_names:
                lab_names[name] += 1
            else:
                lab_names[name] = 1
        
        # Sort by frequency
        sorted_labs = sorted(lab_names.items(), key=lambda x: x[1], reverse=True)
        
        # Check that Synlab and Labor Berlin are among the most common labs
        top_labs = [l[0] for l in sorted_labs[:5]]
        self.assertIn("Synlab", top_labs)
        self.assertIn("Labor Berlin", top_labs)
        
        # Synlab should be more common than Labor Berlin
        synlab_count = lab_names.get("Synlab", 0)
        labor_berlin_count = lab_names.get("Labor Berlin", 0)
        self.assertGreater(synlab_count, labor_berlin_count)


if __name__ == "__main__":
    unittest.main() 