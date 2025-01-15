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
datamimic --version
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

## Usage Guide

### Basic Usage

1. Create a new data generation project:

    ```bash
    datamimic init my-project
    cd my-project
    ```

2. Configure your data model in `datamimic.xml`:

    ```xml
    <setup>
        <generate name="datamimic_user_list" count="100" target="CSV,JSON">
            <variable name="person" entity="Person(min_age=18, max_age=90, female_quota=0.5)"/>
            <key name="id" generator="IncrementGenerator"/>
            <key name="first_name" script="person.given_name"/>
            <key name="last_name" script="person.family_name"/>
            <key name="gender" script="person.gender"/>
            <key name="birth_date" script="person.birthdate" converter="DateFormat('%d.%m.%Y')"/>
            <key name="email" script="person.family_name + '@' + person.given_name + '.de'"/>
            <key name="ce_user" values="True, False"/>
            <key name="ee_user" values="True, False"/>
            <key name="datamimic_lover" constant="DEFINITELY"/>
        </generate>
    </setup>
    ```

3. Generate data:

    ```bash
    datamimic run datamimic.xml
    ```

4. Access the generated data in the `output` directory.

    **json export:**

    ```json
   [
   {"id": 1, "first_name": "Mary", "last_name": "Mcgowan", "gender": "female", "birth_date": "1946-05-15T00:00:00", "email": "Mcgowan@Mary.de", "ce_user": false, "ee_user": true, "datamimic_lover": "DEFINITELY"},
   {"id": 2, "first_name": "Gabrielle", "last_name": "Malone", "gender": "female", "birth_date": "1989-11-27T00:00:00", "email": "Malone@Gabrielle.de", "ce_user": false, "ee_user": true, "datamimic_lover": "DEFINITELY"},
   {"id": 4, "first_name": "Margaret", "last_name": "Torres", "gender": "female", "birth_date": "2006-07-13T00:00:00", "email": "Torres@Margaret.de", "ce_user": false, "ee_user": false, "datamimic_lover": "DEFINITELY"},
    {"id": 5, "first_name": "Monica", "last_name": "Meyers", "gender": "female", "birth_date": "1983-07-22T00:00:00", "email": "Meyers@Monica.de", "ce_user": true, "ee_user": false, "datamimic_lover": "DEFINITELY"},
    {"id": 6, "first_name": "Jason", "last_name": "Davis", "gender": "male", "birth_date": "1941-07-05T00:00:00", "email": "Davis@Jason.de", "ce_user": true, "ee_user": false, "datamimic_lover": "DEFINITELY"},
    {"...":  "..."},
    {"id": 100, "first_name": "Jared", "last_name": "Rivas", "gender": "male", "birth_date": "1975-03-16T00:00:00", "email": "Rivas@Jared.de", "ce_user": true, "ee_user": true, "datamimic_lover": "DEFINITELY"}
   ]
    ```

    **csv export:**

    ```csv
    id|first_name|last_name|gender|birth_date|email|ce_user|ee_user|datamimic_lover
    1|Mary|Mcgowan|female|1946-05-15 00:00:00|Mcgowan@Mary.de|False|True|DEFINITELY
    2|Gabrielle|Malone|female|1989-11-27 00:00:00|Malone@Gabrielle.de|False|True|DEFINITELY
    3|Antonio|Davis|male|2005-05-12 00:00:00|Davis@Antonio.de|False|True|DEFINITELY
    4|Margaret|Torres|female|2006-07-13 00:00:00|Torres@Margaret.de|False|False|DEFINITELY
    5|Monica|Meyers|female|1983-07-22 00:00:00|Meyers@Monica.de|True|False|DEFINITELY
    ...
    100|Jason|Davis|male|1941-07-05 00:00:00|Davis@Jason.de|True|False|DEFINITELY
    ```

### Advanced Features

DATAMIMIC supports various advanced features:

- **Custom Generators**: Create your own data generators
- **Data Relationships**: Define complex relationships between entities
- **Import/Export Formats**: Support for JSON, XML, CSV, RDBMS and MongoDB
- **Import/Export Formats ( only EE )**: Kafka, EDI, XSD and more
- **Data Anonymization**: Anonymize data to comply with privacy regulations
- **Data Validation**: Define and enforce data validation rules
- **Scripting**: Extend functionality using Python scripts
- **Database Integration**: Connect to databases for seamless data generation
- **Model-Driven Generation**: Utilize models to generate realistic data
- **Validation Rules**: Define and enforce data validation rules
- **Scripting**: Extend functionality using Python scripts

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
