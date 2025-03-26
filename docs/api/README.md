# DATAMIMIC API Reference

This section provides detailed API documentation for using DATAMIMIC in your applications.

## Contents

- [Command Line Interface](cli.md) - Documentation for the DATAMIMIC CLI
- [XML Configuration](xml-config.md) - Reference for XML-based configuration
- [Python SDK](python-sdk.md) - Comprehensive Python API documentation
- [Extension APIs](extensions.md) - APIs for extending DATAMIMIC functionality

## Getting Started

The DATAMIMIC API can be utilized in multiple ways:

1. **Command Line Interface** - For quick data generation tasks and automation
2. **XML Configuration** - For declarative data modeling and generation
3. **Python SDK** - For direct integration with your Python applications
4. **Extensions** - For customizing and extending DATAMIMIC capabilities

## API Overview

### Command Line Interface (CLI)

```bash
# Basic Commands
datamimic version                    # Display version information
datamimic init <project-name>        # Initialize a new project
datamimic run <descriptor.xml>       # Run a data generation descriptor
datamimic demo list                  # List available demos
datamimic demo create <demo-name>    # Create a specific demo
```

### Python SDK Quick Start

```python
from datamimic_ce.domains.common.services import PersonService
from datamimic_ce.factory.datamimic_test_factory import DataMimicTestFactory

# Using domain services
person_service = PersonService(dataset="US")
person = person_service.generate()

# Using test factory
factory = DataMimicTestFactory("customer.xml", "customer")
customer = factory.create()
```

### XML Configuration Example

```xml
<setup>
    <generate name="users" count="100">
        <variable name="person" entity="Person()"/>
        <key name="id" generator="IncrementGenerator"/>
        <key name="name" script="person.full_name"/>
        <key name="email" script="person.email"/>
    </generate>
</setup>
```

## Common Use Cases

### Data Generation

- Generate test data for applications
- Create training datasets for machine learning
- Produce demonstration data for demos and presentations
- Anonymize production data for development environments

### Integration Scenarios

- Database seeding and testing
- API testing with realistic data
- Performance testing with large datasets
- Data migration testing

### Privacy & Compliance

- GDPR-compliant data anonymization
- Data masking for sensitive information
- Pseudonymization for development environments
- Compliance testing and validation

## Best Practices

1. **Project Organization**
   - Use separate descriptors for different data domains
   - Maintain consistent naming conventions
   - Version control your descriptors

2. **Performance Optimization**
   - Use batch generation for large datasets
   - Leverage parallel processing capabilities
   - Implement efficient data relationships

3. **Data Quality**
   - Define comprehensive validation rules
   - Use appropriate data distributions
   - Maintain referential integrity

## Advanced Topics

- [Custom Generator Development](extensions.md#custom-generators)
- [Domain-Specific Modeling](xml-config.md#domain-modeling)
- [Integration Patterns](python-sdk.md#integration)
- [Security Best Practices](extensions.md#security)

## API Reference Links

- [CLI Command Reference](cli.md)
- [XML Schema Reference](xml-config.md)
- [Python API Reference](python-sdk.md)
- [Extension Development Guide](extensions.md)

## Support & Resources

- [GitHub Repository](https://github.com/rapiddweller/datamimic)
- [Issue Tracker](https://github.com/rapiddweller/datamimic/issues)
- [Community Discussions](https://github.com/rapiddweller/datamimic/discussions) 