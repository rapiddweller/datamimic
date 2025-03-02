# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office generator utilities.

This module provides utility functions for generating administration office data.
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


def generate_office_id() -> str:
    """Generate a unique office ID.

    Returns:
        A unique office ID
    """
    import uuid

    return f"ADM-{uuid.uuid4().hex[:8].upper()}"


def generate_office_name(office_type: str, jurisdiction: str, city: str, state: str) -> str:
    """Generate an office name.

    Args:
        office_type: The type of office
        jurisdiction: The jurisdiction of the office
        city: The city where the office is located
        state: The state where the office is located

    Returns:
        An office name
    """
    # Name formats
    name_formats = []
    
    if "Municipal" in office_type or "City" in office_type:
        name_formats = [
            f"{city} City Hall",
            f"{city} Municipal Building",
            f"{city} Government Center",
            f"City of {city} Administration",
            f"{city} Office of the Mayor",
        ]
    elif "County" in office_type:
        name_formats = [
            f"{city} County Administration Building",
            f"{city} County Government Center",
            f"{city} County Office Complex",
            f"{city} County Services Building",
            f"{state} County Courthouse",
        ]
    elif "State" in office_type:
        name_formats = [
            f"{state} State Office Building",
            f"{state} Department of Administration",
            f"{state} Government Complex",
            f"{state} Administrative Services",
            f"{state} Capitol Building",
        ]
    elif "Federal" in office_type:
        name_formats = [
            f"Federal Building - {city}",
            f"U.S. Government Center - {city}",
            f"Federal Administrative Building - {city}",
            f"U.S. Federal Complex - {city}",
            f"Federal Office Building - {city}",
        ]
    else:
        # Specialized agencies
        if "Tax" in office_type:
            name_formats = [
                f"{jurisdiction} Tax Office",
                f"{jurisdiction} Revenue Service",
                f"{jurisdiction} Department of Taxation",
                f"{jurisdiction} Tax Authority",
                f"Tax Commission of {jurisdiction}",
            ]
        elif "DMV" in office_type or "Motor" in office_type:
            name_formats = [
                f"{jurisdiction} Department of Motor Vehicles",
                f"{jurisdiction} DMV Office",
                f"{jurisdiction} Motor Vehicle Administration",
                f"{jurisdiction} Vehicle Registration Center",
                f"Bureau of Motor Vehicles - {jurisdiction}",
            ]
        elif "Social" in office_type or "Welfare" in office_type:
            name_formats = [
                f"{jurisdiction} Department of Social Services",
                f"{jurisdiction} Social Welfare Office",
                f"{jurisdiction} Human Services Agency",
                f"{jurisdiction} Social Security Office",
                f"Department of Human Services - {jurisdiction}",
            ]
        else:
            name_formats = [
                f"{jurisdiction} Government Office",
                f"{jurisdiction} Administrative Services",
                f"{jurisdiction} Public Administration Building",
                f"{jurisdiction} Civil Services Office",
                f"Public Administration Center - {jurisdiction}",
            ]
    
    if not name_formats:
        name_formats = [
            f"{jurisdiction} Government Office",
            f"{jurisdiction} Administrative Services",
            f"{jurisdiction} Public Administration Building",
            f"{jurisdiction} Civil Services Office",
            f"Public Administration Center - {jurisdiction}",
        ]
    
    return random.choice(name_formats)


def generate_office_type() -> str:
    """Generate an office type.

    Returns:
        An office type
    """
    types = [
        "Municipal Government Office",
        "City Administration",
        "County Government Office",
        "State Government Agency",
        "Federal Government Office",
        "Tax Office",
        "Department of Motor Vehicles",
        "Social Services Office",
        "Public Records Office",
        "Permits and Licensing Office",
        "Elections Office",
        "Public Works Administration",
        "Health Department",
        "Housing Authority",
        "Environmental Protection Agency",
        "Planning and Development Office",
    ]
    
    return random.choice(types)


