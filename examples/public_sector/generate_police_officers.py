#!/usr/bin/env python3
# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script for generating police officer data.

This script demonstrates how to use the PoliceOfficerService to generate
synthetic police officer data.
"""

import argparse
import json
import os
import sys

# Add parent directory to path to allow importing from datamimic_ce
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datamimic_ce.domains.public_sector.services.police_officer_service import PoliceOfficerService


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Generate synthetic police officer data")
    parser.add_argument("--count", type=int, default=10, help="Number of police officers to generate")
    parser.add_argument("--locale", type=str, default="en", help="Locale to use (e.g., 'en', 'de')")
    parser.add_argument("--dataset", type=str, default="US", help="Dataset to use (e.g., 'US', 'DE')")
    parser.add_argument("--output", type=str, default="police_officers.json", help="Output file path")
    parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--rank", type=str, help="Filter officers by rank")
    parser.add_argument("--department", type=str, help="Filter officers by department")
    parser.add_argument("--unit", type=str, help="Filter officers by unit")
    
    return parser.parse_args()


def main():
    """Main function for generating police officer data."""
    args = parse_args()
    
    # Get the service instance
    service = PoliceOfficerService.get_instance(locale=args.locale, dataset=args.dataset)
    
    # Generate officers based on filters
    if args.rank:
        print(f"Generating {args.count} officers with rank '{args.rank}'...")
        officers = service.get_officers_by_rank(args.rank, args.count)
    elif args.department:
        print(f"Generating {args.count} officers from department '{args.department}'...")
        officers = service.get_officers_by_department(args.department, args.count)
    elif args.unit:
        print(f"Generating {args.count} officers from unit '{args.unit}'...")
        officers = service.get_officers_by_unit(args.unit, args.count)
    else:
        print(f"Generating {args.count} random officers...")
        officers = service.generate_officers(args.count)
    
    # Export the data
    output_path = service.export_officers(
        count=args.count, 
        output_path=args.output, 
        format=args.format
    )
    
    print(f"Generated {args.count} police officers and saved to {output_path}")
    
    # Print a sample officer
    if officers:
        print("\nSample Police Officer:")
        print(json.dumps(officers[0], indent=2))


if __name__ == "__main__":
    main()