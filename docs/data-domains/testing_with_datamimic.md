# Testing with DATAMIMIC

> **Note:** This documentation focuses specifically on using DATAMIMIC's Domain-Driven Framework for unit testing. DATAMIMIC has many additional capabilities beyond what is documented here.

## Advantages for Testing

DATAMIMIC offers several advantages for unit testing:

1. **Domain-specific test data**: Generate realistic test entities that match your business domains
2. **Consistent relationships**: Related entities maintain logical consistency
3. **Controllable randomness**: Get different data on each test run, but control it when needed
4. **Reduced test maintenance**: Tests don't break when data schemas change
5. **Better test coverage**: Automatic generation of edge cases and diverse scenarios

## First Steps

Install DATAMIMIC to get started:

```bash
pip install datamimic-ce
```

## Basic Testing Pattern

Here's a simple example of using DATAMIMIC to test a healthcare service:

```python
import unittest
from datamimic_ce.domains.healthcare.services.patient_service import PatientService
from your_app.services.medical_billing import calculate_insurance_coverage

class TestMedicalBilling(unittest.TestCase):
    def setUp(self):
        # Create a service to generate test data
        self.patient_service = PatientService()
        
    def test_insurance_coverage_calculation(self):
        # Generate a test patient with realistic medical data
        patient = self.patient_service.generate()
        
        # Test your application code with the generated data
        coverage_amount = calculate_insurance_coverage(
            patient.insurance_provider,
            patient.insurance_policy_number,
            patient.conditions
        )
        
        # Assert expected behavior
        self.assertIsInstance(coverage_amount, float)
        self.assertGreaterEqual(coverage_amount, 0)
        
    def test_multiple_patients_billing(self):
        # Generate multiple test patients
        patients = self.patient_service.generate_batch(10)
        
        # Test your code with a batch of patients
        for patient in patients:
            coverage = calculate_insurance_coverage(
                patient.insurance_provider,
                patient.insurance_policy_number,
                patient.conditions
            )
            self.assertIsInstance(coverage, float)
```

## Testing with Fixed Data

When you need deterministic tests:

```python
import unittest
from datamimic_ce.domains.healthcare.services.patient_service import PatientService

class TestPatientProcessing(unittest.TestCase):
    def test_with_deterministic_data(self):
        # Create service with a fixed seed for reproducible results
        patient_service = PatientService(seed=12345)
        
        # This will generate the same patient data every time
        patient = patient_service.generate()
        
        # Your test code here...
```

## Mocking External Services

DATAMIMIC is perfect for mocking API responses:

```python
from unittest.mock import patch
from datamimic_ce.domains.financial.services.bank_account_service import BankAccountService

class TestBankAPI:
    @patch('your_app.services.bank_api.get_account_details')
    def test_account_processing(self, mock_get_account):
        # Generate realistic mock data
        account_service = BankAccountService()
        mock_account = account_service.generate()
        
        # Configure the mock to return our generated data
        mock_get_account.return_value = mock_account.to_dict()
        
        # Test your code that calls the API
        # ...
```

## Testing Edge Cases

Generate specific edge cases for thorough testing:

```python
from datamimic_ce.domains.healthcare.services.patient_service import PatientService

# Generate elderly patients for testing age-specific rules
elderly_patient_service = PatientService(min_age=65, max_age=100)
elderly_patients = elderly_patient_service.generate_batch(5)

# Test with specific conditions
cardiac_patient_service = PatientService(
    conditions=["Coronary Artery Disease", "Hypertension"]
)
cardiac_patient = cardiac_patient_service.generate()
```

## Property-Based Testing

Combine DATAMIMIC with property-based testing frameworks:

```python
import hypothesis
from hypothesis import given
from datamimic_ce.domains.healthcare.services.patient_service import PatientService

# Create a service to use in our tests
patient_service = PatientService()

@given(hypothesis.strategies.integers(min_value=1, max_value=100))
def test_patient_batch_generation(count):
    """Test that we can generate any number of patients."""
    patients = patient_service.generate_batch(count)
    assert len(patients) == count
    for patient in patients:
        assert patient.patient_id is not None
        assert patient.medical_record_number is not None
```

## Integration Testing

Use DATAMIMIC for integration tests with databases:

```python
import pytest
from datamimic_ce.domains.common.services.person_service import PersonService
from your_app.database import db_session
from your_app.models import User

@pytest.fixture
def populated_database():
    # Generate test users
    person_service = PersonService()
    people = person_service.generate_batch(10)
    
    # Add to test database
    for person in people:
        user = User(
            username=person.email.split('@')[0],
            email=person.email,
            full_name=person.name
        )
        db_session.add(user)
    db_session.commit()
    
    yield db_session
    
    # Cleanup
    db_session.query(User).delete()
    db_session.commit()

def test_user_search(populated_database):
    # Your integration test using the populated database
    # ...
```

## Best Practices

1. **Create service instances in setUp methods** for test classes
2. **Use seed values** when you need reproducible results
3. **Generate related entities together** to maintain consistency
4. **Leverage domain-specific services** that match your business logic
5. **Combine with property-based testing** for thorough test coverage

## Testing Against Production-Like Data

Use DATAMIMIC to generate synthetic datasets that closely resemble your production data:

```python
# Configure distribution parameters based on production statistics
patient_service = PatientService(
    dataset="US",
    female_quota=0.52,  # Matches our production gender distribution
    min_age=30,         # Matches our customer demographic
    max_age=75          # Matches our customer demographic
)

# Generate a large dataset for testing
patients = patient_service.generate_batch(count=10000)

# Save to test database
for patient in patients:
    db.session.add(patient.to_db_model())
db.session.commit()

# Run tests against this dataset
```

## Conclusion

DATAMIMIC's domain-driven approach to synthetic data generation makes it an excellent tool for testing at all levels. By providing realistic, coherent data that follows real-world distributions, DATAMIMIC helps ensure your tests accurately reflect the conditions your software will face in production. 