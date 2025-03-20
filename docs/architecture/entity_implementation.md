# DataMimic Entity Implementation Guide

This guide provides detailed information on implementing entities in the DataMimic domain architecture.

## Entity Model Architecture

Each entity in DataMimic consists of several components:

1. **Entity Model**: The core class that represents the entity
2. **Data Loader**: Responsible for loading reference data
3. **Generator**: Handles generation of complex attribute values
4. **Service**: Provides high-level operations for the entity

## Implementing a New Entity Model

### Step 1: Create the Data Loader

Start by implementing a data loader for any reference data your entity needs:

```python
# domains/your_domain/data_loaders/your_entity_loader.py
from datamimic_ce.core.base_data_loader import BaseDataLoader

class YourEntityLoader(BaseDataLoader):
    # Class-level caches for efficient data access
    _SOME_DATA_CACHE = {}
    
    @classmethod
    def get_entity_data(cls, country_code: str) -> list[tuple[str, float]]:
        """Load entity-specific data for the given country code."""
        return cls.get_country_specific_data(
            data_type="your_data_type",
            country_code=country_code,
            domain_path="your_domain_path"
        )
    
    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Provide default values when no country-specific data exists."""
        if data_type == "your_data_type":
            return [("Value1", 0.5), ("Value2", 0.5)]
        return []
```

### Step 2: Create the Entity Generator

Next, implement a generator for complex attribute generation:

```python
# domains/your_domain/generators/your_entity_generator.py
from typing import Optional, List

class YourEntityGenerator:
    """Generator for entity-specific attributes."""
    
    def __init__(self, dataset: str = "US", count: int = 1):
        """Initialize the generator.
        
        Args:
            dataset: Country code for country-specific generation
            count: Number of entities to generate
        """
        self.dataset = dataset
        self.count = count
        # Initialize other generators you might need
    
    def generate_attribute1(self) -> str:
        """Generate a specific attribute."""
        # Implementation here
        return "Generated value"
    
    def generate_attribute2(self, param: str) -> str:
        """Generate another attribute based on a parameter."""
        # Implementation here
        return f"Generated value for {param}"
```

### Step 3: Implement the Entity Model

The core entity model class:

```python
# domains/your_domain/models/your_entity.py
from typing import Optional, Dict, Any

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.your_domain.data_loaders.your_entity_loader import YourEntityLoader
from datamimic_ce.domains.your_domain.generators.your_entity_generator import YourEntityGenerator

class YourEntity(BaseEntity):
    """YourEntity model representing a specific domain entity."""
    
    def __init__(
        self,
        dataset: str = "US",
        count: int = 1,
        **kwargs
    ):
        """Initialize the entity.
        
        Args:
            dataset: Country code for country-specific generation
            count: Number of entities to generate
            **kwargs: Additional parameters for customization
        """
        super().__init__()
        self.dataset = dataset
        self.count = count
        
        # Load entity-specific data
        self._entity_data = YourEntityLoader.get_entity_data(country_code=dataset)
        
        # Initialize generators
        self._entity_generator = YourEntityGenerator(dataset=dataset, count=count)
        
        # Initialize property cache for lazy loading
        self._property_cache = PropertyCache()
    
    @property
    def id(self) -> str:
        """Get the entity ID.
        
        Returns:
            The entity ID
        """
        return self._property_cache.get_or_generate(
            "id",
            lambda: self._entity_generator.generate_id()
        )
    
    @property
    def name(self) -> str:
        """Get the entity name.
        
        Returns:
            The entity name
        """
        return self._property_cache.get_or_generate(
            "name",
            lambda: self._entity_generator.generate_name()
        )
    
    # Add more properties as needed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to a dictionary.
        
        Returns:
            Dictionary representation of the entity
        """
        return {
            "id": self.id,
            "name": self.name,
            # Add other properties
        }
    
    def reset(self) -> None:
        """Reset all cached properties."""
        self._property_cache.clear()
```

### Step 4: Create the Entity Service

Implement a service class for higher-level operations:

