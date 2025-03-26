# Healthcare Data Generation with DATAMIMIC

This example demonstrates how to generate synthetic healthcare data using the DATAMIMIC framework.

## Basic Patient Generation

The foundation of healthcare data generation is the `PatientService`:

```python
from datamimic_ce.domains.healthcare.services import PatientService

# Create a service instance
patient_service = PatientService()

# Generate a single patient
patient = patient_service.generate()

# Access patient attributes
print(f"Patient ID: {patient.patient_id}")
print(f"Name: {patient.full_name}")
print(f"Age: {patient.age}")
print(f"Gender: {patient.gender}")
print(f"Blood Type: {patient.blood_type}")
```

Example output:
```
Patient ID: PAT-23AEEABA
Name: Shirley Thompson
Age: 65
Gender: female
Blood Type: AB-
```

## Medical Conditions and Health Data

Patients include realistic medical conditions and health metrics:

```python
# Access medical conditions
print(f"Medical Conditions: {patient.conditions}")

# Access health metrics
print(f"Height: {patient.height_cm} cm")
print(f"Weight: {patient.weight_kg} kg")
print(f"BMI: {patient.bmi}")
```

Example output:
```
Medical Conditions: ['Depression']
Height: 154.8 cm
Weight: 42.4 kg
BMI: 17.7
```

## Insurance Information

Patients come with insurance details:

```python
# Access insurance information
print(f"Insurance Provider: {patient.insurance_provider}")
print(f"Policy Number: {patient.insurance_policy_number}")
```

Example output:
```
Insurance Provider: Tricare
Policy Number: GOP-68961860
```

## Generating Multiple Patients

You can generate multiple patients at once:

```python
# Generate a batch of patients
patients = patient_service.generate_batch(count=5)

# Loop through and access attributes
for i, patient in enumerate(patients):
    print(f"Patient {i+1}: {patient.full_name}, {patient.age} years old, {patient.blood_type}")
```

Example output:
```
Patient 1: Paul Riley, 61 years old, AB-
Patient 2: William Rodriguez, 56 years old, B+
Patient 3: Charles Ortiz, 37 years old, A+
Patient 4: Jessica Williams, 42 years old, O-
Patient 5: Mary Johnson, 29 years old, A+
```

## Working with Doctors

Generate doctor data using the `DoctorService`:

```python
from datamimic_ce.domains.healthcare.services import DoctorService

# Create a doctor service
doctor_service = DoctorService()

# Generate a doctor
doctor = doctor_service.generate()

# Access doctor attributes
print(f"Doctor ID: {doctor.doctor_id}")
print(f"Name: {doctor.full_name}")
print(f"Specialty: {doctor.specialty}")
print(f"Experience: {doctor.years_of_experience} years")
print(f"Medical School: {doctor.medical_school}")
```

Example output:
```
Doctor ID: DOC-4533B6B1
Name: Teresa Gross
Specialty: Obstetrics and Gynecology
Experience: 4 years
Medical School: Duke University School of Medicine
```

## Hospital Information

Generate hospital data using the `HospitalService`:

```python
from datamimic_ce.domains.healthcare.services import HospitalService

# Create a hospital service
hospital_service = HospitalService()

# Generate a hospital
hospital = hospital_service.generate()

# Access hospital attributes
print(f"Hospital: {hospital.name}")
print(f"Type: {hospital.hospital_type}")
print(f"Beds: {hospital.beds}")
```

Example output:
```
Hospital: Cornell Healthcare
Type: Community Hospital
Beds: 349
```

## Electronic Health Records

Generate medical records for patients:

```python
from datamimic_ce.domains.healthcare.services import MedicalRecordService

# Create a medical record service
record_service = MedicalRecordService()

# Generate a medical record for a specific patient
medical_record = record_service.generate(patient_id=patient.patient_id)

# Access medical record attributes
print(f"Record ID: {medical_record.record_id}")
print(f"Patient ID: {medical_record.patient_id}")
print(f"Date: {medical_record.date}")
print(f"Notes: {medical_record.notes[:100]}...")  # Truncated for readability
```

Example output:
```
Record ID: MR-9A76F1C2
Patient ID: PAT-23AEEABA
Date: 2023-11-15 09:45:00
Notes: Patient presents with symptoms of depression. Reports feeling tired constantly and lacking interest in...
```

## Advanced Usage: Creating a Patient Cohort

Create a cohort of patients with specific characteristics:

```python
# Generate elderly patients with diabetes
elderly_diabetic_patients = []

# Generate a larger pool of patients
all_patients = patient_service.generate_batch(count=100)

# Filter for specific criteria
for patient in all_patients:
    if patient.age >= 65 and "Diabetes" in patient.conditions:
        elderly_diabetic_patients.append(patient)

print(f"Found {len(elderly_diabetic_patients)} elderly patients with diabetes")

# Display the first few
for i, patient in enumerate(elderly_diabetic_patients[:3]):
    print(f"Patient {i+1}: {patient.full_name}, {patient.age} years old")
    print(f"  Conditions: {patient.conditions}")
```

Example output:
```
Found 12 elderly patients with diabetes
Patient 1: Robert Johnson, 72 years old
  Conditions: ['Diabetes', 'Hypertension', 'Arthritis']
Patient 2: Margaret Williams, 68 years old
  Conditions: ['Diabetes', 'COPD']
Patient 3: Thomas Smith, 79 years old
  Conditions: ['Diabetes', 'Coronary Artery Disease', 'Chronic Kidney Disease']
```

## Exporting Healthcare Data to CSV

Export a batch of patients to a CSV file:

```python
import csv
from datetime import datetime

# Generate a batch of patients
patients = patient_service.generate_batch(count=10)

# Export to CSV
with open('patients.csv', 'w', newline='') as csvfile:
    fieldnames = ['patient_id', 'name', 'age', 'gender', 'blood_type', 'conditions']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for patient in patients:
        writer.writerow({
            'patient_id': patient.patient_id,
            'name': patient.full_name,
            'age': patient.age,
            'gender': patient.gender,
            'blood_type': patient.blood_type,
            'conditions': ', '.join(patient.conditions)
        })

print("Exported 10 patients to patients.csv")
```

## Creating Related Healthcare Entities

Create a more complete healthcare scenario with related entities:

```python
# Generate a hospital
hospital = hospital_service.generate()

# Generate doctors associated with the hospital
doctors = doctor_service.generate_batch(count=3)

# Generate patients 
patients = patient_service.generate_batch(count=5)

# Print the healthcare ecosystem
print(f"Hospital: {hospital.name}")

print("\nDoctors:")
for doctor in doctors:
    print(f"- {doctor.full_name}, {doctor.specialty}")

print("\nPatients:")
for patient in patients:
    print(f"- {patient.full_name}, {patient.age} years old, Conditions: {patient.conditions}")
```

Example output:
```
Hospital: Memorial Regional Hospital

Doctors:
- Teresa Gross, Obstetrics and Gynecology
- Isaac Kerr, Family Medicine
- Sarah Johnson, Cardiology

Patients:
- Paul Riley, 61 years old, Conditions: ['Depression']
- William Rodriguez, 56 years old, Conditions: ['Hypertension', 'Hyperlipidemia']
- Charles Ortiz, 37 years old, Conditions: ['Asthma']
- Jessica Williams, 42 years old, Conditions: ['Migraine', 'Anxiety']
- Mary Johnson, 29 years old, Conditions: []
```

This demonstrates how DATAMIMIC can generate realistic, related healthcare entities for testing and development. 