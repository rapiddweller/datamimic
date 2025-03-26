# DATAMIMIC Community Edition 🌟

[![Maintainability](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rapiddweller_datamimic&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rapiddweller_datamimic)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-≥3.10-blue.svg)](https://www.python.org/downloads/)

---

## 🚀 Quick Intro

**DATAMIMIC** is an AI-powered, model-driven test data generation platform designed to quickly deliver realistic, privacy-compliant synthetic data. 

✅ **Model-driven** | ✅ **AI-ready** | ✅ **Privacy-focused** | ✅ **Open Source (MIT)**

📞 **[Book your Free Strategy Call and Demo](https://datamimic.io/contact)** to explore the full power of our Enterprise solution!

---

## 🟢 Community vs 🟣 Enterprise Editions

| Feature                        | Community | Enterprise |
|--------------------------------|-----------|------------|
| Core Model-driven Generation   | ✅        | ✅         |
| Python & XML APIs              | ✅        | ✅         |
| Basic Anonymization            | ✅        | ✅         |
| AI-Enhanced Data Generation    | ❌        | ✅         |
| Advanced Enterprise Integrations | ❌      | ✅         |
| Priority Support & SLA         | ❌        | ✅         |

👉 [Learn more about Enterprise Edition](https://datamimic.io)

---

## 📦 Installation

Install easily via pip:

```bash
pip install datamimic-ce
```

Verify installation:

```bash
datamimic version
```

---

## ⚡ Quick Start

Generate realistic data effortlessly:

**Python Example:**

```python
from datamimic_ce.domains.common.services import PersonService

person_service = PersonService(dataset="US")
person = person_service.generate()

print(f"Person: {person.name}, Email: {person.email}")
```

**XML Example:**

```xml
<setup>
  <generate name="user_data" count="10" target="CSV">
    <key name="name" entity="Person().name"/>
    <key name="email" entity="Person().email"/>
  </generate>
</setup>
```

Run XML via CLI:

```bash
datamimic run datamimic.xml
```

---

### ⚙️ Custom Domain Factory Example

Quickly generate test-specific data using `DataMimicTestFactory`:

**customer.xml:**

```xml
<setup>
    <generate name="customer" count="10">
        <variable name="person" entity="Person(min_age=21, max_age=67)"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="first_name" script="person.given_name"/>
        <key name="last_name" script="person.family_name"/>
        <key name="email" script="person.email"/>
        <key name="status" values="'active', 'inactive', 'pending'"/>
    </generate>
</setup>
```

**Python Usage:**

```python
from datamimic_ce.factory.datamimic_test_factory import DataMimicTestFactory

customer_factory = DataMimicTestFactory("customer.xml", "customer")
customer = customer_factory.create()

print(customer["id"])  # 1
print(customer["first_name"])  # Jose
print(customer["last_name"])   # Ayers
```

---

## 🎯 Why DATAMIMIC?

- 🚀 **Accelerate Development**: Instantly create test data.
- 🛡️ **Privacy First**: Built-in GDPR compliance.
- 📊 **Realistic Data**: Authentic, weighted distributions from various data domains.
- 🔧 **High Flexibility**: Easily model, standardize, and customize data generation processes.
- 📥📤 **Versatile Sources**: Extensive import/export capabilities (JSON, XML, CSV, RDBMS, MongoDB, etc.).
- 🗃️ **Metadata-Driven**: Operate seamlessly with an integrated metadata model.

---

## 🌐 Documentation & Demos

- 📚 [Full Documentation](https://docs.datamimic.io)
- 🚀 Run an instant demo:
  
```bash
datamimic demo create healthcare-example
datamimic run ./healthcare-example/datamimic.xml
```

### 📘 Additional Resources

- [CLI Interface](docs/api/cli.md)
- [Data Domains Details](docs/data-domains/README.md)

---

## ❓ FAQ

**Q:** Is Community Edition suitable for commercial projects?

**A:** Absolutely! DATAMIMIC CE uses the MIT License.

**Q:** Why upgrade to Enterprise Edition (EE) instead of using Community Edition (CE)?

**A:** EE provides a web UI, enterprise support, team collaboration, and advanced features like AI-powered test data generation, workflow automation, and compliance tools.

**Q:** Can I contribute?

**A:** Yes! See [Contributing Guide](CONTRIBUTING.md).

---

## 🛠️ Support & Community

- 💬 [GitHub Discussions](https://github.com/rapiddweller/datamimic/discussions)
- 🐛 [Issue Tracker](https://github.com/rapiddweller/datamimic/issues)
- 📧 [Email Support](mailto:support@rapiddweller.com)

---

## 🌟 Stay Connected

- 🌐 [Website](https://datamimic.io)
- 💼 [LinkedIn](https://www.linkedin.com/company/rapiddweller)

---

⭐ **Star us on GitHub** to keep DATAMIMIC growing!
