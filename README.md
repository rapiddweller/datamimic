# DATAMIMIC Community Edition 🌟

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-≥3.10-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/rapiddweller/datamimic.svg)](https://github.com/rapiddweller/datamimic/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/rapiddweller/datamimic.svg)](https://github.com/rapiddweller/datamimic/network)
[![PyPI version](https://badge.fury.io/py/datamimic-ce.svg)](https://badge.fury.io/py/datamimic-ce)
[![Downloads](https://pepy.tech/badge/datamimic-ce)](https://pepy.tech/project/datamimic-ce)
---

## Introduction

Welcome to **DATAMIMIC**, the Model-Driven and AI-powered platform that revolutionizes test data generation! By leveraging advanced AI and model-driven technologies, DATAMIMIC enables developers and testers to create realistic, scalable, and privacy-compliant test data with ease.

[![Watch the video](https://img.youtube.com/vi/sycO7qd1Bhk/0.jpg)](https://www.youtube.com/watch?v=sycO7qd1Bhk)

---

## DATAMIMIC Feature Overview 🎯

### Core Features 🔵

#### 🧠 Model-Driven Generation

- Create sophisticated data models for consistent test data generation
- Define complex relationships between entities
- Support for nested and hierarchical data structures

#### 📊 Data Types & Integration

- **Basic Data Types Support**
  - All standard primitive types
  - Complex data structures
  - Custom data type definitions
- **Core Database Integration**
  - RDBMS support (PostgreSQL, MySQL, Oracle)
  - MongoDB integration
  - Basic import/export functionality

#### 🛡️ Data Privacy & Compliance

- GDPR-compliant data anonymization
- Basic pseudonymization capabilities
- Data masking for sensitive information
- Configurable privacy rules

#### ⚡ Core Capabilities

- **High Performance Engine**
  - Optimized for large datasets
  - Parallel processing support
  - Memory-efficient operations
- **Python Integration**
  - Native Python API
  - Seamless dependency management
  - Python script extensions
- **Basic Extensibility**
  - Custom generator support
  - Plugin architecture
  - Basic scripting capabilities

---

### Enterprise Features 🟣

#### 🧠 AI-Powered Generation

- **GAN-based Synthesis**
  - Realistic data patterns
  - Learning from existing datasets
  - Pattern replication
- **LLM Integration**
  - Natural language content
  - Context-aware generation
  - Semantic consistency
- **Automatic Modeling**
  - Schema inference
  - Pattern detection
  - Model optimization

#### 🔗 Advanced Integrations

- **Streaming Support**
  - Kafka integration
  - Real-time data generation
  - Stream processing
- **Enterprise Formats**
  - EDI processing
  - Advanced XSD handling
  - Custom format support
- **Advanced Connectors**
  - Enterprise systems
  - Cloud platforms
  - Legacy systems

#### 🛡️ Enhanced Privacy Features

- **Advanced Anonymization**
  - Context-aware masking
  - Reversible anonymization
  - Custom privacy rules
- **Compliance Tools**
  - Audit logging
  - Compliance reporting
  - Policy enforcement
- **Enterprise Security**
  - Role-based access
  - Encryption support
  - Security audit trails

#### 📈 Advanced Data Validation

- **Validation Framework**
  - Custom rule engines
  - Complex validation logic
  - Cross-field validation

---

## Why Use DATAMIMIC?

Traditional test data generation can be time-consuming and may compromise data privacy. DATAMIMIC addresses these challenges by:

- **Reducing Time-to-Market**: Quickly generate test data without manual intervention.
- **Enhancing Test Coverage**: Simulate diverse data scenarios for comprehensive testing.
- **Ensuring Compliance**: Maintain data privacy and comply with legal regulations.
- **Improving Data Quality**: Generate realistic data that mirrors production environments.
- **Superior Synthetic Data**: Produce synthetic data with higher accuracy than open-source alternatives.

---

## Advanced Features

DATAMIMIC supports a rich set of advanced capabilities:

- **Custom Generators**: Create your own data generators for specialized use cases
- **Data Relationships**: Define complex relationships between entities with referential integrity
- **Import/Export Formats**: Support for JSON, XML, CSV, RDBMS and MongoDB
- **Import/Export Formats (Enterprise Edition)**: Kafka, EDI, XSD and more enterprise formats
- **Data Anonymization**: Anonymize data to comply with privacy regulations while maintaining data utility
- **Data Validation**: Define and enforce data validation rules for consistency
- **Scripting**: Extend functionality using Python scripts for complete flexibility
- **Database Integration**: Connect to databases for seamless data generation and storage
- **Model-Driven Generation**: Utilize models to generate realistic data with proper distributions
- **Weighted Distribution System**: Generate data that follows real-world statistical patterns
- **Multi-Domain Support**: Industry-specific models across healthcare, finance, insurance, and more

---

## Quick Start Guide for Developers

### Installation

Install DATAMIMIC Community Edition using pip:

```bash
pip install datamimic-ce
```

### Method 1: Using Python API

Generate synthetic data directly in your Python code:

```python
# Import the required services
from datamimic_ce.domains.common.services import PersonService
from datamimic_ce.domains.healthcare.services import PatientService
from datamimic_ce.domains.finance.services import BankAccountService

# Generate person data
person_service = PersonService(dataset="US")
person = person_service.generate()

print(f"Person: {person.name}, {person.age} years old")
print(f"Email: {person.email}")
print(f"Address: {person.address.street}, {person.address.city}, {person.address.state}")

# Generate healthcare data
patient_service = PatientService()
patient = patient_service.generate()
print(f"Patient ID: {patient.patient_id}")
print(f"Blood Type: {patient.blood_type}")
print(f"Conditions: {', '.join(patient.conditions)}")

# Generate batch data
people = person_service.generate_batch(count=1000)
print(f"Generated {len(people)} unique people")
```

#### 🚀 Benefits and Use Cases

- **🔧 Direct Control**: Fine-grained programmatic control over data generation
- **🧩 Composable**: Combine different services for complex scenarios
- **🏭 High Volume**: Efficiently generate thousands of records with minimal code
- **🔍 Inspection**: Direct access to object properties for validation
- **🔄 Customization**: Easily modify parameters to suit specific test cases
- **⚡ Performance**: Native Python execution for maximum speed

Perfect for:
- Applications requiring direct integration with Python codebase
- Complex data manipulation scenarios
- When you need full programmatic control
- Scenarios requiring dynamic parameter adjustment
- High-performance data generation requirements

### Method 2: Using XML Configuration

Create a data model in XML format (`datamimic.xml`):

```xml
<setup>
    <generate name="datamimic_user_list" count="100" target="CSV,JSON">
        <variable name="person" entity="Person(min_age=18, max_age=90, female_quota=0.5)"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="given_name" script="person.given_name"/>
        <key name="family_name" script="person.family_name"/>
        <key name="gender" script="person.gender"/>
        <key name="birth_date" script="person.birthdate" converter="DateFormat('%d.%m.%Y')"/>
        <key name="email" script="person.family_name + '@' + person.given_name + '.de'"/>
        <key name="ce_user" values="True, False"/>
        <key name="ee_user" values="True, False"/>
        <key name="datamimic_lover" constant="DEFINITELY"/>
    </generate>
</setup>
```

Then generate the data using the command line:

```bash
datamimic run datamimic.xml
```

#### 🚀 Benefits and Use Cases

- **📝 Declarative**: Define your data requirements in a clear, declarative format
- **🔄 Reusable**: Create templates that can be reused across projects
- **🔌 Portable**: XML definitions work across different environments
- **🧰 Tooling**: Compatible with XML editors and validation tools
- **📊 Output Flexibility**: Generate multiple output formats from a single definition
- **🔒 Stability**: Consistent outputs across runs

Perfect for:
- Configuration-driven applications
- CI/CD pipeline integration
- Cross-language environments
- When separation of code and data definitions is needed
- Scenarios requiring multiple output formats

### Method 3: Generate Complex Related Data

You can create realistic scenarios with related entities:

```python
# Import required services
from datamimic_ce.domains.healthcare.services import PatientService, DoctorService, HospitalService

# Create the services
hospital_service = HospitalService()
doctor_service = DoctorService()
patient_service = PatientService()

# Generate related entities
hospital = hospital_service.generate()
doctors = doctor_service.generate_batch(count=5)
patients = patient_service.generate_batch(count=20)

# Create relationships
for doctor in doctors:
    doctor.hospital = hospital
    
for patient in patients:
    patient.primary_doctor = doctors[0]  # Assign the first doctor to all patients
    
# Print the relationships
print(f"Hospital: {hospital.name}")
print(f"Doctors ({len(doctors)}):")
for doctor in doctors:
    print(f"  - Dr. {doctor.family_name}, {doctor.specialty}")
    
print(f"Patients ({len(patients)}):")
for i, patient in enumerate(patients[:5]):  # Show just the first 5
    print(f"  - {patient.given_name} {patient.family_name} (Patient ID: {patient.patient_id})")
if len(patients) > 5:
    print(f"  - And {len(patients) - 5} more patients...")
```

#### 🚀 Benefits and Use Cases

- **🔗 Relationships**: Create complex, interconnected data relationships
- **🧩 Entity Graphs**: Build complete entity graphs with referential integrity
- **🌐 Ecosystem**: Model entire business domains in a single setup
- **📊 Real-world Modeling**: Simulate realistic business scenarios
- **🧪 End-to-End Testing**: Test complex business rules across related entities
- **🔍 Data Consistency**: Ensure consistent relationships across your test data

Perfect for:
- Complex domain modeling
- Database schema validation
- Microservice integration testing
- Business logic validation across entity boundaries
- Scenarios requiring realistic data relationships

### Method 4: Custom Domain Factory

Create a factory for test-specific data generation with the `DataMimicTestFactory`:

**customer.xml**:
```xml
<setup>
    <!-- customer.xml -->
    <generate name="customer" count="10">
        <!-- Basic customer info -->
        <variable name="person" entity="Person(min_age=21, max_age=67)"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="first_name" script="person.given_name"/>
        <key name="last_name" script="person.family_name"/>
        <key name="email" script="person.email"/>
        <key name="status" values="'active', 'inactive', 'pending'"/>
    </generate>
</setup>
```

```python
from datamimic_ce.factory.datamimic_test_factory import DataMimicTestFactory

customer_factory = DataMimicTestFactory("customer.xml", "customer")
customer = customer_factory.create()

print(customer["id"])  # 1
print(customer["first_name"])  # Jose
print(customer["last_name"])   # Ayers
```

#### 🚀 Benefits and Use Cases

- **🧪 Testing Focus**: Simplified API designed specifically for testing scenarios
- **🔄 Dictionary Access**: Easy access to generated data through dictionary-like interface
- **📝 Test Fixtures**: Create consistent test fixtures for unit and integration tests
- **🧩 Factory Pattern**: Implements the factory pattern for test data generation
- **📊 Deterministic Output**: Predictable outputs for repeatable test scenarios
- **🚀 Productivity**: Rapid test data creation with minimal setup
- **🏗️ Test Architecture**: Clean separation between test data and test logic
- **🌱 Maintainability**: Centralized data definition for easier updates

Perfect for:
- Unit testing with consistent test data
- Integration testing with complex business rules
- Test-driven development (TDD) workflows
- Creating pre-configured test fixtures
- Simplifying test setup with one-line data generation
- Projects requiring standardized test data across multiple test suites
- Keeping test data definitions separate from test logic
- Rapid development of test scenarios

---

## Documentation

For comprehensive documentation, please visit:

- [Main Documentation](docs/README.md) - Overview and getting started guide
- [Domain-Driven Framework](docs/data-domains/README.md) - Documentation for domain-specific data generation
- [API Reference](docs/api/) - Detailed API documentation
- [Advanced Topics](docs/advanced/) - Advanced usage and customization

---

## Installation

### Prerequisites

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version **3.10** or higher
- **Optional**: uv Package Manager for development setup [GitHub](https://github.com/astral-sh/uv)

### User Installation

The simplest way to get started with DATAMIMIC is through pip:

```bash
pip install datamimic-ce
```

Verify the installation:

```bash
datamimic version
```

### Developer Installation

For contributors and developers who want to work with the source code:

1. Install uv Package Manager:

    ```bash
    pip install uv
    ```

2. Clone and set up the repository:

    ```bash
    git clone https://github.com/rapiddweller/datamimic.git
    cd datamimic
    uv sync
    ```

---

## Examples and Demos

Explore our demo collection:

```bash
# List available demos
datamimic demo list

# Run a specific demo
datamimic demo create demo-model
datamimic run ./demo-model/datamimic.xml
```

Key demos include:

- Basic entity generation
- Complex relationships
- Database integration
- Custom generator creation
- Privacy compliance examples

Find more examples in the `datamimic_ce/demos` directory.

---

## Contributing

We ❤️ contributions! Here's how you can help:

- **Code Contributions**: Submit pull requests for new features or bug fixes.
- **Documentation**: Improve existing docs or help with translations.
- **Community Engagement**: Join discussions and support other users.

---

## 📜 DATAMIMIC Licensing Options

### 🌟 Community Edition

Open Source Freedom for Everyone

#### ✨ Key Benefits

- **🔓 MIT License**: Maximum freedom for innovation
- **💼 Commercial Ready**: Use freely in commercial projects
- **🔄 Modification Rights**: Full source code access and modification rights
- **🌍 No Restrictions**: Deploy anywhere, anytime

#### 🎁 What's Included

- **📦 Core Features**
  - Model-driven data generation
  - Basic data types & integrations
  - GDPR compliance tools
  
- **👥 Community Support**
  - Active GitHub community
  - Public issue tracking
  - Community discussions
  - Regular updates

#### 💫 Perfect For

- Individual developers
- Startups & small teams
- Open source projects
- Learning & evaluation
- POC development

---

### ⭐ Enterprise Edition

Professional Power for Business Success

#### 🚀 Premium Benefits

- **📋 Commercial License**: Enterprise-grade flexibility
- **🔐 Advanced Features**: Full suite of professional tools
- **🎯 Priority Support**: Direct access to expert team
- **🛠️ Custom Solutions**: Tailored to your needs

#### 💎 Premium Features

- **🤖 AI Capabilities**
  - GAN-based synthesis
  - LLM integration
  - Automated modeling
  
- **🔗 Enterprise Integration**
  - Advanced connectors
  - Kafka streaming
  - EDI support
  
- **🛡️ Enhanced Security**
  - Advanced privacy features
  - Compliance reporting
  - Audit trails

#### 🎯 Ideal For

- Large enterprises
- Financial institutions
- Healthcare organizations
- Government agencies
- High-compliance industries

#### 📞 Get Started
>
> Ready to unlock the full potential of DATAMIMIC?

**Contact Our Team:**

- 📧 Email: [sales@rapiddweller.com](mailto:sales@rapiddweller.com)
- 🌐 Visit: [datamimic.io/enterprise](https://datamimic.io)

---

### 🤝 Compare Editions

| Feature | Community | Enterprise |
|---------|-----------|------------|
| Base Features | ✅ | ✅ |
| Source Code Access | ✅ | ✅ |
| Commercial Use | ✅ | ✅ |
| AI Features | ❌ | ✅ |
| Priority Support | ❌ | ✅ |
| Enterprise Integrations | ❌ | ✅ |
| SLA Support | ❌ | ✅ |
| Custom Development | ❌ | ✅ |
| Superior Synthetic Data Quality | ❌ | ✅ |

---

> ***"Empower your data generation journey with the right DATAMIMIC edition for your needs"***

---

## Support

Need help or have questions? We're here for you!

- 📚 [Documentation](https://docs.datamimic.io)
- 💬 [GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions)
- 🐛 [Issue Tracker](https://github.com/rapiddweller/datamimic/issues)
- 📧 [Email Support](mailto:support@rapiddweller.com)

---

## Connect with Us

Stay updated and connect with our community!

- 🌐 **Website**: [www.datamimic.io](https://datamimic.io)
- 🏢 **Rapiddweller**: [www.rapiddweller.com](https://rapiddweller.com)
- 💼 **LinkedIn**: [rapiddweller](https://www.linkedin.com/company/rapiddweller)

---

## Acknowledgments

A big thank you to all our contributors! Your efforts make DATAMIMIC possible.

---

**Don't forget to ⭐ star and 👀 watch this repository to stay updated!**

---

## Legal Notices

For detailed licensing information, please see the [LICENSE](LICENSE) file.
