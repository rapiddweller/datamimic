# #!/usr/bin/env python3
# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# """
# Generate hospital data example.

# This script demonstrates how to generate and export hospital data
# using the Hospital entity and HospitalService.
# """

# import argparse
# import json
# import os
# import sys

# from datamimic_ce.domains.healthcare.services.hospital_service import HospitalService


# def generate_single_hospital():
#     """Generate a single hospital and print the details in JSON format."""
#     service = HospitalService()
#     hospital = service.generate_hospital()
#     print(json.dumps(hospital, indent=2))


# def generate_hospitals_batch(count: int, output_file: str = None):
#     """Generate a batch of hospitals and export them to a file or print a sample.

#     Args:
#         count: The number of hospitals to generate.
#         output_file: The path to the output file. If None, prints the first 3 hospitals.
#     """
#     service = HospitalService()
#     hospitals = service.generate_batch(count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(hospitals, output_file)
#             print(f"Exported {count} hospitals to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(hospitals, output_file)
#             print(f"Exported {count} hospitals to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         # Print the first 3 hospitals (or all if less than 3)
#         sample_size = min(3, len(hospitals))
#         print(f"Generated {count} hospitals. Here are the first {sample_size}:")
#         for i, hospital in enumerate(hospitals[:sample_size]):
#             print(f"\nHospital {i + 1}:")
#             print(json.dumps(hospital, indent=2))


# def get_hospitals_by_type(hospital_type: str, count: int = 10, output_file: str = None):
#     """Generate hospitals of a specific type.

#     Args:
#         hospital_type: The type of hospital to generate.
#         count: The number of hospitals to generate.
#         output_file: The path to the output file. If None, prints the hospitals.
#     """
#     service = HospitalService()
#     hospitals = service.get_hospitals_by_type(hospital_type, count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(hospitals, output_file)
#             print(f"Exported {len(hospitals)} {hospital_type} hospitals to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(hospitals, output_file)
#             print(f"Exported {len(hospitals)} {hospital_type} hospitals to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(hospitals)} {hospital_type} hospitals:")
#         for i, hospital in enumerate(hospitals):
#             print(f"\nHospital {i + 1}:")
#             print(json.dumps(hospital, indent=2))


# def get_hospitals_by_service(service_name: str, count: int = 10, output_file: str = None):
#     """Generate hospitals that offer a specific service.

#     Args:
#         service_name: The service that hospitals should offer.
#         count: The number of hospitals to generate.
#         output_file: The path to the output file. If None, prints the hospitals.
#     """
#     service = HospitalService()
#     hospitals = service.get_hospitals_by_service(service_name, count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals offering {service_name} to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals offering {service_name} to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(hospitals)} hospitals offering {service_name}:")
#         for i, hospital in enumerate(hospitals):
#             print(f"\nHospital {i + 1}:")
#             print(json.dumps(hospital, indent=2))


# def get_hospitals_by_department(department: str, count: int = 10, output_file: str = None):
#     """Generate hospitals that have a specific department.

#     Args:
#         department: The department that hospitals should have.
#         count: The number of hospitals to generate.
#         output_file: The path to the output file. If None, prints the hospitals.
#     """
#     service = HospitalService()
#     hospitals = service.get_hospitals_by_department(department, count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals with {department} department to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals with {department} department to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(hospitals)} hospitals with {department} department:")
#         for i, hospital in enumerate(hospitals):
#             print(f"\nHospital {i + 1}:")
#             print(json.dumps(hospital, indent=2))


# def get_hospitals_by_bed_count_range(min_beds: int, max_beds: int, count: int = 10, output_file: str = None):
#     """Generate hospitals within a specific bed count range.

#     Args:
#         min_beds: The minimum number of beds.
#         max_beds: The maximum number of beds.
#         count: The number of hospitals to generate.
#         output_file: The path to the output file. If None, prints the hospitals.
#     """
#     service = HospitalService()
#     hospitals = service.get_hospitals_by_bed_count_range(min_beds, max_beds, count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals with {min_beds}-{max_beds} beds to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals with {min_beds}-{max_beds} beds to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(hospitals)} hospitals with {min_beds}-{max_beds} beds:")
#         for i, hospital in enumerate(hospitals):
#             print(f"\nHospital {i + 1}:")
#             print(json.dumps(hospital, indent=2))


# def get_hospitals_with_emergency_services(count: int = 10, output_file: str = None):
#     """Generate hospitals that offer emergency services.

