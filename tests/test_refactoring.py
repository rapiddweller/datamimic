# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Test script to validate the refactoring of entities."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from datamimic_ce.entities.healthcare.clinical_trial_entity.core import ClinicalTrialEntity


def test_clinical_trial_entity() -> None:
    """Test the ClinicalTrialEntity after refactoring."""
    print("Testing ClinicalTrialEntity...")
    
    # Create an instance of ClinicalTrialEntity
    entity = ClinicalTrialEntity()
    
    # Access some properties
    properties = [
        "trial_id", "nct_id", "phase", "status", "title", "brief_summary", 
        "sponsor", "start_date", "end_date", "locations", "primary_outcomes"
    ]
    
    # Print the properties
    for prop in properties:
        value = getattr(entity, prop)
        print(f"  {prop}: {value}")
    
    # Test to_dict method
    entity_dict = entity.to_dict()
    print(f"  Entity has {len(entity_dict)} properties")
    
    # Test reset method
    entity.reset()
    print("  Entity reset successful")


def generate_entity_batch(entity_type: str, count: int, output_file: str | None = None) -> list[dict[str, Any]]:
    """Generate a batch of entities and optionally save to a file.
    
    Args:
        entity_type: Type of entity to generate (e.g., "clinical_trial")
        count: Number of entities to generate
        output_file: Optional file path to save the entities
        
    Returns:
        A list of entity dictionaries
    """
    # Don't instantiate BaseClassFactoryUtil as it's an abstract class
    factory_util = None
    
    if entity_type == "clinical_trial":
        batch = ClinicalTrialEntity.generate_batch(count, factory_util)
    else:
        raise ValueError(f"Unsupported entity type: {entity_type}")
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch, f, indent=2)
        print(f"Saved {len(batch)} {entity_type} entities to {output_file}")
    
    return batch


def main() -> None:
    """Run the tests."""
    parser = argparse.ArgumentParser(description="Test the refactored entities")
    parser.add_argument("--generate", type=str, choices=["clinical_trial"], help="Generate a batch of entities")
    parser.add_argument("--count", type=int, default=5, help="Number of entities to generate")
    parser.add_argument("--output", type=str, help="Output file for generated entities")
    
    args = parser.parse_args()
    
    if args.generate:
        generate_entity_batch(args.generate, args.count, args.output)
    else:
        # Run tests
        test_clinical_trial_entity()


if __name__ == "__main__":
    main() 