# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Educational institution generator utilities.

This module provides utility functions for generating educational institution data.
"""

import random
import datetime
from typing import TypeVar, List, Dict, Any

T = TypeVar("T")  # Define a type variable for generic typing


def weighted_choice(choices: list[tuple[T, float]]) -> T:
    """Choose a random item from a weighted list.

    Args:
        choices: A list of tuples containing items and their weights

    Returns:
        A randomly selected item based on weights
    """
    if not choices:
        raise ValueError("Cannot make a weighted choice from an empty list")

    # Extract items and weights
    items = [item for item, _ in choices]
    weights = [weight for _, weight in choices]

    # Make a weighted choice
    return random.choices(items, weights=weights, k=1)[0]


def generate_institution_id() -> str:
    """Generate a unique institution ID.

    Returns:
        A unique institution ID
    """
    import uuid

    return f"EDU-{uuid.uuid4().hex[:8].upper()}"


def generate_institution_name(institution_type: str, level: str, city: str, state: str) -> str:
    """Generate an institution name.

    Args:
        institution_type: The type of institution
        level: The education level
        city: The city where the institution is located
        state: The state where the institution is located

    Returns:
        An institution name
    """
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


def generate_institution_type() -> str:
    """Generate an institution type.

    Returns:
        An institution type
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


def generate_education_level(institution_type: str) -> str:
    """Generate an education level based on institution type.

    Args:
        institution_type: The type of institution

    Returns:
        An education level
    """
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


def generate_founding_year(institution_type: str) -> int:
    """Generate a founding year based on institution type.

    Args:
        institution_type: The type of institution

    Returns:
        A founding year
    """
    current_year = datetime.datetime.now().year
    min_age = 5  # Minimum age for a school
    max_age = 200  # Maximum age for a school (oldest universities)
    
    # Adjust based on institution type - universities tend to be older
    if "University" in institution_type:
        min_age = 20
        max_age = 300
    elif "College" in institution_type:
        min_age = 15
        max_age = 150
    
    return current_year - random.randint(min_age, max_age)


def generate_student_count(institution_type: str, level: str) -> int:
    """Generate a student count based on institution type and level.

    Args:
        institution_type: The type of institution
        level: The education level

    Returns:
        A student count
    """
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


def generate_staff_count(student_count: int) -> int:
    """Generate a staff count based on student count.

    Args:
        student_count: The number of students

    Returns:
        A staff count
    """
    # Make staff count proportional to student count
    student_to_staff_ratio = random.uniform(10, 25)  # Average student-to-staff ratio
    
    return max(5, int(student_count / student_to_staff_ratio))


def generate_institution_website(name: str, institution_type: str) -> str:
    """Generate a website URL for an institution.

    Args:
        name: The institution name
        institution_type: The type of institution

    Returns:
        A website URL
    """
    # Simplified name for URL
    url_name = name.lower().replace(" ", "")
    url_name = ''.join(c for c in url_name if c.isalnum())
    
    # Determine domain extension based on type
    if "University" in institution_type or "College" in institution_type:
        domain = ".edu"
    elif "School" in institution_type and "Public" in institution_type:
        domain = ".k12.us"
    else:
        domain = ".org"
    
    return f"https://www.{url_name}{domain}"


def generate_institution_email(website: str) -> str:
    """Generate an email address for an institution.

    Args:
        website: The institution website

    Returns:
        An email address
    """
    # Extract domain from website
    domain = website.replace("https://www.", "")
    
    return f"info@{domain}"


def generate_educational_programs(level: str, count: int = None) -> List[str]:
    """Generate a list of educational programs based on education level.

    Args:
        level: The education level
        count: The number of programs to generate (default: random 3-10)

    Returns:
        A list of educational programs
    """
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
    if count is None:
        count = random.randint(3, min(10, len(all_programs)))
    else:
        count = min(count, len(all_programs))
        
    return random.sample(all_programs, count)


def generate_accreditations(institution_type: str, level: str, count: int = None) -> List[str]:
    """Generate a list of accreditations based on institution type and level.

    Args:
        institution_type: The type of institution
        level: The education level
        count: The number of accreditations to generate (default: random 1-3)

    Returns:
        A list of accreditations
    """
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
    if count is None:
        count = random.randint(1, min(3, len(accreditation_list)))
    else:
        count = min(count, len(accreditation_list))
        
    return random.sample(accreditation_list, count)


def generate_facilities(institution_type: str, level: str, count: int = None) -> List[str]:
    """Generate a list of facilities based on institution type and level.

    Args:
        institution_type: The type of institution
        level: The education level
        count: The number of facilities to generate (default: random 5-15)

    Returns:
        A list of facilities
    """
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
    if count is None:
        count = random.randint(5, min(15, len(all_facilities)))
    else:
        count = min(count, len(all_facilities))
        
    return random.sample(all_facilities, count)