```python
# domains/your_domain/services/your_entity_service.py
from typing import List, Dict, Any, Optional

from datamimic_ce.domains.your_domain.models.your_entity import YourEntity

class YourEntityService:
    """Service for creating and managing entities."""
    
    @staticmethod
    def create_entity(
        dataset: str = "US",
        count: int = 1,
        **kwargs
    ) -> YourEntity:
        """Create a single entity instance.
        
        Args:
            dataset: Country code for country-specific generation
            count: Number of entities to generate
            **kwargs: Additional parameters for customization
            
        Returns:
            A new entity instance
        """
        return YourEntity(dataset=dataset, count=count, **kwargs)
    
    @staticmethod
    def create_entities(
        count: int,
        dataset: str = "US",
        **kwargs
    ) -> List[YourEntity]:
        """Create multiple entity instances.
        
        Args:
            count: Number of entities to create
            dataset: Country code for country-specific generation
            **kwargs: Additional parameters for customization
            
        Returns:
            List of entity instances
        """
        return [
            YourEntity(dataset=dataset, count=count, **kwargs)
            for _ in range(count)
        ]
    
    @staticmethod
    def filter_by_attribute(
        entities: List[YourEntity],
        attribute: str,
        value: Any
    ) -> List[YourEntity]:
        """Filter entities by attribute value.
        
        Args:
            entities: List of entities to filter
            attribute: Attribute name to filter by
            value: Value to filter for
            
        Returns:
            Filtered list of entities
        """
        return [
            entity for entity in entities
            if getattr(entity, attribute) == value
        ]
    
    @staticmethod
    def entities_to_dict(entities: List[YourEntity]) -> List[Dict[str, Any]]:
        """Convert a list of entities to a list of dictionaries.
        
        Args:
            entities: List of entities to convert
            
        Returns:
            List of dictionaries representing entities
        """
        return [entity.to_dict() for entity in entities]
```

### Step 5: Register the Entity in the Framework

Update variable_task.py to include your entity in the mapping:

```python
# In the entity_mappings dictionary in variable_task.py
entity_mappings = {
    # Other mappings...
    "YourEntity": "your_domain.models.your_entity.YourEntity",
}
```

## Best Practices for Entity Implementation

1. **Property Caching**:
   - Use `PropertyCache` for all properties that require computation
   - Implement a proper `reset()` method to clear cache

2. **Realistic Data Generation**:
   - Use realistic distributions for attribute values
   - Consider relationships between attributes
   - Support locale-specific generation when appropriate

3. **Modularity**:
   - Keep generators focused on specific attribute types
   - Separate data loading from generation logic
   - Use composition over inheritance

4. **Performance**:
   - Cache reference data at the class level
   - Use lazy loading for expensive operations
   - Consider memory usage for large-scale generation

5. **Testing**:
   - Create unit tests for each component
   - Test with different locales and datasets
   - Verify property caching and reset functionality

6. **Documentation**:
   - Document public methods and properties
   - Explain the purpose of each class
   - Include examples for complex functionality

## Example Python Usage

```python
# Import the entity service
from datamimic_ce.domains.your_domain.services.your_entity_service import YourEntityService

# Create a single entity
entity = YourEntityService.create_entity(dataset="US")

# Access properties
print(f"Entity ID: {entity.id}")
print(f"Entity Name: {entity.name}")

# Create multiple entities
entities = YourEntityService.create_entities(count=10, dataset="DE")

# Filter entities
filtered = YourEntityService.filter_by_attribute(entities, "attribute", "value")

# Convert to dictionaries
entity_dicts = YourEntityService.entities_to_dict(entities)
```

## Example XML Usage

```xml
<generate name="YourEntities" count="5">
    <variable name="entity" entity="YourEntity" dataset="US" />
    <key name="id" script="entity.id" />
    <key name="name" script="entity.name" />
    <!-- Other attributes -->
</generate>
```

This XML configuration will create 5 instances of your entity with the US dataset and output the id and name attributes.