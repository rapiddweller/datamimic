# import unittest

# from datamimic_ce.domain_test.common.literal_generators.science_generators import (
#     ChemicalFormulaGenerator,
#     NucleotideSequenceGenerator,
#     ScientificUnitGenerator,
#     UnitType,
#     MetricPrefix,
#     PhysicalConstantGenerator,
# )


# class TestScienceGenerators(unittest.TestCase):
#     """Test suite for science-related generators."""

#     def test_nucleotide_sequence_generator(self):
#         """Test nucleotide sequence generation."""
#         # Test DNA sequence
#         generator = NucleotideSequenceGenerator(sequence_type="DNA", length=20)
#         sequence = generator.generate()
#         self.assertIsInstance(sequence, str)
#         self.assertEqual(len(sequence), 20)
#         self.assertTrue(all(base in "TCGA" for base in sequence))

#         # Test RNA sequence
#         generator = NucleotideSequenceGenerator(sequence_type="RNA", length=15)
#         sequence = generator.generate()
#         self.assertEqual(len(sequence), 15)
#         self.assertTrue(all(base in "UCGA" for base in sequence))

#         # Test invalid sequence type
#         with self.assertRaises(ValueError):
#             NucleotideSequenceGenerator(sequence_type="invalid")

#         # Test minimum length enforcement
#         generator = NucleotideSequenceGenerator(length=0)
#         sequence = generator.generate()
#         self.assertTrue(len(sequence) >= 1)

#     def test_scientific_unit_generator(self):
#         """Test scientific unit generation."""
#         # Test base units without prefix
#         generator = ScientificUnitGenerator(include_prefix=False)
#         unit = generator.generate()
#         self.assertIsInstance(unit, str)
#         self.assertTrue(any(u.value[0] in unit for u in UnitType))

#         # Test units with symbols
#         generator = ScientificUnitGenerator(use_symbol=True, include_prefix=False)
#         unit = generator.generate()
#         self.assertTrue(any(u.value[1] in unit for u in UnitType))

#         # Test specific unit type
#         generator = ScientificUnitGenerator(unit_type="LENGTH", include_prefix=False)
#         unit = generator.generate()
#         self.assertTrue("meter" in unit or "m" in unit)

#         # Test with positive prefixes
#         generator = ScientificUnitGenerator(prefix_sign="positive")
#         unit = generator.generate()
#         self.assertTrue(any(p.value[0] in unit for p in MetricPrefix if p.value[2] > 0))

#         # Test with negative prefixes
#         generator = ScientificUnitGenerator(prefix_sign="negative")
#         unit = generator.generate()
#         self.assertTrue(any(p.value[0] in unit for p in MetricPrefix if p.value[2] < 0))

#         # Test invalid unit type
#         with self.assertRaises(ValueError):
#             ScientificUnitGenerator(unit_type="invalid")

#         # Test invalid prefix sign
#         with self.assertRaises(ValueError):
#             ScientificUnitGenerator(prefix_sign="invalid")

#     def test_chemical_formula_generator(self):
#         """Test chemical formula generation."""
#         # Test simple compounds (complexity 1)
#         generator = ChemicalFormulaGenerator(complexity=1)
#         formula = generator.generate()
#         self.assertIsInstance(formula, str)
#         self.assertTrue(any(formula == compound for compound in generator._common_compounds[1]))

#         # Test medium complexity compounds
#         generator = ChemicalFormulaGenerator(complexity=2)
#         formula = generator.generate()
#         self.assertTrue(any(formula == compound for compound in generator._common_compounds[2]))

#         # Test complex compounds
#         generator = ChemicalFormulaGenerator(complexity=3)
#         formula = generator.generate()
#         self.assertTrue(any(formula == compound for compound in generator._common_compounds[3]))

#         # Test complexity limits
#         generator = ChemicalFormulaGenerator(complexity=0)  # Should be raised to 1
#         formula = generator.generate()
#         self.assertTrue(any(formula == compound for compound in generator._common_compounds[1]))

#         generator = ChemicalFormulaGenerator(complexity=4)  # Should be limited to 3
#         formula = generator.generate()
#         self.assertTrue(any(formula == compound for compound in generator._common_compounds[3]))

#     def test_physical_constant_generator(self):
#         """Test physical constant generation."""
#         # Test full output (name, value, and unit)
#         generator = PhysicalConstantGenerator()
#         constant = generator.generate()
#         self.assertIsInstance(constant, str)
#         # Should contain all parts
#         self.assertTrue(any(c[0] in constant for c in generator._constants))  # Symbol
#         self.assertTrue(any(c[2] in constant for c in generator._constants))  # Value
#         self.assertTrue(any(c[3] in constant for c in generator._constants))  # Unit

#         # Test without value
#         generator = PhysicalConstantGenerator(include_value=False)
#         constant = generator.generate()
#         self.assertTrue(any(c[0] in constant for c in generator._constants))  # Symbol
#         self.assertFalse(any(c[2] in constant for c in generator._constants))  # No value

#         # Test without unit
#         generator = PhysicalConstantGenerator(include_unit=False)
#         constant = generator.generate()
#         self.assertTrue(any(c[0] in constant for c in generator._constants))  # Symbol
#         self.assertFalse(any(c[3] in constant for c in generator._constants))  # No unit

#         # Test name only
#         generator = PhysicalConstantGenerator(include_value=False, include_unit=False)
#         constant = generator.generate()
#         self.assertTrue(any(c[0] in constant for c in generator._constants))  # Symbol
#         self.assertTrue(any(c[1] in constant for c in generator._constants))  # Name
#         self.assertFalse(any(c[2] in constant for c in generator._constants))  # No value
#         self.assertFalse(any(c[3] in constant for c in generator._constants))  # No unit


# if __name__ == "__main__":
#     unittest.main()
