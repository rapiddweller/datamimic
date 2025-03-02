# Medical Record Entity Package

This package provides functionality for generating realistic medical record data. It is structured as a modular package to improve maintainability and extensibility.

## Package Structure

- `__init__.py`: Exports the main classes from the package
- `core.py`: Contains the `MedicalRecordEntity` class that orchestrates the generation of medical record data
- `data_loader.py`: Contains the `MedicalRecordDataLoader` class for loading data from CSV files
- `generators.py`: Contains specialized generator classes for different types of medical record data

## Main Components

### MedicalRecordEntity

The `MedicalRecordEntity` class is the main entry point for generating medical record data. It provides methods and properties for generating various aspects of a medical record, such as:

- Record ID
- Patient and doctor information
- Visit type and chief complaint
- Vital signs
- Diagnoses and procedures
- Medications and lab results
- Allergies
- Assessment and plan
- Follow-up information
- Clinical notes

### MedicalRecordDataLoader

The `MedicalRecordDataLoader` class is responsible for loading data from CSV files. It provides methods for retrieving various types of medical data, such as:

- Visit types
- Chief complaints
- Diagnosis codes
- Procedure codes
- Medications
- Lab tests
- Allergies
- Specimen types
- Labs
- Statuses
- Medical conditions

### Specialized Generators

The package includes several specialized generator classes for different types of medical record data:

- `DiagnosisGenerator`: Generates diagnosis data
- `ProcedureGenerator`: Generates procedure data
- `MedicationGenerator`: Generates medication data
- `LabResultGenerator`: Generates lab result data
- `AllergyGenerator`: Generates allergy data
- `AssessmentGenerator`: Generates assessment data
- `PlanGenerator`: Generates plan data
- `FollowUpGenerator`: Generates follow-up data
- `NotesGenerator`: Generates clinical notes

## Usage Example

```python
from datamimic_ce.entities.healthcare.medical_record_entity import MedicalRecordEntity
from datamimic_ce.class_factory_util import ClassFactoryUtil

# Create a class factory utility
class_factory_util = ClassFactoryUtil()

# Create a medical record entity
medical_record = MedicalRecordEntity(class_factory_util, locale="en_US")

# Generate a single medical record
record_data = medical_record.to_dict()

# Generate a batch of medical records
batch_data = medical_record.generate_batch(count=100)
```

## Data Files

The package relies on CSV data files for generating realistic medical record data. These files should be placed in the appropriate data directory and follow the naming convention `<data_type>_<country_code>.csv`, for example:

- `visit_types_US.csv`
- `chief_complaints_US.csv`
- `diagnosis_codes_US.csv`
- `procedure_codes_US.csv`
- `medications_US.csv`
- `lab_tests_US.csv`
- `allergies_US.csv`
- `specimen_types_US.csv`
- `labs_US.csv`
- `statuses_US.csv`
- `medical_conditions_US.csv`

If a country-specific file is not found, the system will log an error and provide appropriate fallback behavior. 