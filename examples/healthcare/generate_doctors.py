#!/usr/bin/env python3
# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script for generating doctor data.

This script demonstrates how to use the Doctor entity and DoctorService
to generate and export doctor data.
"""

import argparse
import json
import os
import sys

# Add the parent directory to the Python path to allow importing datamimic_ce
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datamimic_ce.domains.healthcare import Doctor, DoctorService
from datamimic_ce.utils.domain_class_util import DomainClassUtil


def generate_single_doctor(locale="en", dataset=None):
    """Generate a single doctor and print it to the console.

    Args:
        locale: The locale to use
        dataset: The dataset to use
    """
    # Create a class factory utility
    class_factory_util = DomainClassUtil()

    # Create a doctor entity
    doctor = Doctor(
        class_factory_util=class_factory_util,
        locale=locale,
        dataset=dataset,
    )

    # Convert the doctor to a dictionary
    doctor_dict = doctor.to_dict()

    # Print the doctor as JSON
    print(json.dumps(doctor_dict, indent=2))


def generate_doctors_batch(count=10, locale="en", dataset=None, output_path=None, format="json"):
    """Generate a batch of doctors and export them to a file.

    Args:
        count: The number of doctors to generate
        locale: The locale to use
        dataset: The dataset to use
        output_path: The path to write the output to
        format: The output format (json, csv)
    """
    # Create a doctor service
    doctor_service = DoctorService(locale=locale, dataset=dataset)

    # Generate and export doctors
    if output_path:
        output_file = doctor_service.export_doctors(count, output_path, format)
        print(f"Exported {count} doctors to {output_file}")
    else:
        # If no output path is specified, print the first 3 doctors to the console
        doctors = doctor_service.generate_doctors(count)
        print(f"Generated {count} doctors. Here are the first 3:")
        for i, doctor in enumerate(doctors[:3], 1):
            print(f"\nDoctor {i}:")
            print(json.dumps(doctor, indent=2))
        if count > 3:
            print(f"\n... and {count - 3} more.")


def get_doctor_by_specialty(specialty, locale="en", dataset=None):
    """Get a doctor with a specific specialty.

    Args:
        specialty: The specialty to look for
        locale: The locale to use
        dataset: The dataset to use
    """
    # Create a doctor service
    doctor_service = DoctorService(locale=locale, dataset=dataset)

    # Get a doctor with the specified specialty
    doctor = doctor_service.get_doctor_by_specialty(specialty)

    # Print the doctor as JSON
    print(json.dumps(doctor, indent=2))


def main():
    """Parse command line arguments and execute the appropriate function."""
    parser = argparse.ArgumentParser(description="Generate doctor data")
    parser.add_argument("--count", type=int, default=10, help="Number of doctors to generate")
    parser.add_argument("--locale", default="en", help="Locale to use")
    parser.add_argument("--dataset", help="Dataset to use")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--specialty", help="Generate a doctor with a specific specialty")
    parser.add_argument("--single", action="store_true", help="Generate a single doctor")

    args = parser.parse_args()

    if args.specialty:
        get_doctor_by_specialty(args.specialty, args.locale, args.dataset)
    elif args.single:
        generate_single_doctor(args.locale, args.dataset)
    else:
        generate_doctors_batch(args.count, args.locale, args.dataset, args.output, args.format)


if __name__ == "__main__":
    main()
