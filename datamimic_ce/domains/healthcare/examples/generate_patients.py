# #!/usr/bin/env python3
# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# """
# Generate patient data example.

# This script demonstrates how to generate and export patient data
# using the Patient entity and PatientService.
# """

# import argparse
# import json
# import os
# import sys

# from datamimic_ce.domains.healthcare.services.patient_service import PatientService


# def generate_single_patient():
#     """Generate a single patient and print the details in JSON format."""
#     service = PatientService()
#     patient = service.generate_patient()
#     print(json.dumps(patient, indent=2))


# def generate_patients_batch(count: int, output_file: str = None):
#     """Generate a batch of patients and export them to a file or print a sample.

#     Args:
#         count: The number of patients to generate.
#         output_file: The path to the output file. If None, prints the first 3 patients.
#     """
#     service = PatientService()
#     patients = service.generate_batch(count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(patients, output_file)
#             print(f"Exported {count} patients to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(patients, output_file)
#             print(f"Exported {count} patients to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         # Print the first 3 patients (or all if less than 3)
#         sample_size = min(3, len(patients))
#         print(f"Generated {count} patients. Here are the first {sample_size}:")
#         for i, patient in enumerate(patients[:sample_size]):
#             print(f"\nPatient {i + 1}:")
#             print(json.dumps(patient, indent=2))


# def get_patients_by_condition(condition: str, count: int = 10, output_file: str = None):
#     """Generate patients with a specific medical condition.

#     Args:
#         condition: The medical condition to include.
#         count: The number of patients to generate.
#         output_file: The path to the output file. If None, prints the patients.
#     """
#     service = PatientService()
#     patients = service.get_patients_by_condition(condition, count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(patients, output_file)
#             print(f"Exported {len(patients)} patients with {condition} to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(patients, output_file)
#             print(f"Exported {len(patients)} patients with {condition} to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(patients)} patients with {condition}:")
#         for i, patient in enumerate(patients):
#             print(f"\nPatient {i + 1}:")
#             print(json.dumps(patient, indent=2))


# def get_patients_by_age_range(min_age: int, max_age: int, count: int = 10, output_file: str = None):
#     """Generate patients within a specific age range.

#     Args:
#         min_age: The minimum age.
#         max_age: The maximum age.
#         count: The number of patients to generate.
#         output_file: The path to the output file. If None, prints the patients.
#     """
#     service = PatientService()
#     patients = service.get_patients_by_age_range(min_age, max_age, count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(patients, output_file)
#             print(f"Exported {len(patients)} patients aged {min_age}-{max_age} to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(patients, output_file)
#             print(f"Exported {len(patients)} patients aged {min_age}-{max_age} to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(patients)} patients aged {min_age}-{max_age}:")
#         for i, patient in enumerate(patients):
#             print(f"\nPatient {i + 1}:")
#             print(json.dumps(patient, indent=2))


# def main():
#     """Parse command-line arguments and execute the appropriate function."""
#     parser = argparse.ArgumentParser(description="Generate patient data")
#     subparsers = parser.add_subparsers(dest="command", help="Command to execute")

#     # Single patient command
#     single_parser = subparsers.add_parser("single", help="Generate a single patient")

#     # Batch command
#     batch_parser = subparsers.add_parser("batch", help="Generate a batch of patients")
#     batch_parser.add_argument("--count", type=int, default=10, help="Number of patients to generate")
#     batch_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Condition command
#     condition_parser = subparsers.add_parser("condition", help="Generate patients with a specific condition")
#     condition_parser.add_argument("condition", type=str, help="Medical condition to include")
#     condition_parser.add_argument("--count", type=int, default=10, help="Number of patients to generate")
#     condition_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Age range command
#     age_parser = subparsers.add_parser("age", help="Generate patients within a specific age range")
#     age_parser.add_argument("min_age", type=int, help="Minimum age")
#     age_parser.add_argument("max_age", type=int, help="Maximum age")
#     age_parser.add_argument("--count", type=int, default=10, help="Number of patients to generate")
#     age_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     args = parser.parse_args()

#     if args.command == "single":
#         generate_single_patient()
#     elif args.command == "batch":
#         generate_patients_batch(args.count, args.output)
#     elif args.command == "condition":
#         get_patients_by_condition(args.condition, args.count, args.output)
#     elif args.command == "age":
#         get_patients_by_age_range(args.min_age, args.max_age, args.count, args.output)
#     else:
#         parser.print_help()


# if __name__ == "__main__":
#     main()