def generate_jurisdiction(office_type: str, city: str, state: str) -> str:
    """Generate a jurisdiction based on office type.

    Args:
        office_type: The type of office
        city: The city where the office is located
        state: The state where the office is located

    Returns:
        A jurisdiction
    """
    if "Municipal" in office_type or "City" in office_type:
        return f"City of {city}"
    elif "County" in office_type:
        return f"{city} County"
    elif "State" in office_type:
        return f"State of {state}"
    elif "Federal" in office_type:
        return "Federal"
    else:
        # For specialized agencies, determine jurisdiction based on type
        jurisdictions = [f"City of {city}", f"{city} County", f"State of {state}", "Federal"]
        return random.choice(jurisdictions)


def generate_founding_year(office_type: str) -> int:
    """Generate a founding year based on office type.

    Args:
        office_type: The type of office

    Returns:
        A founding year
    """
    current_year = datetime.datetime.now().year
    
    # Different ranges based on type
    if "Federal" in office_type:
        # Federal offices tend to be older
        min_age = 20
        max_age = 200
    elif "State" in office_type:
        # State offices also have history
        min_age = 15
        max_age = 150
    elif "County" in office_type:
        min_age = 10
        max_age = 100
    else:
        # Local and specialized offices tend to be newer
        min_age = 5
        max_age = 75
    
    return current_year - random.randint(min_age, max_age)


def generate_staff_count(office_type: str) -> int:
    """Generate a staff count based on office type.

    Args:
        office_type: The type of office

    Returns:
        A staff count
    """
    # Staff size ranges based on office type
    if "Federal" in office_type:
        return random.randint(50, 500)
    elif "State" in office_type:
        return random.randint(30, 300)
    elif "County" in office_type:
        return random.randint(20, 150)
    elif "Municipal" in office_type or "City" in office_type:
        return random.randint(10, 100)
    else:
        # Specialized offices
        return random.randint(5, 75)


def generate_annual_budget(office_type: str, staff_count: int) -> float:
    """Generate an annual budget based on office type and staff count.

    Args:
        office_type: The type of office
        staff_count: The number of staff members

    Returns:
        An annual budget in dollars
    """
    # Budget calculation based on staff size and office type
    # Base budget per staff member (salary, benefits, overhead)
    base_per_staff = random.uniform(80000, 120000)
    
    # Additional budget based on office type
    if "Federal" in office_type:
        multiplier = random.uniform(1.5, 3.0)
    elif "State" in office_type:
        multiplier = random.uniform(1.2, 2.0)
    elif "County" in office_type:
        multiplier = random.uniform(1.0, 1.5)
    else:
        multiplier = random.uniform(0.8, 1.2)
    
    # Calculate total budget
    budget = staff_count * base_per_staff * multiplier
    
    # Add some randomization
    budget *= random.uniform(0.9, 1.1)
    
    # Round to nearest thousand
    return round(budget / 1000) * 1000


def generate_hours_of_operation() -> Dict[str, str]:
    """Generate hours of operation for a government office.

    Returns:
        A dictionary mapping days to hours
    """
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    weekend = ["Saturday", "Sunday"]
    hours = {}
    
    # Most government offices have standard hours on weekdays
    standard_open = random.choice(["8:00 AM", "8:30 AM", "9:00 AM"])
    standard_close = random.choice(["4:30 PM", "5:00 PM", "5:30 PM"])
    
    # Set weekday hours
    for day in weekdays:
        hours[day] = f"{standard_open} - {standard_close}"
    
    # Some offices have extended hours one day a week
    if random.random() < 0.3:  # 30% chance
        extended_day = random.choice(weekdays)
        extended_close = random.choice(["6:00 PM", "6:30 PM", "7:00 PM"])
        hours[extended_day] = f"{standard_open} - {extended_close}"
    
    # Some offices are open on Saturday
    if random.random() < 0.2:  # 20% chance
        saturday_open = random.choice(["9:00 AM", "10:00 AM"])
        saturday_close = random.choice(["1:00 PM", "2:00 PM", "3:00 PM"])
        hours["Saturday"] = f"{saturday_open} - {saturday_close}"
    else:
        hours["Saturday"] = "Closed"
    
    # Almost all government offices are closed on Sunday
    hours["Sunday"] = "Closed"
    
    return hours


