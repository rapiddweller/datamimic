# Generator Migration to Domain Architecture

## Overview

This document outlines the process of migrating generators from the global generator directory to the domain-specific architecture. This migration is part of our ongoing effort to modularize the codebase and improve its maintainability.

## Motivation

The current architecture has generators defined in a global `generators` directory, while entities are being migrated to a domain-based structure. This creates several issues:

1. **Circular imports** - Domain models depend on global generators which may depend on domain-specific loaders
2. **Poor cohesion** - Related components (models, generators, loaders) are spread across different parts of the codebase
3. **Unclear ownership** - Difficult to determine which domain is responsible for a particular generator
4. **Inconsistent architecture** - Mixed approach with some components in domains and others global

## Migration Plan

### Step 1: Identify Generator Dependencies

For each generator:
1. Identify its dependencies (other generators, data loaders, etc.)
2. Determine which domain it belongs to (common, healthcare, finance, etc.)
3. Check for circular dependencies with domain components

### Step 2: Create Domain-Specific Generator Classes

1. Create the appropriate directory structure: `domains/<domain_name>/generators/`
2. Move generator code to the new location
3. Update imports to reference domain-specific dependencies
4. Address any circular dependencies by restructuring

### Step 3: Update References

1. Update imports in all files that reference the generators
2. Maintain backward compatibility where necessary (see approach below)

### Step 4: Testing

1. Write tests for domain-specific generators
2. Ensure all existing functionality works with the new structure
3. Verify no regressions in functionality

## Backward Compatibility

To maintain backward compatibility during the transition period, we can use one of these approaches:

### Option 1: Proxy Classes (Recommended)

Keep the original generator files but have them import and re-export the domain version:

```python
# datamimic_ce/generators/phone_number_generator.py
from datamimic_ce.domains.common.generators.phone_number_generator import PhoneNumberGenerator
```

### Option 2: Deprecation Warnings

Add deprecation warnings to the original generators:

```python
import warnings
warnings.warn(
    "This module is deprecated. Use datamimic_ce.domains.common.generators.phone_number_generator instead.",
    DeprecationWarning,
    stacklevel=2
)
```

## Directory Structure

The new structure for generators will follow the domain-based pattern:

```
datamimic_ce/
  domains/
    common/
      generators/
        phone_number_generator.py
        email_generator.py
        ...
    healthcare/
      generators/
        medical_code_generator.py
        diagnosis_generator.py
        ...
    finance/
      generators/
        payment_method_generator.py
        currency_generator.py
        ...
```

## Example Migration

### Before

```python
# datamimic_ce/generators/phone_number_generator.py
class PhoneNumberGenerator:
    def __init__(self, country_code="US"):
        # Implementation
    
    def generate(self):
        # Implementation
```

### After

```python
# datamimic_ce/domains/common/generators/phone_number_generator.py
class PhoneNumberGenerator:
    def __init__(self, country_code="US"):
        # Implementation
    
    def generate(self):
        # Implementation
```

```python
# datamimic_ce/generators/phone_number_generator.py (for backward compatibility)
from datamimic_ce.domains.common.generators.phone_number_generator import PhoneNumberGenerator
```

## Conclusion

Migrating generators to the domain architecture will resolve circular dependencies, improve code organization, and align with our modular architecture goals. By following this plan, we can ensure a smooth transition without breaking existing functionality.