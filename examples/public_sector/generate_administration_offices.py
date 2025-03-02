#!/usr/bin/env python3
# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script for generating administration office data.

This script demonstrates how to use the AdministrationOfficeService to generate
synthetic public administration office data.
"""

import argparse
import json
import os
import sys

# Add parent directory to path to allow importing from datamimic_ce
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datamimic_ce.domains.public_sector.services.administration_office_service import AdministrationOfficeService


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Generate synthetic public administration office data")
    parser.add_argument("--count", type=int, default=10, help="Number of offices to generate")
    parser.add_argument("--locale", type=str, default="en", help="Locale to use (e.g., 'en', 'de')")
    parser.add_argument("--dataset", type=str, default="US", help="Dataset to use (e.g., 'US', 'DE')")
    parser.add_argument("--output", type=str, default="administration_offices.json", help="Output file path")
    parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--type", type=str, help="Filter offices by type (e.g., 'Municipal Government', 'Federal')")
    parser.add_argument("--jurisdiction", type=str, help="Filter offices by jurisdiction (e.g., 'City of Boston')")
    parser.add_argument("--min-budget", type=float, help="Minimum annual budget for filtering")
    parser.add_argument("--max-budget", type=float, help="Maximum annual budget for filtering")
    parser.add_argument("--preset", type=str, choices=["municipal", "state", "federal"], help="Use a preset filter")
    
    return parser.parse_args()


def main():
    """Main function for generating administration office data."""
    args = parse_args()
    
    # Get the service instance
    service = AdministrationOfficeService.get_instance(locale=args.locale, dataset=args.dataset)
    
    # Generate offices based on filters
    if args.preset == "municipal":
        print(f"Generating {args.count} municipal government offices...")
        offices = service.get_municipal_offices(args.count)
    elif args.preset == "state":
        print(f"Generating {args.count} state government offices...")
        offices = service.get_state_offices(args.count)
    elif args.preset == "federal":
        print(f"Generating {args.count} federal government offices...")
        offices = service.get_federal_offices(args.count)
    elif args.type:
        print(f"Generating {args.count} offices of type '{args.type}'...")
        offices = service.get_offices_by_type(args.type, args.count)
    elif args.jurisdiction:
        print(f"Generating {args.count} offices in jurisdiction '{args.jurisdiction}'...")
        offices = service.get_offices_by_jurisdiction(args.jurisdiction, args.count)
    elif args.min_budget is not None and args.max_budget is not None:
        print(f"Generating {args.count} offices with budget between ${args.min_budget:,.2f} and ${args.max_budget:,.2f}...")
        offices = service.get_offices_by_budget_range(args.min_budget, args.max_budget, args.count)
    else:
        print(f"Generating {args.count} random administrative offices...")
        offices = service.generate_offices(args.count)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) if os.path.dirname(args.output) else '.', exist_ok=True)
    
    # Export the data
    if args.format == "json":
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(offices, f, indent=2)
    elif args.format == "csv":
        import csv
        
        # Get all possible keys from all offices
        fieldnames = set()
        for office in offices:
            fieldnames.update(office.keys())
            
            # Handle nested dictionaries like address and hours_of_operation
            nested_keys = []
            for key, value in office.items():
                if isinstance(value, dict):
                    nested_keys.append(key)
                    for nested_key in value.keys():
                        fieldnames.add(f"{key}_{nested_key}")
            
            # Remove nested dictionaries
            for key in nested_keys:
                fieldnames.discard(key)
        
        # Flatten the data
        flat_offices = []
        for office in offices:
            flat_office = {}
            for key, value in office.items():
                if isinstance(value, dict):
                    for nested_key, nested_value in value.items():
                        flat_office[f"{key}_{nested_key}"] = nested_value
                else:
                    flat_office[key] = value
            flat_offices.append(flat_office)
            
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
            writer.writeheader()
            writer.writerows(flat_offices)
    
    print(f"Generated {args.count} administration offices and saved to {args.output}")
    
    # Print a sample office
    if offices:
        print("\nSample Administration Office:")
        sample_office = offices[0]
        
        # Format the sample nicely
        formatted_sample = {
            "office_id": sample_office["office_id"],
            "name": sample_office["name"],
            "type": sample_office["type"],
            "jurisdiction": sample_office["jurisdiction"],
            "annual_budget": f"${sample_office['annual_budget']:,.2f}",
            "staff_count": sample_office["staff_count"],
            "services": sample_office["services"][:3] + (["..."] if len(sample_office["services"]) > 3 else []),
            "departments": sample_office["departments"][:3] + (["..."] if len(sample_office["departments"]) > 3 else []),
            "leadership": {k: v for i, (k, v) in enumerate(sample_office["leadership"].items()) if i < 3}
        }
        
        if len(sample_office["leadership"]) > 3:
            formatted_sample["leadership"]["..."] = "..."
            
        print(json.dumps(formatted_sample, indent=2))


if __name__ == "__main__":
    main()