def generate_government_website(jurisdiction: str) -> str:
    """Generate a government website URL.

    Args:
        jurisdiction: The jurisdiction of the office

    Returns:
        A website URL
    """
    # Clean up the jurisdiction for URL
    jurisdiction = jurisdiction.lower()
    url_name = jurisdiction.replace("city of ", "")
    url_name = url_name.replace("state of ", "")
    url_name = url_name.replace(" county", "county")
    url_name = url_name.replace(" ", "")
    url_name = ''.join(c for c in url_name if c.isalnum())
    
    # Determine domain extension based on jurisdiction
    domain = ".gov"  # All US government entities use .gov
    
    return f"https://www.{url_name}{domain}"


def generate_government_email(website: str, office_type: str) -> str:
    """Generate a government email address.

    Args:
        website: The office website
        office_type: The type of office

    Returns:
        An email address
    """
    # Extract domain from website
    domain = website.replace("https://www.", "")
    
    # Determine department from office type
    office_type = office_type.lower()
    
    if "tax" in office_type:
        department = "tax"
    elif "motor" in office_type or "dmv" in office_type:
        department = "dmv"
    elif "social" in office_type or "welfare" in office_type:
        department = "socialservices"
    elif "permit" in office_type or "licens" in office_type:
        department = "permits"
    elif "election" in office_type:
        department = "elections"
    elif "health" in office_type:
        department = "health"
    elif "housing" in office_type:
        department = "housing"
    elif "environment" in office_type:
        department = "environment"
    elif "planning" in office_type or "development" in office_type:
        department = "planning"
    else:
        department = "info"
    
    return f"{department}@{domain}"


