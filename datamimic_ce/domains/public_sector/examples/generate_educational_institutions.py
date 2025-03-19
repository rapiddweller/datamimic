#!/usr/bin/env python3
# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script for generating educational institution data.

This script demonstrates how to use the EducationalInstitutionService to generate
synthetic educational institution data.
"""

import argparse
import json
import os
import sys

# Add parent directory to path to allow importing from datamimic_ce
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datamimic_ce.domains.public_sector.services.educational_institution_service import EducationalInstitutionService


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Generate synthetic educational institution data")
    parser.add_argument("--count", type=int, default=10, help="Number of institutions to generate")
    parser.add_argument("--locale", type=str, default="en", help="Locale to use (e.g., 'en', 'de')")
    parser.add_argument("--dataset", type=str, default="US", help="Dataset to use (e.g., 'US', 'DE')")
    parser.add_argument("--output", type=str, default="educational_institutions.json", help="Output file path")
    parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--type", type=str, help="Filter institutions by type (e.g., 'University', 'College')")
    parser.add_argument(
        "--level", type=str, help="Filter institutions by level (e.g., 'Elementary', 'Higher Education')"
    )
    parser.add_argument("--min-students", type=int, help="Minimum student count for filtering")
    parser.add_argument("--max-students", type=int, help="Maximum student count for filtering")
    parser.add_argument("--preset", type=str, choices=["universities", "colleges", "k12"], help="Use a preset filter")

    return parser.parse_args()


def main():
    """Main function for generating educational institution data."""
    args = parse_args()

    # Get the service instance
    service = EducationalInstitutionService.get_instance(locale=args.locale, dataset=args.dataset)

    # Generate institutions based on filters
    if args.preset == "universities":
        print(f"Generating {args.count} universities...")
        institutions = service.get_universities(args.count)
    elif args.preset == "colleges":
        print(f"Generating {args.count} colleges...")
        institutions = service.get_colleges(args.count)
    elif args.preset == "k12":
        print(f"Generating {args.count} K-12 schools...")
        institutions = service.get_k12_schools(args.count)
    elif args.type:
        print(f"Generating {args.count} institutions of type '{args.type}'...")
        institutions = service.get_institutions_by_type(args.type, args.count)
    elif args.level:
        print(f"Generating {args.count} institutions of level '{args.level}'...")
        institutions = service.get_institutions_by_level(args.level, args.count)
    elif args.min_students is not None and args.max_students is not None:
        print(f"Generating {args.count} institutions with {args.min_students}-{args.max_students} students...")
        institutions = service.get_institutions_by_student_count_range(args.min_students, args.max_students, args.count)
    else:
        print(f"Generating {args.count} random institutions...")
        institutions = service.generate_institutions(args.count)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) if os.path.dirname(args.output) else ".", exist_ok=True)

    # Export the data
    if args.format == "json":
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(institutions, f, indent=2)
    elif args.format == "csv":
        import csv

        # Get all possible keys from all institutions
        fieldnames = set()
        for institution in institutions:
            fieldnames.update(institution.keys())

            # Handle nested dictionaries like address
            nested_keys = []
            for key, value in institution.items():
                if isinstance(value, dict):
                    nested_keys.append(key)
                    for nested_key in value:
                        fieldnames.add(f"{key}_{nested_key}")

            # Remove nested dictionaries
            for key in nested_keys:
                fieldnames.discard(key)

        # Flatten the data
        flat_institutions = []
        for institution in institutions:
            flat_institution = {}
            for key, value in institution.items():
                if isinstance(value, dict):
                    for nested_key, nested_value in value.items():
                        flat_institution[f"{key}_{nested_key}"] = nested_value
                else:
                    flat_institution[key] = value
            flat_institutions.append(flat_institution)

        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
            writer.writeheader()
            writer.writerows(flat_institutions)

    print(f"Generated {args.count} educational institutions and saved to {args.output}")

    # Print a sample institution
    if institutions:
        print("\nSample Educational Institution:")
        print(json.dumps(institutions[0], indent=2))


if __name__ == "__main__":
    main()
