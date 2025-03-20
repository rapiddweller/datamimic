# DataMimic Entity Domains

This document describes the various domains available in DataMimic and the entities contained within each domain.

## Domain Overview

DataMimic organizes entities into logical domains based on their business function:

| Domain        | Description                                 | Key Entities                                  |
|---------------|---------------------------------------------|-----------------------------------------------|
| Common        | Generally useful entities                   | Person, Address, Company, City, Country       |
| Healthcare    | Medical and healthcare entities             | Patient, Doctor, Hospital, MedicalDevice      |
| Finance       | Financial services entities                 | BankAccount, CreditCard, Transaction, Payment |
| Ecommerce     | Online shopping and retail                  | Product, Order, UserAccount, CRM              |
| Insurance     | Insurance industry entities                 | InsurancePolicy, InsuranceCompany             |
| Public Sector | Government and public administration        | AdministrationOffice, EducationalInstitution  |

## Domain Descriptions

### Common Domain

The common domain contains entities that are widely used across different business domains:

- **Person**: Individual people with demographics, contact info, and personal details
- **Address**: Physical locations with street, city, state, zip code, etc.
- **Company**: Business organizations with name, contact, sector, etc.
- **City**: Geographic city information with population, coordinates, etc.
- **Country**: Country-level information with codes, names, populations, etc.

These entities form the foundation for other domain-specific entities, which often reference or extend them.

### Healthcare Domain

The healthcare domain contains medical and healthcare-related entities:

- **Patient**: Individuals receiving medical care (extends Person)
- **Doctor**: Medical professionals (extends Person)
- **Hospital**: Medical facilities with departments, staff, etc.
- **MedicalDevice**: Equipment used in medical procedures
- **MedicalRecord**: Patient health records and history
- **MedicalProcedure**: Specific medical interventions
- **LabTest**: Laboratory-based diagnostic procedures
- **ClinicalTrial**: Research studies for medical treatments

### Finance Domain

The finance domain contains banking and financial services entities:

- **BankAccount**: Account information with balances, types, etc.
- **CreditCard**: Payment card details
- **Transaction**: Financial movements between accounts
- **Payment**: Specific payment instances
- **Invoice**: Billing documents
- **Bank**: Financial institutions
- **DigitalWallet**: Electronic payment systems

### Ecommerce Domain

The ecommerce domain contains online shopping and retail entities:

- **Product**: Items for sale with descriptions, prices, etc.
- **Order**: Purchase orders with items, totals, etc.
- **UserAccount**: Customer accounts
- **CRM**: Customer relationship management data

### Insurance Domain

The insurance domain contains insurance industry entities:

- **InsurancePolicy**: Policy contracts with terms, coverage, etc.
- **InsuranceCompany**: Insurance providers
- **InsuranceProduct**: Specific insurance offerings
- **Claim**: Insurance claims and processing data

### Public Sector Domain

The public sector domain contains government and public administration entities:

- **AdministrationOffice**: Government offices and agencies
- **EducationalInstitution**: Schools, colleges, universities
- **PoliceOfficer**: Law enforcement personnel (extends Person)

## Cross-Domain Relationships

Many entities have relationships with entities in other domains:

- A **Patient** (Healthcare) extends **Person** (Common)
- A **Doctor** (Healthcare) extends **Person** (Common) and works at a **Hospital** (Healthcare)
- A **Product** (Ecommerce) may be a **MedicalDevice** (Healthcare)
- An **Invoice** (Finance) may reference an **Order** (Ecommerce)
- A **Company** (Common) may be an **InsuranceCompany** (Insurance)

These relationships allow for complex, realistic data generation scenarios.

## Adding New Domains

DataMimic supports adding new domains to meet specific business needs:

1. Create a new domain package under `datamimic_ce/domains/`
2. Follow the standard domain structure (models, data_loaders, etc.)
3. Implement domain-specific entities following the entity implementation guide
4. Register the new entities in the entity mapping

## Domain-Specific Customizations

Each domain may have specific customizations:

- **Healthcare**: ICD codes, medical terminology, procedure workflows
- **Finance**: Currency handling, transaction rules, account types
- **Ecommerce**: Product categories, shipping options, pricing models
- **Insurance**: Risk scoring, policy types, coverage calculations
- **Public Sector**: Jurisdiction types, regulatory frameworks

These domain-specific elements are implemented in the respective domain packages.

## Using Multiple Domains

XML configurations can combine entities from multiple domains:

```xml
<generate name="PatientWithInsurance" count="10">
    <variable name="patient" entity="Patient" dataset="US" />
    <variable name="policy" entity="InsurancePolicy" dataset="US" />
    <key name="patient_id" script="patient.id" />
    <key name="patient_name" script="patient.full_name" />
    <key name="policy_id" script="policy.id" />
    <key name="policy_type" script="policy.type" />
    <key name="premium" script="policy.premium" />
</generate>
```

This generates combined data from the Healthcare and Insurance domains.