def generate_government_services(office_type: str, count: int = None) -> List[str]:
    """Generate a list of government services based on office type.

    Args:
        office_type: The type of office
        count: The number of services to generate (default: random 5-10)

    Returns:
        A list of services
    """
    office_type = office_type.lower()
    
    # Common government services
    common_services = [
        "General Information",
        "Forms and Applications",
        "Records Management",
        "Document Certification",
        "Public Inquiries",
        "Complaint Processing",
    ]
    
    # Specialized services based on office type
    specialized_services = []
    
    if "tax" in office_type:
        specialized_services = [
            "Tax Filing Assistance",
            "Property Tax Assessment",
            "Tax Payment Processing",
            "Tax Appeals",
            "Business Tax Registration",
            "Tax Exemption Applications",
            "Tax Records Access",
        ]
    elif "motor" in office_type or "dmv" in office_type:
        specialized_services = [
            "Driver's License Issuance",
            "Vehicle Registration",
            "License Plate Issuance",
            "Driver Testing",
            "Vehicle Inspections",
            "ID Card Issuance",
            "Commercial Vehicle Licensing",
        ]
    elif "social" in office_type or "welfare" in office_type:
        specialized_services = [
            "Benefit Applications",
            "Case Management",
            "Financial Assistance Programs",
            "Food Assistance Programs",
            "Housing Assistance",
            "Elder Care Services",
            "Child Support Services",
            "Healthcare Enrollment Assistance",
        ]
    elif "permit" in office_type or "licens" in office_type:
        specialized_services = [
            "Business License Applications",
            "Professional Licensing",
            "Building Permits",
            "Special Event Permits",
            "Zoning Permits",
            "License Renewals",
            "Inspection Scheduling",
        ]
    elif "election" in office_type:
        specialized_services = [
            "Voter Registration",
            "Ballot Access Information",
            "Election Worker Recruitment",
            "Absentee Ballot Processing",
            "Election Results Reporting",
            "Polling Place Information",
            "Campaign Finance Reporting",
        ]
    elif "health" in office_type:
        specialized_services = [
            "Health Inspections",
            "Vaccination Programs",
            "Public Health Education",
            "Health Facility Licensing",
            "Epidemiological Services",
            "Birth and Death Certificates",
            "Health Code Enforcement",
        ]
    elif "housing" in office_type:
        specialized_services = [
            "Affordable Housing Programs",
            "Rental Assistance",
            "Housing Development Grants",
            "Homeless Services",
            "Housing Code Enforcement",
            "Fair Housing Complaints",
            "Home Repair Programs",
        ]
    elif "environment" in office_type:
        specialized_services = [
            "Environmental Permits",
            "Pollution Control",
            "Conservation Programs",
            "Environmental Inspections",
            "Water Quality Monitoring",
            "Air Quality Testing",
            "Recycling Programs",
            "Hazardous Waste Management",
        ]
    elif "planning" in office_type or "development" in office_type:
        specialized_services = [
            "Zoning Information",
            "Land Use Planning",
            "Development Review",
            "Economic Development Assistance",
            "Community Planning",
            "Infrastructure Planning",
            "Historic Preservation",
            "Urban Design Review",
        ]
    elif "municipal" in office_type or "city" in office_type:
        specialized_services = [
            "City Services Coordination",
            "Community Outreach",
            "City Council Support",
            "Budget Information",
            "Local Ordinance Information",
            "Public Space Permits",
            "Neighborhood Services",
        ]
    elif "county" in office_type:
        specialized_services = [
            "County Records",
            "Property Records",
            "Marriage Licenses",
            "County Tax Services",
            "Public Works Projects",
            "Parks and Recreation",
            "County Courts Administration",
        ]
    elif "state" in office_type:
        specialized_services = [
            "State Program Administration",
            "State Grants Management",
            "State Agency Coordination",
            "Legislative Affairs",
            "State Policy Implementation",
            "State Regulations Information",
            "State Budget Information",
        ]
    elif "federal" in office_type:
        specialized_services = [
            "Federal Program Information",
            "Federal Grants Administration",
            "Federal Agency Coordination",
            "Federal Records Access",
            "Regulatory Compliance Assistance",
            "Federal Benefits Information",
            "Congressional Liaison Services",
        ]
    
    # Choose services based on office type
    all_services = common_services + specialized_services
    
    # If no specialized services were found, use these general government services
    if not specialized_services:
        general_services = [
            "Public Records Access",
            "Permit Processing",
            "Fee Collection",
            "Administrative Hearings",
            "Public Meeting Coordination",
            "Community Outreach",
            "Regulatory Compliance",
        ]
        all_services = common_services + general_services
    
    # Choose a subset of services
    if count is None:
        count = random.randint(5, min(10, len(all_services)))
    else:
        count = min(count, len(all_services))
        
    return random.sample(all_services, count)


