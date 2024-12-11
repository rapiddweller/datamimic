# **DATAMIMIC Community Edition**

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-≥3.10-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/rapiddweller/datamimic.svg)](https://github.com/rapiddweller/datamimic/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/rapiddweller/datamimic.svg)](https://github.com/rapiddweller/datamimic/network)

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Why Use DATAMIMIC?](#why-use-datamimic)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
- [Examples and Demos](#examples-and-demos)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)
- [Connect with Us](#connect-with-us)
- [FAQ](#faq)
- [Acknowledgments](#acknowledgments)

---

## Introduction

Welcome to **DATAMIMIC Community Edition**, the AI-powered platform that revolutionizes test data generation! By leveraging advanced AI and model-driven technologies, DATAMIMIC enables developers and testers to create realistic, scalable, and privacy-compliant test data with ease.

[![Watch the video](https://img.youtube.com/vi/sycO7qd1Bhk/0.jpg)](https://www.youtube.com/watch?v=sycO7qd1Bhk)

---

## Key Features

- 🧠 **Model-Driven Data Generation**: Utilize sophisticated algorithms to simulate real-world data scenarios.
- 🔮 **AI-Powered Data Generation**: Simulate real-world data scenarios using cutting-edge AI algorithms. (Like GANs, LLMs, and more)
- 🛡️ **Data Privacy Compliance**: Anonymize and pseudonymize data to meet GDPR and global data protection standards.
- 🚀 **High Performance**: Engineered for scalability to handle complex datasets efficiently.
- 🐍 **Seamless Python Integration**: Easily integrate with Python projects and manage dependencies.
- ⚙️ **Extensibility**: Customize and extend functionalities to suit your specific testing needs.

> **Note:** The Community Edition focuses on core functionalities and does not include AI-powered features like automatic model generation. These advanced features are available in the **Enterprise Edition**.


---

## Why Use DATAMIMIC?

Traditional test data generation can be time-consuming and may compromise data privacy. DATAMIMIC addresses these challenges by:

- **Reducing Time-to-Market**: Quickly generate test data without manual intervention.
- **Enhancing Test Coverage**: Simulate diverse data scenarios for comprehensive testing.
- **Ensuring Compliance**: Maintain data privacy and comply with legal regulations.
- **Improving Data Quality**: Generate realistic data that mirrors production environments.

---

## Getting Started

### Prerequisites

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version **3.10** or higher
- **uv Package Manager**: Install from [GitHub](https://github.com/astral-sh/uv)

### Quick Start

Get up and running with DATAMIMIC in just a few steps!

1. **Install uv Package Manager**

   ```bash
   pip install uv
   ```

2. **Clone the Repository**

   ```bash
   git clone https://github.com/rapiddweller/datamimic.git
   cd datamimic
   ```

3. **Install Dependencies**

   ```bash
   uv sync
   ```

4. **Run DATAMIMIC**

   ```bash
   uv run datamimic --help
   ```

5. **Explore Demos**

   List available demos:

   ```bash
   uv run datamimic demo list
   ```

   Run a demo:

   ```bash
   uv run datamimic demo create demo-model
   uv run datamimic run ./demo-model/datamimic.xml
   ```

---

## Examples and Demos

Discover the capabilities of DATAMIMIC through our curated demos:

- **Overview Generators**: Explore available entities and generators.
- **Demo Model**: Generate data using built-in generators and custom datasets.
- **Demo JSON/XML**: Generate and export JSON and XML data.
- **Demo Database**: Connect to databases and perform read/write operations.

Find these and more in the `datamimic_ce/demos` directory.

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

- **Issues**: Open an [issue](https://github.com/rapiddweller/datamimic/issues) on GitHub.
- **Email**: Reach out at [support@rapiddweller.com](mailto:support@rapiddweller.com).

---

## Connect with Us

Stay updated and connect with our community!

- 🌐 **Website**: [www.datamimic.io](https://datamimic.io)
- 🏢 **Rapiddweller**: [www.rapiddweller.com](https://rapiddweller.com)
- 💼 **LinkedIn**: [rapiddweller](https://www.linkedin.com/company/rapiddweller)
- 🐦 **Twitter**: [@rapiddweller](https://twitter.com/rapiddweller)

---

## FAQ

### Q: What Python versions are supported?

**A:** DATAMIMIC requires Python **3.10** or higher.

### Q: How do I install `uv`?

**A:** Install `uv` using `pip`:

```bash
pip install uv
```

or just using `pip`

```bash
pip install datamimic-ce
```

---

## Acknowledgments

A big thank you to all our contributors! Your efforts make DATAMIMIC possible.

---

**Don't forget to ⭐ star and 👀 watch this repository to stay updated!**

---

**Legal Notices**

For detailed licensing information, please see the [LICENSE](LICENSE) file.
