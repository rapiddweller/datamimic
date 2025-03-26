# Person Generation with DATAMIMIC

This example demonstrates how to generate synthetic person data using the DATAMIMIC framework.

## Basic Person Generation

The most straightforward way to generate a person is using the `PersonService`:

```python
from datamimic_ce.domains.common.services import PersonService

# Create a service instance
person_service = PersonService(dataset="US")  # Specify locale/dataset

# Generate a single person
person = person_service.generate()

# Access basic person attributes
print(f"Name: {person.name}")
print(f"Age: {person.age}")
print(f"Gender: {person.gender}")
print(f"Email: {person.email}")
```

Example output:
```
Name: Mary Preston
Age: 48
Gender: female
Email: mpreston@kiigyibcrcw.at
```

## Accessing Address Information

Person entities include detailed address information:

```python
# Access address attributes
address = person.address
print(f"Street: {address.street}")
print(f"City: {address.city}")
print(f"State: {address.state}")
print(f"Zip: {address.zip}")
print(f"Country: {address.country}")
```

Example output:
```
Street: 5th Street
City: Canton
State: OH
Zip: 44702
Country: United States
```

## Generating Multiple People

You can generate multiple people at once using the `generate_batch` method:

```python
# Generate a batch of people
people = person_service.generate_batch(count=5)

# Loop through and access attributes
for i, person in enumerate(people):
    print(f"Person {i+1}: {person.name}, {person.age} years old")
```

Example output:
```
Person 1: George Smith, 29 years old
Person 2: Victoria Buchanan, 56 years old
Person 3: Jessica Lee, 35 years old
Person 4: William Davis, 42 years old
Person 5: Susan Johnson, 31 years old
```

## Working with Different Locales

DATAMIMIC supports generating data for different regions by specifying the dataset:

```python
# Create services for different regions
us_service = PersonService(dataset="US")
uk_service = PersonService(dataset="UK")
ca_service = PersonService(dataset="CA")  # Canada

# Generate people from different regions
us_person = us_service.generate()
uk_person = uk_service.generate()
ca_person = ca_service.generate()

print(f"US Person: {us_person.name}, {us_person.address.state}")
print(f"UK Person: {uk_person.name}, {uk_person.address.state}")
print(f"CA Person: {ca_person.name}, {ca_person.address.state}")
```

Example output:
```
US Person: Robert Suarez, NY
UK Person: Emma Wilson, London
CA Person: Jacques Tremblay, ON
```

## Exporting to Different Formats

### Converting to Dictionary

```python
# Convert to dictionary
person_dict = person.to_dict()
print(person_dict)
```

### Converting to JSON

```python
import json
from datetime import datetime

# Create a JSON encoder for datetime objects
class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Convert to JSON
person_json = json.dumps(person.to_dict(), cls=DatetimeEncoder, indent=2)
print(person_json)
```

Example output:
```json
{
  "birthdate": "1976-03-15T14:22:18",
  "given_name": "Robert",
  "family_name": "Suarez",
  "gender": "male",
  "name": "Robert Suarez",
  "age": 48,
  "email": "robert_suarez@objectflash.ch",
  "phone": "+1-555-123-4567",
  "address": {
    "street": "Cedar Street",
    "city": "Albany",
    "state": "NY",
    "zip": "12205",
    "country": "United States"
  }
}
```

## Advanced Usage: Customizing Generation

You can customize the generation process by providing specific parameters:

```python
# Generate a person with specific characteristics
custom_person = person_service.generate(
    gender="female",
    age_range=(25, 35)  # Only generate people between 25-35
)

print(f"Custom Person: {custom_person.name}, {custom_person.age} years old, {custom_person.gender}")
```

Example output:
```
Custom Person: Jennifer Williams, 29 years old, female
```

## Integration with Other Domains

Person entities can be used as the foundation for other domain-specific entities:

```python
from datamimic_ce.domains.healthcare.services import PatientService
from datamimic_ce.domains.finance.services import CustomerService

# Generate domain-specific entities based on people
patient_service = PatientService()
patient = patient_service.generate()

customer_service = CustomerService()
customer = customer_service.generate()

print(f"Patient: {patient.full_name}, ID: {patient.patient_id}")
print(f"Customer: {customer.full_name}, ID: {customer.customer_id}")
```

Example output:
```
Patient: Paul Riley, ID: PAT-13FDBE18
Customer: Sarah Johnson, ID: CUST-A7C42F19
```

## Processing Batch Data

You can process batch-generated data efficiently:

```python
# Generate a batch of people
people = person_service.generate_batch(count=100)

# Filter for specific criteria
seniors = [p for p in people if p.age >= 65]
young_adults = [p for p in people if 18 <= p.age < 30]

print(f"Generated {len(people)} people")
print(f"Seniors: {len(seniors)} ({len(seniors)/len(people)*100:.1f}%)")
print(f"Young Adults: {len(young_adults)} ({len(young_adults)/len(people)*100:.1f}%)")
```

Example output:
```
Generated 100 people
Seniors: 17 (17.0%)
Young Adults: 23 (23.0%)
```

This distribution reflects realistic demographic patterns due to DATAMIMIC's weighted datasets. 