#     Args:
#         count: The number of hospitals to generate.
#         output_file: The path to the output file. If None, prints the hospitals.
#     """
#     service = HospitalService()
#     hospitals = service.get_hospitals_with_emergency_services(count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals with emergency services to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(hospitals, output_file)
#             print(f"Exported {len(hospitals)} hospitals with emergency services to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(hospitals)} hospitals with emergency services:")
#         for i, hospital in enumerate(hospitals):
#             print(f"\nHospital {i + 1}:")
#             print(json.dumps(hospital, indent=2))


# def get_teaching_hospitals(count: int = 10, output_file: str = None):
#     """Generate teaching hospitals.

#     Args:
#         count: The number of hospitals to generate.
#         output_file: The path to the output file. If None, prints the hospitals.
#     """
#     service = HospitalService()
#     hospitals = service.get_teaching_hospitals(count)

#     if output_file:
#         # Determine the file format based on the extension
#         _, ext = os.path.splitext(output_file)
#         if ext.lower() == ".json":
#             service.export_to_json(hospitals, output_file)
#             print(f"Exported {len(hospitals)} teaching hospitals to {output_file}")
#         elif ext.lower() == ".csv":
#             service.export_to_csv(hospitals, output_file)
#             print(f"Exported {len(hospitals)} teaching hospitals to {output_file}")
#         else:
#             print(f"Unsupported file format: {ext}")
#             sys.exit(1)
#     else:
#         print(f"Generated {len(hospitals)} teaching hospitals:")
#         for i, hospital in enumerate(hospitals):
#             print(f"\nHospital {i + 1}:")
#             print(json.dumps(hospital, indent=2))


# def main():
#     """Parse command-line arguments and execute the appropriate function."""
#     parser = argparse.ArgumentParser(description="Generate hospital data")
#     subparsers = parser.add_subparsers(dest="command", help="Command to execute")

#     # Batch command
#     batch_parser = subparsers.add_parser("batch", help="Generate a batch of hospitals")
#     batch_parser.add_argument("--count", type=int, default=10, help="Number of hospitals to generate")
#     batch_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Type command
#     type_parser = subparsers.add_parser("type", help="Generate hospitals of a specific type")
#     type_parser.add_argument("type", type=str, help="Hospital type (e.g., General, Teaching, Community, Specialty)")
#     type_parser.add_argument("--count", type=int, default=10, help="Number of hospitals to generate")
#     type_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Service command
#     service_parser = subparsers.add_parser("service", help="Generate hospitals that offer a specific service")
#     service_parser.add_argument("service", type=str, help="Service name (e.g., Emergency Care, Surgery)")
#     service_parser.add_argument("--count", type=int, default=10, help="Number of hospitals to generate")
#     service_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Department command
#     department_parser = subparsers.add_parser("department", help="Generate hospitals that have a specific department")
#     department_parser.add_argument("department", type=str, help="Department name (e.g., Emergency, Surgery)")
#     department_parser.add_argument("--count", type=int, default=10, help="Number of hospitals to generate")
#     department_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Bed count range command
#     bed_count_parser = subparsers.add_parser("beds", help="Generate hospitals within a specific bed count range")
#     bed_count_parser.add_argument("min_beds", type=int, help="Minimum number of beds")
#     bed_count_parser.add_argument("max_beds", type=int, help="Maximum number of beds")
#     bed_count_parser.add_argument("--count", type=int, default=10, help="Number of hospitals to generate")
#     bed_count_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Emergency services command
#     emergency_parser = subparsers.add_parser("emergency", help="Generate hospitals that offer emergency services")
#     emergency_parser.add_argument("--count", type=int, default=10, help="Number of hospitals to generate")
#     emergency_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     # Teaching hospitals command
#     teaching_parser = subparsers.add_parser("teaching", help="Generate teaching hospitals")
#     teaching_parser.add_argument("--count", type=int, default=10, help="Number of hospitals to generate")
#     teaching_parser.add_argument("--output", type=str, help="Output file path (.json or .csv)")

#     args = parser.parse_args()

#     if args.command == "single":
#         generate_single_hospital()
#     elif args.command == "batch":
#         generate_hospitals_batch(args.count, args.output)
#     elif args.command == "type":
#         get_hospitals_by_type(args.type, args.count, args.output)
#     elif args.command == "service":
#         get_hospitals_by_service(args.service, args.count, args.output)
#     elif args.command == "department":
#         get_hospitals_by_department(args.department, args.count, args.output)
#     elif args.command == "beds":
#         get_hospitals_by_bed_count_range(args.min_beds, args.max_beds, args.count, args.output)
#     elif args.command == "emergency":
#         get_hospitals_with_emergency_services(args.count, args.output)
#     elif args.command == "teaching":
#         get_teaching_hospitals(args.count, args.output)
#     else:
#         parser.print_help()


# if __name__ == "__main__":
#     main()
