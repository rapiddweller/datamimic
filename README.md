# **DATAMIMIC Community Edition**

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

Welcome to **DATAMIMIC Community Edition**, the AI-powered platform that revolutionizes test data generation! By leveraging advanced AI and model-driven technologies, DATAMIMIC enables developers and testers to create realistic, scalable, and privacy-compliant test data with ease.

[![Watch the video](https://img.youtube.com/vi/sycO7qd1Bhk/0.jpg)](https://www.youtube.com/watch?v=sycO7qd1Bhk)

---

## Key Features

- 🎯 **Intelligent Data Synthesis**: Generate contextually accurate and logically consistent test data
- 📊 **Multi-Database Support**: Compatible with major databases including PostgreSQL, Oracle, MongoDB, and more
- 🔄 **Flexible Data Formats**: Support for various data formats including CSV, JSON, XML, and SQL
- 📈 **Scalable Performance**: Generate millions of records efficiently with optimized memory usage
- 🎨 **Rich Data Types**: Support for complex data types including dates, addresses, names, and custom patterns
- 🔗 **Relationship Preservation**: Maintain referential integrity and data relationships across tables
- 🛠️ **Command-Line Interface**: Intuitive CLI for easy integration into development workflows
- 📝 **Template-Based Generation**: Create reusable templates for consistent data generation
- 🔍 **Data Validation**: Built-in validation to ensure data quality and consistency
- 🌐 **International Support**: Generate locale-specific data for global testing scenarios
- 🧠 **Model-Driven Generation**: Create realistic test data using sophisticated modeling algorithms
- 🔮 **Pattern Recognition**: Analyze and replicate data patterns for authentic test scenarios
- 🛡️ **Privacy Protection**: Built-in anonymization and pseudonymization for regulatory compliance
- 🚀 **Optimized Performance**: Generate large datasets efficiently with minimal resource usage
- 🐍 **Python Ecosystem**: Seamlessly integrate with Python projects and development workflows
- ⚙️ **Customization**: Flexible architecture supporting custom generators and data types

> **Note:** The Community Edition focuses on core functionalities and does not include AI-powered features like automatic model generation. These advanced features are available in the **Enterprise Edition**.


---

## Why Use DATAMIMIC?

DATAMIMIC revolutionizes test data generation by solving critical challenges that organizations face:

- **Accelerated Development Cycles**: Generate millions of realistic test records in minutes instead of days
- **Enhanced Testing Quality**: Create comprehensive test scenarios with statistically accurate data distributions
- **Robust Data Privacy**: Built-in anonymization ensures GDPR, CCPA, and HIPAA compliance
- **Production-Like Data**: Generate synthetic data that perfectly mimics real production patterns
- **Cost Efficiency**: Eliminate manual data creation and reduce storage costs
- **Risk Mitigation**: Avoid exposing sensitive production data in non-production environments
- **Consistent Quality**: Ensure data consistency across all testing and development phases
- **Global Testing Support**: Generate locale-specific data for international applications

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
            <key name="birthDate" script="person.birthdate" converter="DateFormat('%d.%m.%Y')"/>
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
   {"id": 1, "first_name": "Mary", "last_name": "Mcgowan", "gender": "female", "birthDate": "1946-05-15T00:00:00", "email": "Mcgowan@Mary.de", "ce_user": false, "ee_user": true, "datamimic_lover": "DEFINITELY"},
   {"id": 2, "first_name": "Gabrielle", "last_name": "Malone", "gender": "female", "birthDate": "1989-11-27T00:00:00", "email": "Malone@Gabrielle.de", "ce_user": false, "ee_user": true, "datamimic_lover": "DEFINITELY"},
   {"id": 4, "first_name": "Margaret", "last_name": "Torres", "gender": "female", "birthDate": "2006-07-13T00:00:00", "email": "Torres@Margaret.de", "ce_user": false, "ee_user": false, "datamimic_lover": "DEFINITELY"},
    {"id": 5, "first_name": "Monica", "last_name": "Meyers", "gender": "female", "birthDate": "1983-07-22T00:00:00", "email": "Meyers@Monica.de", "ce_user": true, "ee_user": false, "datamimic_lover": "DEFINITELY"},
    {"id": 6, "first_name": "Jason", "last_name": "Davis", "gender": "male", "birthDate": "1941-07-05T00:00:00", "email": "Davis@Jason.de", "ce_user": true, "ee_user": false, "datamimic_lover": "DEFINITELY"},
    {"...":  "..."},
    {"id": 100, "first_name": "Jared", "last_name": "Rivas", "gender": "male", "birthDate": "1975-03-16T00:00:00", "email": "Rivas@Jared.de", "ce_user": true, "ee_user": true, "datamimic_lover": "DEFINITELY"}
   ]
    ```

    **csv export:**
    ```csv
    id|first_name|last_name|gender|birthDate|email|ce_user|ee_user|datamimic_lover
    1|Mary|Mcgowan|female|1946-05-15 00:00:00|Mcgowan@Mary.de|False|True|DEFINITELY
    2|Gabrielle|Malone|female|1989-11-27 00:00:00|Malone@Gabrielle.de|False|True|DEFINITELY
    3|Antonio|Davis|male|2005-05-12 00:00:00|Davis@Antonio.de|False|True|DEFINITELY
    4|Margaret|Torres|female|2006-07-13 00:00:00|Torres@Margaret.de|False|False|DEFINITELY
    5|Monica|Meyers|female|1983-07-22 00:00:00|Meyers@Monica.de|True|False|DEFINITELY
    ...
    100|Jason|Davis|male|1941-07-05 00:00:00|Davis@Jason.de|True|False|DEFINITELY
    ```


### Advanced Features

DATAMIMIC offers powerful capabilities for sophisticated data generation and management:

Data Generation & Manipulation:
- **Custom Generators**: Build specialized generators tailored to your needs
- **Data Relationships**: Model complex entity relationships and dependencies
- **Model-Driven Generation**: Generate realistic data based on predefined models
- **Data Validation**: Enforce data quality with customizable validation rules

Import/Export Capabilities:
- **Community Edition Formats**:
  - Structured: JSON, XML, CSV
  - Databases: RDBMS (PostgreSQL, Oracle, etc.), MongoDB
- **Enterprise Edition Formats**:
  - Messaging: Apache Kafka
  - Enterprise: EDI, XSD
  - And more...

Security & Integration:
- **Data Anonymization**: Protect sensitive data with robust anonymization techniques
- **Database Integration**: Seamless connectivity with major database systems
- **Scripting Support**: Extend functionality via Python scripting
- **Privacy Compliance**: Built-in tools for GDPR and other privacy regulations

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

Check out our [Contribution Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

DATAMIMIC CE is now open source and licensed under MIT:

- 📄 **Open Source License**: Licensed under the [MIT License](LICENSE)
- 🆓 **Free for Everyone**: Use freely for both personal and commercial projects
- 💡 **Key Permissions**:
  - Commercial use
  - Modification
  - Distribution
  - Private use

For questions or support, contact us at [info@rapiddweller.com](mailto:info@rapiddweller.com).

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
- 🐦 **Twitter**: [@rapiddweller](https://twitter.com/rapiddweller)

---

## Acknowledgments

A big thank you to all our contributors! Your efforts make DATAMIMIC possible.

---

**Don't forget to ⭐ star and 👀 watch this repository to stay updated!**

---

**Legal Notices**

For detailed licensing information, please see the [LICENSE](LICENSE) file.
