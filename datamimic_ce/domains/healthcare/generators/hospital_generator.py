# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital generator utilities.

This module provides utility functions for generating hospital data.
"""

import random

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator


class HospitalGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None) -> None:
        self._dataset = dataset or "US"
        self._address_generator = AddressGenerator(dataset=self._dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=self._dataset)

    @property
    def dataset(self) -> str:
        """Get the dataset.

        Returns:
            The dataset.
        """
        return self._dataset

    @property
    def address_generator(self) -> AddressGenerator:
        """Get the address generator.

        Returns:
            The address generator.
        """
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        """Get the phone number generator.

        Returns:
            The phone number generator.
        """
        return self._phone_number_generator

    def generate_hospital_name(self, city: str, state: str) -> str:
        """Generate a hospital name based on location.

        Args:
            city: The city where the hospital is located.
            state: The state where the hospital is located.

        Returns:
            A hospital name.
        """
        # Define name patterns
        name_patterns = [
            "{city} General Hospital",
            "{city} Medical Center",
            "{city} Community Hospital",
            "{city} Regional Medical Center",
            "{city} Memorial Hospital",
            "{state} University Hospital",
            "{city} Methodist Hospital",
            "{city} Presbyterian Hospital",
            "{city} Baptist Medical Center",
            "{city} St. Mary's Hospital",
            "{city} St. Joseph's Hospital",
            "{city} Mercy Hospital",
            "{city} Children's Hospital",
            "{city} Veterans Hospital",
            "University of {state} Medical Center",
            "{city} Health System",
            "{city} Healthcare",
            "North {city} Medical Center",
            "South {city} Hospital",
            "East {city} Regional Hospital",
            "West {city} Medical Center",
            "{city} County Hospital",
            "{city} Memorial Health",
            "{city} Regional Health System",
            "{city} Medical Associates",
        ]

        # Select a random name pattern
        pattern = random.choice(name_patterns)

        # Fill in the pattern with the city and state
        return pattern.format(city=city, state=state)

    def get_hospital_type(self):
        default_hospital_types = [
            "General",
            "Teaching",
            "Community",
            "Specialty",
            "Rehabilitation",
            "Psychiatric",
            "Children's",
            "Veterans",
            "Long-term Care",
        ]
        return random.choice(default_hospital_types)

    def generate_departments(self, hospital_type: str, count: int | None = None) -> list[str]:
        """Generate a list of hospital departments.

        Returns:
            A list of hospital departments.
        """

        # Define common departments for all hospital types
        common_departments = [
            "Emergency",
            "Radiology",
            "Laboratory",
            "Pharmacy",
            "Administration",
        ]

        # Define specialty departments by hospital type
        specialty_departments = {
            "General": [
                "Internal Medicine",
                "Surgery",
                "Pediatrics",
                "Obstetrics and Gynecology",
                "Cardiology",
                "Neurology",
                "Orthopedics",
                "Oncology",
                "Psychiatry",
                "Urology",
                "Gastroenterology",
                "Pulmonology",
                "Nephrology",
                "Endocrinology",
            ],
            "Teaching": [
                "Internal Medicine",
                "Surgery",
                "Pediatrics",
                "Obstetrics and Gynecology",
                "Cardiology",
                "Neurology",
                "Orthopedics",
                "Oncology",
                "Psychiatry",
                "Urology",
                "Gastroenterology",
                "Pulmonology",
                "Nephrology",
                "Endocrinology",
                "Research",
                "Medical Education",
                "Residency Programs",
                "Fellowship Programs",
            ],
            "Community": [
                "Internal Medicine",
                "Surgery",
                "Pediatrics",
                "Obstetrics and Gynecology",
                "Cardiology",
                "Orthopedics",
                "Community Outreach",
                "Primary Care",
                "Family Medicine",
            ],
            "Specialty": [
                "Cardiology",
                "Neurology",
                "Orthopedics",
                "Oncology",
                "Pediatrics",
                "Women's Health",
                "Behavioral Health",
                "Rehabilitation",
            ],
            "Rehabilitation": [
                "Physical Therapy",
                "Occupational Therapy",
                "Speech Therapy",
                "Cardiac Rehabilitation",
                "Pulmonary Rehabilitation",
                "Neurological Rehabilitation",
                "Orthopedic Rehabilitation",
                "Spinal Cord Injury Rehabilitation",
                "Traumatic Brain Injury Rehabilitation",
            ],
            "Psychiatric": [
                "Adult Psychiatry",
                "Child and Adolescent Psychiatry",
                "Geriatric Psychiatry",
                "Addiction Treatment",
                "Mood Disorders",
                "Anxiety Disorders",
                "Psychotic Disorders",
                "Personality Disorders",
                "Eating Disorders",
                "Forensic Psychiatry",
            ],
            "Children's": [
                "Pediatric Emergency",
                "Neonatal Intensive Care",
                "Pediatric Intensive Care",
                "Pediatric Surgery",
                "Pediatric Cardiology",
                "Pediatric Neurology",
                "Pediatric Oncology",
                "Pediatric Orthopedics",
                "Pediatric Psychiatry",
                "Child Life Services",
                "Developmental Pediatrics",
            ],
            "Veterans": [
                "Primary Care",
                "Mental Health",
                "Surgery",
                "Rehabilitation",
                "Geriatrics",
                "Spinal Cord Injury",
                "Traumatic Brain Injury",
                "Prosthetics",
                "Post-Traumatic Stress Disorder",
                "Substance Abuse Treatment",
                "Veterans Benefits Counseling",
            ],
            "Long-term Care": [
                "Skilled Nursing",
                "Rehabilitation",
                "Memory Care",
                "Palliative Care",
                "Hospice Care",
                "Respiratory Therapy",
                "Wound Care",
                "Nutrition Services",
                "Social Services",
                "Activities and Recreation",
            ],
        }

        # Determine the number of departments to generate
        if count is None:
            if hospital_type == "Specialty":
                count = random.randint(5, 10)
            elif hospital_type == "Community":
                count = random.randint(8, 15)
            else:
                count = random.randint(10, 20)

        # Get the specialty departments for this hospital type
        type_departments = specialty_departments.get(hospital_type, [])

        # Combine common and specialty departments
        all_departments = common_departments + type_departments

        # Select random departments
        if count >= len(all_departments):
            return sorted(all_departments)
        else:
            return sorted(random.sample(all_departments, count))

    def generate_services(self, hospital_type: str, departments: list[str], count: int | None = None) -> list[str]:
        """Generate a list of hospital services.

        Returns:
            A list of hospital services.
        """

        # Define common services for all hospital types
        common_services = [
            "Diagnostic Imaging",
            "Laboratory Services",
            "Pharmacy Services",
            "Outpatient Care",
        ]

        # Define department-specific services
        department_services = {
            "Emergency": [
                "Emergency Care",
                "Trauma Care",
                "Urgent Care",
            ],
            "Surgery": [
                "General Surgery",
                "Minimally Invasive Surgery",
                "Outpatient Surgery",
                "Robotic Surgery",
            ],
            "Internal Medicine": [
                "Primary Care",
                "Preventive Medicine",
                "Chronic Disease Management",
            ],
            "Pediatrics": [
                "Pediatric Primary Care",
                "Pediatric Specialty Care",
                "Well-Child Visits",
                "Immunizations",
            ],
            "Obstetrics and Gynecology": [
                "Maternity Care",
                "Prenatal Care",
                "Labor and Delivery",
                "Gynecological Surgery",
                "Women's Health Services",
            ],
            "Cardiology": [
                "Cardiac Diagnostics",
                "Cardiac Rehabilitation",
                "Cardiac Catheterization",
                "Electrophysiology",
                "Heart Failure Management",
            ],
            "Neurology": [
                "Neurological Diagnostics",
                "Stroke Care",
                "Epilepsy Management",
                "Movement Disorders Treatment",
                "Headache Management",
            ],
            "Orthopedics": [
                "Joint Replacement",
                "Sports Medicine",
                "Fracture Care",
                "Spine Surgery",
                "Orthopedic Rehabilitation",
            ],
            "Oncology": [
                "Chemotherapy",
                "Radiation Therapy",
                "Surgical Oncology",
                "Cancer Screening",
                "Cancer Support Services",
            ],
            "Radiology": [
                "X-ray",
                "CT Scan",
                "MRI",
                "Ultrasound",
                "Mammography",
                "PET Scan",
                "Nuclear Medicine",
            ],
            "Physical Therapy": [
                "Orthopedic Rehabilitation",
                "Neurological Rehabilitation",
                "Sports Rehabilitation",
                "Post-surgical Rehabilitation",
            ],
            "Occupational Therapy": [
                "Activities of Daily Living Training",
                "Hand Therapy",
                "Cognitive Rehabilitation",
                "Pediatric Occupational Therapy",
            ],
            "Speech Therapy": [
                "Speech and Language Evaluation",
                "Swallowing Therapy",
                "Voice Therapy",
                "Cognitive-Communication Therapy",
            ],
            "Psychiatry": [
                "Inpatient Psychiatric Care",
                "Outpatient Psychiatric Care",
                "Medication Management",
                "Psychotherapy",
                "Crisis Intervention",
            ],
            "Rehabilitation": [
                "Inpatient Rehabilitation",
                "Outpatient Rehabilitation",
                "Cardiac Rehabilitation",
                "Pulmonary Rehabilitation",
                "Neurological Rehabilitation",
            ],
        }

        # Define specialty services by hospital type
        specialty_services = {
            "General": [
                "Intensive Care",
                "Inpatient Care",
                "Emergency Care",
                "Surgery",
                "Maternity Care",
                "Pediatric Care",
            ],
            "Teaching": [
                "Medical Education",
                "Clinical Research",
                "Specialized Treatments",
                "Advanced Diagnostics",
                "Transplant Services",
            ],
            "Community": [
                "Community Health Programs",
                "Preventive Care",
                "Health Education",
                "Wellness Programs",
                "Primary Care",
            ],
            "Specialty": [
                "Specialized Diagnostics",
                "Specialized Treatments",
                "Specialized Surgery",
                "Specialized Rehabilitation",
            ],
            "Rehabilitation": [
                "Physical Rehabilitation",
                "Occupational Rehabilitation",
                "Speech Rehabilitation",
                "Cognitive Rehabilitation",
                "Vocational Rehabilitation",
            ],
            "Psychiatric": [
                "Mental Health Assessment",
                "Psychiatric Medication Management",
                "Individual Therapy",
                "Group Therapy",
                "Family Therapy",
                "Crisis Intervention",
            ],
            "Children's": [
                "Pediatric Emergency Care",
                "Pediatric Surgery",
                "Neonatal Intensive Care",
                "Pediatric Intensive Care",
                "Child Life Services",
                "Pediatric Specialty Care",
            ],
            "Veterans": [
                "Veterans Health Services",
                "PTSD Treatment",
                "Prosthetics Services",
                "Veterans Benefits Counseling",
                "Military Transition Support",
            ],
            "Long-term Care": [
                "Skilled Nursing Care",
                "Rehabilitation Services",
                "Memory Care",
                "Palliative Care",
                "Hospice Care",
                "Respite Care",
            ],
        }

        # Collect services based on departments
        department_specific_services = []
        for department in departments:
            if department in department_services:
                department_specific_services.extend(department_services[department])

        # Get the specialty services for this hospital type
        type_services = specialty_services.get(hospital_type, [])

        # Combine all services
        all_services = common_services + department_specific_services + type_services

        # Remove duplicates
        all_services = list(set(all_services))

        # Determine the number of services to generate
        if count is None:
            if hospital_type == "Specialty":
                count = random.randint(10, 20)
            elif hospital_type == "Community":
                count = random.randint(15, 25)
            else:
                count = random.randint(20, 40)

        # Select random services
        if count >= len(all_services):
            return sorted(all_services)
        else:
            return sorted(random.sample(all_services, count))

    def generate_accreditation(self, hospital_type: str) -> list[str]:
        """Generate a list of hospital accreditations.

        Returns:
            A list of accreditations held by the hospital.
        """

        # Define common accreditations for all hospital types
        common_accreditations = [
            "Joint Commission",
            "DNV GL Healthcare",
            "Healthcare Facilities Accreditation Program (HFAP)",
        ]

        # Define specialty accreditations by hospital type
        specialty_accreditations = {
            "General": [
                "American College of Surgeons Commission on Cancer (CoC)",
                "American College of Radiology (ACR)",
                "College of American Pathologists (CAP)",
            ],
            "Teaching": [
                "Accreditation Council for Graduate Medical Education (ACGME)",
                "Liaison Committee on Medical Education (LCME)",
                "American College of Surgeons Commission on Cancer (CoC)",
                "National Accreditation Program for Breast Centers (NAPBC)",
            ],
            "Community": [
                "National Committee for Quality Assurance (NCQA)",
                "American College of Radiology (ACR)",
            ],
            "Specialty": [
                "Commission on Accreditation of Rehabilitation Facilities (CARF)",
                "American College of Surgeons Commission on Cancer (CoC)",
                "American College of Radiology (ACR)",
            ],
            "Rehabilitation": [
                "Commission on Accreditation of Rehabilitation Facilities (CARF)",
                "American Academy of Physical Medicine and Rehabilitation",
            ],
            "Psychiatric": [
                "Commission on Accreditation of Rehabilitation Facilities (CARF)",
                "American Psychological Association (APA)",
            ],
            "Children's": [
                "Children's Hospital Association",
                "American Academy of Pediatrics",
            ],
            "Veterans": [
                "Department of Veterans Affairs",
                "Commission on Accreditation of Rehabilitation Facilities (CARF)",
            ],
            "Long-term Care": [
                "Commission on Accreditation of Rehabilitation Facilities (CARF)",
                "National Committee for Quality Assurance (NCQA)",
            ],
        }

        # Get the specialty accreditations for this hospital type
        type_accreditations = specialty_accreditations.get(hospital_type, [])

        # Combine common and specialty accreditations
        all_accreditations = common_accreditations + type_accreditations

        # Determine how many accreditations to include
        num_accreditations = random.randint(1, min(4, len(all_accreditations)))

        # Select random accreditations
        return random.sample(all_accreditations, num_accreditations)
