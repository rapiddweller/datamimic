# DATAMIMIC Domain Architecture

## Overview

DataMimic uses a domain-driven design architecture to organize its entity models, data generators, and related functionality. This architecture provides several benefits:

- **Improved organization** and maintainability through logical separation by domain
- **Better encapsulation** with clear separation of concerns
- **Enhanced modularity** allowing easier extensions and customizations
- **Clearer dependencies** between related components
- **Consistent patterns** across all domains

## Domain Structure

Each domain follows a consistent structure:

```
domains/
├── common/           # Common entities like Address, Person, Company
│   ├── data_loaders/ # Data loading components
│   ├── generators/   # Specialized data generators
│   ├── models/       # Entity models
│   ├── services/     # High-level domain services
│   └── utils/        # Domain-specific utilities
├── healthcare/       # Healthcare-specific entities
│   ├── data_loaders/
│   ├── generators/
│   ├── models/
│   ├── services/
│   └── utils/
├── finance/          # Finance domain entities
├── ecommerce/        # E-commerce domain entities
├── insurance/        # Insurance domain entities
└── public_sector/    # Public sector domain entities
```

## Key Components

### 1. Entity Models

Entity models represent domain-specific data like Person, Company, Doctor, etc. All models:

- Inherit from `BaseEntity`
- Use `PropertyCache` for lazy generation and caching of values
- Expose properties for accessing attributes
- Include a `to_dict()` method for serialization
- Implement a `reset()` method to clear property cache

Example:
```python
class Company(BaseEntity):
    def __init__(self, dataset="US", count=1):
        self.dataset = dataset
        self._property_cache = PropertyCache()
        self._company_generator = CompanyGenerator(dataset=dataset)
        
    @property
    def name(self):
        return self._property_cache.get_or_generate(
            "name",
            lambda: self._company_generator.generate_name()
        )
        
    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            # other properties
        }
        
    def reset(self):
        self._property_cache.clear()
```

### 2. Data Loaders

Data loaders handle loading and caching of reference data used by entity models:

- Inherit from `BaseDataLoader`
- Use class-level caching for efficiency
- Provide methods to fetch domain-specific data
- Handle locale/dataset-specific data loading

Example:
```python
class CompanyLoader(BaseDataLoader):
    _SECTOR_CACHE = {}
    
    @classmethod
    def get_sectors(cls, country_code):
        return cls.get_country_specific_data(
            data_type="sector", 
            country_code=country_code
        )
```

### 3. Generators

Generators handle the creation of specific attribute values:

- Specialized by domain and entity type
- Encapsulate complex generation logic
- Use realistic distributions and patterns
- Support locale-specific generation
- **Located in domain-specific generator modules** (not in global generator directory)

Example:
```python
# Path: domains/common/generators/company_generator.py
class CompanyGenerator:
    def __init__(self, dataset="US"):
        self.dataset = dataset
        # Use other domain generators instead of global ones
        self.name_generator = CompanyNameGenerator() 
        
    def generate_company_name(self):
        return self.name_generator.generate()
```

The migration of generators from the global namespace to domain-specific locations helps resolve circular dependencies and improves code organization. For backward compatibility, the original generator files can import and re-export from the domain version:

```python
# Path: generators/company_name_generator.py (legacy location)
# Re-export from domain-specific location for backward compatibility
from datamimic_ce.domains.common.generators.company_name_generator import CompanyNameGenerator
```

### 4. Services

Services provide high-level functionality for working with entities:

- Create and manipulate entities
- Provide bulk operations
- Implement filtering and searching
- Expose domain-specific business operations

Example:
```python
class CompanyService:
    @staticmethod
    def create_companies(count, dataset="US"):
        return [Company(dataset=dataset) for _ in range(count)]
        
    @staticmethod
    def filter_by_sector(companies, sector):
        return [c for c in companies if c.sector == sector]
```

## XML Configuration

The domain architecture is reflected in the XML configuration, which uses a simplified entity reference syntax:

```xml
<generate name="Companies" count="5">
    <variable name="company" entity="Company" dataset="US" />
    <key name="id" script="company.id" />
    <key name="name" script="company.full_name" />
</generate>
```

The framework automatically maps entity names to their domain-specific implementations, making configuration simpler and more maintainable.

## Creating New Domain Components

### Creating Domain Entities

To create a new domain entity:

1. Identify the appropriate domain (or create a new one)
2. Create data loaders for any reference data
3. Implement specialized generators for complex attributes
4. Create the entity model class inheriting from `BaseEntity`
5. Implement a service class for high-level operations
6. Add the entity mapping to `variable_task.py`
7. Create example XML and Python code

### Creating Domain Generators

When implementing a new generator:

1. Determine the appropriate domain for the generator
2. Create the generator in `domains/<domain>/generators/`
3. Implement the generator using other domain-specific components
4. Avoid dependencies on global generators to prevent circular imports
5. If replacing a global generator, create a proxy in the original location
6. Update any existing imports to reference the new location
7. Write tests for the new domain-specific generator

## Best Practices

1. **Domain separation**: Keep domain-specific code within its domain package
2. **Single responsibility**: Each class should have a single, well-defined purpose
3. **Consistent caching**: Use `PropertyCache` for all lazy-loaded properties
4. **Clear interfaces**: Define clear boundaries between domains
5. **Documentation**: Document the purpose and usage of each component
6. **Testing**: Create comprehensive tests for each component

## Migration from Legacy Architecture

DataMimic has migrated from a legacy architecture with flat entity files to the new domain-driven design. The migration involved:

1. Creating domain-specific packages with proper structure
2. Implementing entities using the new architecture
3. **Migrating generators to domain-specific locations**
4. Updating factory methods to use domain-based entities
5. Updating entity references in XML configurations
6. Providing backward compatibility during transition
7. Removing legacy entity implementations when no longer needed

### Generator Migration Strategy

The migration of generators follows these principles:

1. **Complete domain first**: Migrate all related generators together for a domain
2. **Maintain backward compatibility**: Use proxy classes in original locations
3. **Fix circular dependencies**: Restructure imports to prevent cycles
4. **Update tests**: Ensure all tests work with the new structure
5. **Gradual phase-out**: Eventually remove the legacy proxies after deprecation period

See [Generator Migration Guide](generator_migration.md) for detailed steps.