def generate_government_departments(office_type: str, count: int = None) -> List[str]:
    """Generate a list of government departments based on office type.

    Args:
        office_type: The type of office
        count: The number of departments to generate (default: random 3-7)

    Returns:
        A list of departments
    """
    office_type = office_type.lower()
    
    # Common departments found in most government offices
    common_departments = [
        "Administration",
        "Human Resources",
        "Finance",
        "Information Technology",
        "Public Relations",
        "Legal Affairs",
        "Customer Service",
    ]
    
    # Specialized departments based on office type
    specialized_departments = []
    
    if "tax" in office_type:
        specialized_departments = [
            "Tax Collection",
            "Tax Assessment",
            "Audit",
            "Appeals",
            "Business Tax",
            "Property Tax",
            "Tax Research",
        ]
    elif "motor" in office_type or "dmv" in office_type:
        specialized_departments = [
            "Driver Licensing",
            "Vehicle Registration",
            "Driver Testing",
            "Commercial Vehicles",
            "Enforcement",
            "Inspections",
            "Records",
        ]
    elif "social" in office_type or "welfare" in office_type:
        specialized_departments = [
            "Case Management",
            "Benefits Processing",
            "Family Services",
            "Elder Services",
            "Child Support",
            "Housing Assistance",
            "Employment Services",
        ]
    elif "permit" in office_type or "licens" in office_type:
        specialized_departments = [
            "Permit Processing",
            "Inspections",
            "Business Licensing",
            "Professional Licensing",
            "Compliance",
            "Records",
            "Fee Collection",
        ]
    elif "election" in office_type:
        specialized_departments = [
            "Voter Registration",
            "Ballot Processing",
            "Polling Operations",
            "Election Equipment",
            "Campaign Finance",
            "Election Research",
            "Voter Outreach",
        ]
    elif "municipal" in office_type or "city" in office_type:
        specialized_departments = [
            "Mayor's Office",
            "City Council Affairs",
            "Community Development",
            "Urban Planning",
            "Neighborhood Services",
            "Budget Office",
            "City Clerk",
        ]
    elif "county" in office_type:
        specialized_departments = [
            "County Clerk",
            "Property Records",
            "County Executive Office",
            "Board of Supervisors",
            "County Assessor",
            "County Treasurer",
            "Regional Planning",
        ]
    elif "state" in office_type:
        specialized_departments = [
            "Executive Affairs",
            "Legislative Liaison",
            "State Programs",
            "Policy Development",
            "Regulations",
            "State Grants",
            "Intergovernmental Relations",
        ]
    elif "federal" in office_type:
        specialized_departments = [
            "Program Administration",
            "Compliance",
            "Federal Grants",
            "Policy Implementation",
            "Congressional Affairs",
            "Regional Coordination",
            "Federal-State Relations",
        ]
    
    # Choose departments based on office type
    all_departments = common_departments + specialized_departments
    
    # If no specialized departments were found, use these general departments
    if not specialized_departments:
        general_departments = [
            "Operations",
            "Records Management",
            "Facilities",
            "Public Affairs",
            "Regulatory Affairs",
            "Administrative Services",
            "Policy Development",
        ]
        all_departments = common_departments + general_departments
    
    # Choose a subset of departments
    if count is None:
        count = random.randint(3, min(7, len(all_departments)))
    else:
        count = min(count, len(all_departments))
        
    return random.sample(all_departments, count)


def generate_leadership_position(office_type: str) -> str:
    """Generate a leadership position title based on office type.

    Args:
        office_type: The type of office

    Returns:
        A leadership position title
    """
    office_type = office_type.lower()
    
    if "municipal" in office_type or "city" in office_type:
        return random.choice(["Mayor", "City Manager", "Deputy Mayor", "City Administrator"])
    elif "county" in office_type:
        return random.choice(["County Executive", "Board Chair", "County Administrator", "County Commissioner"])
    elif "state" in office_type:
        return random.choice(["Agency Director", "Deputy Director", "State Administrator", "Division Head"])
    elif "federal" in office_type:
        return random.choice(["Director", "Deputy Director", "Administrator", "Program Director"])
    elif "tax" in office_type:
        return "Tax Commissioner"
    elif "motor" in office_type or "dmv" in office_type:
        return "DMV Administrator"
    elif "social" in office_type or "welfare" in office_type:
        return "Social Services Director"
    elif "permit" in office_type or "licens" in office_type:
        return "Licensing Director"
    elif "election" in office_type:
        return "Elections Supervisor"
    elif "health" in office_type:
        return "Health Director"
    elif "housing" in office_type:
        return "Housing Director"
    elif "environment" in office_type:
        return "Environmental Director"
    elif "planning" in office_type:
        return "Planning Director"
    else:
        return "Director"