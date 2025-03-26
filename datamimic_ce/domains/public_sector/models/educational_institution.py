# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Educational institution entity model.

This module provides the EducationalInstitution entity model for generating
realistic educational institution data.
"""

import random
import uuid
from datetime import datetime
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)


class EducationalInstitution(BaseEntity):
    """Generate educational institution data.

    This class generates realistic educational institution data including
    school IDs, names, types, levels, addresses, contact information,
    staff counts, student counts, programs, and accreditations.

    It uses AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    def __init__(self, educational_institution_generator: EducationalInstitutionGenerator):
        super().__init__()
        self._educational_institution_generator = educational_institution_generator

    # Property getters
    @property
    @property_cache
    def institution_id(self) -> str:
        """Get the institution ID.

        Returns:
            A unique identifier for the institution.
        """
        return f"EDU-{uuid.uuid4().hex[:8].upper()}"

    @property
    @property_cache
    def name(self) -> str:
        """Get the institution name.

        Returns:
            The institution name.
        """
        # Get city or address information for naming
        city = self.address.city
        state = self.address.state

        # Generate institution name based on type and level
        institution_type = self.type
        level = self.level

        # Name formats
        name_formats = []

        if "University" in institution_type:
            name_formats = [
                f"{city} University",
                f"University of {city}",
                f"{state} State University",
                f"{city} Technical University",
                f"{city} Metropolitan University",
            ]
        elif "College" in institution_type:
            name_formats = [
                f"{city} College",
                f"{city} Community College",
                f"{state} College",
                f"{city} Technical College",
                f"{city} Liberal Arts College",
            ]
        elif "School" in institution_type:
            if "Elementary" in level:
                name_formats = [
                    f"{city} Elementary School",
                    f"{city} Primary School",
                    f"{city} Academy",
                    f"Washington Elementary School of {city}",
                    "Lincoln Elementary School",
                ]
            elif "Middle" in level:
                name_formats = [
                    f"{city} Middle School",
                    f"{city} Intermediate School",
                    f"{city} Junior High School",
                    "Jefferson Middle School",
                    "Roosevelt Middle School",
                ]
            elif "High" in level:
                name_formats = [
                    f"{city} High School",
                    f"{city} Senior High School",
                    f"{state} High School",
                    "Kennedy High School",
                    "Roosevelt High School",
                ]
            else:
                name_formats = [
                    f"{city} Academy",
                    f"{city} School",
                    f"{city} {level} School",
                    f"{state} Academy",
                    f"Central School of {city}",
                ]

        if not name_formats:
            name_formats = [
                f"{city} Education Center",
                f"{city} Learning Institute",
                f"{city} Academy",
                f"{state} Institute",
                f"Central Institute of {city}",
            ]

        return random.choice(name_formats)

    @property
    @property_cache
    def type(self) -> str:
        """Get the institution type.

        Returns:
            The institution type.
        """
        types = [
            "Public School",
            "Private School",
            "Charter School",
            "Magnet School",
            "Community College",
            "Public University",
            "Private University",
            "Research University",
            "Technical Institute",
            "Liberal Arts College",
            "Vocational School",
            "Special Education School",
        ]

        return random.choice(types)

    @property
    @property_cache
    def level(self) -> str:
        """Get the education level.

        Returns:
            The education level.
        """
        institution_type = self.type

        if "University" in institution_type or "College" in institution_type:
            levels = ["Higher Education", "Undergraduate", "Graduate", "Postgraduate"]
        elif "School" in institution_type:
            if "Vocational" in institution_type:
                levels = ["Vocational Education", "Technical Education", "Adult Education"]
            elif "Special" in institution_type:
                levels = ["Special Education", "K-12"]
            else:
                levels = ["Elementary", "Middle School", "High School", "K-12"]
        else:
            levels = ["Elementary", "Middle School", "High School", "Higher Education", "Vocational Education"]

        return random.choice(levels)

    @property
    @property_cache
    def founding_year(self) -> int:
        """Get the founding year.

        Returns:
            The founding year.
        """
        current_year = datetime.now().year
        min_age = 5  # Minimum age for a school
        max_age = 200  # Maximum age for a school (oldest universities)

        # Adjust based on institution type - universities tend to be older
        if "University" in self.type:
            min_age = 20
            max_age = 300
        elif "College" in self.type:
            min_age = 15
            max_age = 150

        return current_year - random.randint(min_age, max_age)

    @property
    @property_cache
    def student_count(self) -> int:
        """Get the student count.

        Returns:
            The number of students.
        """
        institution_type = self.type
        level = self.level

        # Adjust student count ranges based on institution type and level
        if "University" in institution_type:
            return random.randint(5000, 40000)
        elif "College" in institution_type:
            return random.randint(1000, 15000)
        elif "School" in institution_type:
            if "Elementary" in level:
                return random.randint(200, 800)
            elif "Middle" in level:
                return random.randint(300, 1000)
            elif "High" in level:
                return random.randint(500, 2500)
            else:
                return random.randint(200, 1500)
        else:
            return random.randint(100, 5000)

    @property
    @property_cache
    def staff_count(self) -> int:
        """Get the staff count.

        Returns:
            The number of staff members.
        """
        student_count = self.student_count
        student_to_staff_ratio = random.uniform(10, 25)  # Average student-to-staff ratio

        return max(5, int(student_count / student_to_staff_ratio))

    @property
    @property_cache
    def website(self) -> str:
        """Get the institution website.

        Returns:
            The institution website URL.
        """
        # Derive from name
        name = self.name.lower()

        # Simplified name for URL
        url_name = name.replace(" ", "")
        url_name = "".join(c for c in url_name if c.isalnum())

        # Determine domain extension based on type
        if "University" in self.type or "College" in self.type:
            domain = ".edu"
        elif "School" in self.type and "Public" in self.type:
            domain = ".k12.us"
        else:
            domain = ".org"

        return f"https://www.{url_name}{domain}"

    @property
    @property_cache
    def email(self) -> str:
        """Get the institution email address.

        Returns:
            The institution email address.
        """

        # Extract domain from website
        website = self.website
        domain = website.replace("https://www.", "")

        return f"info@{domain}"

    @property
    @property_cache
    def phone(self) -> str:
        """Get the institution phone number.

        Returns:
            The institution phone number.
        """
        return self._educational_institution_generator.phone_number_generator.generate()

    @property
    @property_cache
    def programs(self) -> list[str]:
        """Get the educational programs offered.

        Returns:
            A list of programs.
        """
        level = self.level

        # Define programs by level
        elementary_programs = [
            "Early Childhood Education",
            "Elementary Education",
            "Reading and Literacy",
            "Math Fundamentals",
            "Science Discovery",
            "Arts and Music",
            "Physical Education",
            "Special Education",
            "Gifted and Talented Program",
            "After-School Programs",
        ]

        middle_school_programs = [
            "Language Arts",
            "Mathematics",
            "Science",
            "Social Studies",
            "Physical Education",
            "Foreign Languages",
            "Technology Education",
            "Visual and Performing Arts",
            "Health Education",
            "Career Exploration",
        ]

        high_school_programs = [
            "English/Literature",
            "Mathematics",
            "Biology",
            "Chemistry",
            "Physics",
            "History",
            "Economics",
            "Computer Science",
            "Foreign Languages",
            "Advanced Placement (AP)",
            "International Baccalaureate (IB)",
            "Technical Education",
            "Business Studies",
            "Performing Arts",
            "Physical Education",
            "Sports Teams",
        ]

        higher_education_programs = [
            "Business Administration",
            "Computer Science",
            "Engineering",
            "Life Sciences",
            "Physical Sciences",
            "Social Sciences",
            "Humanities",
            "Arts",
            "Health Sciences",
            "Education",
            "Law",
            "Medicine",
            "Architecture",
            "Agriculture",
            "Environmental Studies",
            "Communications",
            "Mathematics",
            "Psychology",
            "Economics",
            "Political Science",
        ]

        vocational_programs = [
            "Automotive Technology",
            "Construction Trades",
            "Culinary Arts",
            "Healthcare Technology",
            "Information Technology",
            "Manufacturing Technology",
            "Cosmetology",
            "Hospitality Management",
            "Digital Media",
            "Electrical Technology",
            "HVAC Technology",
            "Plumbing Technology",
            "Welding",
            "Aviation Technology",
            "Agriculture Technology",
        ]

        # Select appropriate programs based on level
        if "Elementary" in level:
            all_programs = elementary_programs
        elif "Middle" in level:
            all_programs = middle_school_programs
        elif "High" in level:
            all_programs = high_school_programs
        elif "Higher" in level or "Undergraduate" in level or "Graduate" in level or "Postgraduate" in level:
            all_programs = higher_education_programs
        elif "Vocational" in level or "Technical" in level:
            all_programs = vocational_programs
        else:
            # Mix of programs
            all_programs = elementary_programs + middle_school_programs + high_school_programs

        # Choose a subset of programs
        num_programs = random.randint(3, min(10, len(all_programs)))
        return random.sample(all_programs, num_programs)

    @property
    @property_cache
    def accreditations(self) -> list[str]:
        """Get the institution accreditations.

        Returns:
            A list of accreditations.
        """
        institution_type = self.type

        # Different accreditation bodies for different institution types
        k12_accreditations = [
            "Cognia (formerly AdvancED)",
            "Middle States Association of Colleges and Schools",
            "National Association of Independent Schools (NAIS)",
            "National Blue Ribbon Schools Program",
            "International Baccalaureate (IB) World School",
            "Western Association of Schools and Colleges (WASC)",
            "New England Association of Schools and Colleges (NEASC)",
            "Southern Association of Colleges and Schools (SACS)",
        ]

        higher_ed_accreditations = [
            "Higher Learning Commission (HLC)",
            "Middle States Commission on Higher Education (MSCHE)",
            "New England Commission of Higher Education (NECHE)",
            "Northwest Commission on Colleges and Universities (NWCCU)",
            "Southern Association of Colleges and Schools Commission on Colleges (SACSCOC)",
            "WASC Senior College and University Commission (WSCUC)",
            "Accreditation Council for Business Schools and Programs (ACBSP)",
            "Accreditation Board for Engineering and Technology (ABET)",
            "Commission on Collegiate Nursing Education (CCNE)",
            "Council for the Accreditation of Educator Preparation (CAEP)",
        ]

        vocational_accreditations = [
            "Council on Occupational Education (COE)",
            "Accrediting Commission of Career Schools and Colleges (ACCSC)",
            "National Accrediting Commission of Career Arts and Sciences (NACCAS)",
            "Accrediting Bureau of Health Education Schools (ABHES)",
            "Distance Education Accrediting Commission (DEAC)",
        ]

        # Select appropriate accreditations based on institution type and level
        if "University" in institution_type or "College" in institution_type:
            accreditation_list = higher_ed_accreditations
        elif "Vocational" in institution_type or "Technical" in institution_type:
            accreditation_list = vocational_accreditations
        else:
            accreditation_list = k12_accreditations

        # Choose a subset of accreditations
        num_accreditations = random.randint(1, min(3, len(accreditation_list)))
        return random.sample(accreditation_list, num_accreditations)

    @property
    @property_cache
    def facilities(self) -> list[str]:
        """Get the institution facilities.

        Returns:
            A list of facilities.
        """
        import random

        institution_type = self.type

        # Common facilities for all institution types
        common_facilities = [
            "Library",
            "Computer Lab",
            "Cafeteria",
            "Administrative Offices",
            "Classrooms",
            "Gymnasium",
            "Auditorium",
            "Sports Fields",
            "Parking",
        ]

        # Specialized facilities by institution type
        k12_facilities = [
            "Playground",
            "Music Room",
            "Art Studio",
            "Science Labs",
            "Counseling Center",
            "Health Office",
            "Special Education Classrooms",
        ]

        higher_ed_facilities = [
            "Research Labs",
            "Lecture Halls",
            "Student Union",
            "Dormitories/Residence Halls",
            "Faculty Offices",
            "Health Center",
            "Fitness Center",
            "Bookstore",
            "Career Services Center",
            "Technology Center",
            "Recreation Center",
            "Performance Spaces",
            "Student Services Building",
            "International Student Center",
            "Graduate Student Center",
        ]

        vocational_facilities = [
            "Workshops",
            "Training Laboratories",
            "Simulation Centers",
            "Automotive Shop",
            "Culinary Kitchen",
            "Construction Workshop",
            "Healthcare Simulation Lab",
            "Welding Shop",
            "Electrical Lab",
            "IT Training Center",
        ]

        # Combine appropriate facilities based on institution type
        all_facilities = common_facilities.copy()

        if "University" in institution_type or "College" in institution_type:
            all_facilities.extend(higher_ed_facilities)
        elif "Vocational" in institution_type or "Technical" in institution_type:
            all_facilities.extend(vocational_facilities)
        else:
            all_facilities.extend(k12_facilities)

        # Choose a subset of facilities
        num_facilities = random.randint(5, min(15, len(all_facilities)))
        return random.sample(all_facilities, num_facilities)

    @property
    @property_cache
    def address(self) -> Address:
        """Get the institution address.

        Returns:
            A dictionary containing the institution's address information.
        """
        return Address(self._educational_institution_generator.address_generator)

    def to_dict(self) -> dict[str, Any]:
        """Convert the educational institution entity to a dictionary.

        Returns:
            A dictionary containing all educational institution properties.
        """
        return {
            "institution_id": self.institution_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "founding_year": self.founding_year,
            "student_count": self.student_count,
            "staff_count": self.staff_count,
            "website": self.website,
            "email": self.email,
            "phone": self.phone,
            "programs": self.programs,
            "accreditations": self.accreditations,
            "facilities": self.facilities,
            "address": self.address,
        }
