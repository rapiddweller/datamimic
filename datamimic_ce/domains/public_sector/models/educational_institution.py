# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Educational institution entity model.

This module provides the EducationalInstitution entity model for generating
realistic educational institution data.
"""

from typing import Any, ClassVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.public_sector.data_loaders.education_loader import EducationDataLoader


class EducationalInstitution(BaseEntity):
    """Generate educational institution data.

    This class generates realistic educational institution data including
    school IDs, names, types, levels, addresses, contact information,
    staff counts, student counts, programs, and accreditations.

    It uses AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Class-level cache for shared data
    _DATA_CACHE: ClassVar[dict[str, Any]] = {}

    def __init__(
        self,
        class_factory_util: Any,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the EducationalInstitution entity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._dataset = dataset
        self._country_code = dataset or "US"

        # Initialize data loader
        self._data_loader = EducationDataLoader()

        # Initialize address entity for address information
        self._address_entity = self._class_factory_util.get_address_entity(locale=locale, dataset=dataset)

        # Initialize field generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize all field generators."""
        # Basic information
        self._institution_id_generator = PropertyCache(self._generate_institution_id)
        self._name_generator = PropertyCache(self._generate_name)
        self._type_generator = PropertyCache(self._generate_type)
        self._level_generator = PropertyCache(self._generate_level)
        self._founding_year_generator = PropertyCache(self._generate_founding_year)
        self._student_count_generator = PropertyCache(self._generate_student_count)
        self._staff_count_generator = PropertyCache(self._generate_staff_count)
        self._website_generator = PropertyCache(self._generate_website)
        self._email_generator = PropertyCache(self._generate_email)
        self._phone_generator = PropertyCache(self._generate_phone)
        self._programs_generator = PropertyCache(self._generate_programs)
        self._accreditations_generator = PropertyCache(self._generate_accreditations)
        self._facilities_generator = PropertyCache(self._generate_facilities)

    def reset(self) -> None:
        """Reset all field generators, causing new values to be generated on the next access."""
        self._address_entity.reset()
        self._institution_id_generator.reset()
        self._name_generator.reset()
        self._type_generator.reset()
        self._level_generator.reset()
        self._founding_year_generator.reset()
        self._student_count_generator.reset()
        self._staff_count_generator.reset()
        self._website_generator.reset()
        self._email_generator.reset()
        self._phone_generator.reset()
        self._programs_generator.reset()
        self._accreditations_generator.reset()
        self._facilities_generator.reset()

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

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of educational institution entities.

        Args:
            count: The number of educational institution entities to generate.

        Returns:
            A list of dictionaries containing the generated educational institution entities.
        """
        institutions = []
        for _ in range(count):
            institutions.append(self.to_dict())
            self.reset()
        return institutions

    # Property getters
    @property
    def institution_id(self) -> str:
        """Get the institution ID.

        Returns:
            A unique identifier for the institution.
        """
        return self._institution_id_generator.get()

    @property
    def name(self) -> str:
        """Get the institution name.

        Returns:
            The institution name.
        """
        return self._name_generator.get()

    @property
    def type(self) -> str:
        """Get the institution type.

        Returns:
            The institution type.
        """
        return self._type_generator.get()

    @property
    def level(self) -> str:
        """Get the education level.

        Returns:
            The education level.
        """
        return self._level_generator.get()

    @property
    def founding_year(self) -> int:
        """Get the founding year.

        Returns:
            The founding year.
        """
        return self._founding_year_generator.get()

    @property
    def student_count(self) -> int:
        """Get the student count.

        Returns:
            The number of students.
        """
        return self._student_count_generator.get()

    @property
    def staff_count(self) -> int:
        """Get the staff count.

        Returns:
            The number of staff members.
        """
        return self._staff_count_generator.get()

    @property
    def website(self) -> str:
        """Get the institution website.

        Returns:
            The institution website URL.
        """
        return self._website_generator.get()

    @property
    def email(self) -> str:
        """Get the institution email address.

        Returns:
            The institution email address.
        """
        return self._email_generator.get()

    @property
    def phone(self) -> str:
        """Get the institution phone number.

        Returns:
            The institution phone number.
        """
        return self._phone_generator.get()

    @property
    def programs(self) -> list[str]:
        """Get the educational programs offered.

        Returns:
            A list of programs.
        """
        return self._programs_generator.get()

    @property
    def accreditations(self) -> list[str]:
        """Get the institution accreditations.

        Returns:
            A list of accreditations.
        """
        return self._accreditations_generator.get()

    @property
    def facilities(self) -> list[str]:
        """Get the institution facilities.

        Returns:
            A list of facilities.
        """
        return self._facilities_generator.get()

    @property
    def address(self) -> dict[str, Any]:
        """Get the institution address.

        Returns:
            A dictionary containing the institution's address information.
        """
        return self._address_entity.to_dict()

    # Generator methods
    def _generate_institution_id(self) -> str:
        """Generate a unique institution ID.

        Returns:
            A unique institution ID.
        """
        import uuid

        return f"EDU-{uuid.uuid4().hex[:8].upper()}"

    def _generate_name(self) -> str:
        """Generate an institution name.

        Returns:
            An institution name.
        """
        import random
        
        # Get city or address information for naming
        city = self._address_entity.city
        state = self._address_entity.state
        
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
                    f"Lincoln Elementary School",
                ]
            elif "Middle" in level:
                name_formats = [
                    f"{city} Middle School",
                    f"{city} Intermediate School",
                    f"{city} Junior High School",
                    f"Jefferson Middle School",
                    f"Roosevelt Middle School",
                ]
            elif "High" in level:
                name_formats = [
                    f"{city} High School",
                    f"{city} Senior High School",
                    f"{state} High School",
                    f"Kennedy High School",
                    f"Roosevelt High School",
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

    def _generate_type(self) -> str:
        """Generate an institution type.

        Returns:
            An institution type.
        """
        import random
        
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

    def _generate_level(self) -> str:
        """Generate an education level.

        Returns:
            An education level.
        """
        import random
        
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

    def _generate_founding_year(self) -> int:
        """Generate a founding year.

        Returns:
            A founding year.
        """
        import random
        import datetime
        
        current_year = datetime.datetime.now().year
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

    def _generate_student_count(self) -> int:
        """Generate a student count.

        Returns:
            A student count.
        """
        import random
        
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

    def _generate_staff_count(self) -> int:
        """Generate a staff count.

        Returns:
            A staff count.
        """
        import random
        
        # Make staff count proportional to student count
        student_count = self.student_count
        student_to_staff_ratio = random.uniform(10, 25)  # Average student-to-staff ratio
        
        return max(5, int(student_count / student_to_staff_ratio))

    def _generate_website(self) -> str:
        """Generate a website URL.

        Returns:
            A website URL.
        """
        # Derive from name
        name = self.name.lower()
        
        # Simplified name for URL
        url_name = name.replace(" ", "")
        url_name = ''.join(c for c in url_name if c.isalnum())
        
        # Determine domain extension based on type
        if "University" in self.type or "College" in self.type:
            domain = ".edu"
        elif "School" in self.type and "Public" in self.type:
            domain = ".k12.us"
        else:
            domain = ".org"
        
        return f"https://www.{url_name}{domain}"

    def _generate_email(self) -> str:
        """Generate an email address.

        Returns:
            An email address.
        """
        name = self.name.lower()
        
        # Extract domain from website
        website = self.website
        domain = website.replace("https://www.", "")
        
        return f"info@{domain}"

    def _generate_phone(self) -> str:
        """Generate a phone number.

        Returns:
            A formatted phone number.
        """
        import random

        area_code = random.randint(100, 999)
        prefix = random.randint(100, 999)
        line = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line}"

    def _generate_programs(self) -> list[str]:
        """Generate a list of educational programs.

        Returns:
            A list of programs.
        """
        import random
        
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

    def _generate_accreditations(self) -> list[str]:
        """Generate a list of accreditations.

        Returns:
            A list of accreditations.
        """
        import random
        
        institution_type = self.type
        level = self.level
        
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

    def _generate_facilities(self) -> list[str]:
        """Generate a list of facilities.

        Returns:
            A list of facilities.
        """
        import random
        
        institution_type = self.type
        level = self.level
        
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