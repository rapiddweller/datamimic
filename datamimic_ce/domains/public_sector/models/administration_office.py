# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office entity model.

This module provides the AdministrationOffice entity model for generating
realistic public administration office data.
"""

from typing import Any, ClassVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.public_sector.data_loaders.administration_loader import AdministrationDataLoader


class AdministrationOffice(BaseEntity):
    """Generate administration office data.

    This class generates realistic public administration office data including
    office IDs, names, types, jurisdictions, addresses, contact information,
    staff counts, budgets, services, and departments.

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
        """Initialize the AdministrationOffice entity.

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
        self._data_loader = AdministrationDataLoader()

        # Initialize address entity for address information
        self._address_entity = self._class_factory_util.get_address_entity(locale=locale, dataset=dataset)

        # Initialize field generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize all field generators."""
        # Basic information
        self._office_id_generator = PropertyCache(self._generate_office_id)
        self._name_generator = PropertyCache(self._generate_name)
        self._type_generator = PropertyCache(self._generate_type)
        self._jurisdiction_generator = PropertyCache(self._generate_jurisdiction)
        self._founding_year_generator = PropertyCache(self._generate_founding_year)
        self._staff_count_generator = PropertyCache(self._generate_staff_count)
        self._annual_budget_generator = PropertyCache(self._generate_annual_budget)
        self._hours_of_operation_generator = PropertyCache(self._generate_hours_of_operation)
        self._website_generator = PropertyCache(self._generate_website)
        self._email_generator = PropertyCache(self._generate_email)
        self._phone_generator = PropertyCache(self._generate_phone)
        self._services_generator = PropertyCache(self._generate_services)
        self._departments_generator = PropertyCache(self._generate_departments)
        self._leadership_generator = PropertyCache(self._generate_leadership)

    def reset(self) -> None:
        """Reset all field generators, causing new values to be generated on the next access."""
        self._address_entity.reset()
        self._office_id_generator.reset()
        self._name_generator.reset()
        self._type_generator.reset()
        self._jurisdiction_generator.reset()
        self._founding_year_generator.reset()
        self._staff_count_generator.reset()
        self._annual_budget_generator.reset()
        self._hours_of_operation_generator.reset()
        self._website_generator.reset()
        self._email_generator.reset()
        self._phone_generator.reset()
        self._services_generator.reset()
        self._departments_generator.reset()
        self._leadership_generator.reset()

    def to_dict(self) -> dict[str, Any]:
        """Convert the administration office entity to a dictionary.

        Returns:
            A dictionary containing all administration office properties.
        """
        return {
            "office_id": self.office_id,
            "name": self.name,
            "type": self.type,
            "jurisdiction": self.jurisdiction,
            "founding_year": self.founding_year,
            "staff_count": self.staff_count,
            "annual_budget": self.annual_budget,
            "hours_of_operation": self.hours_of_operation,
            "website": self.website,
            "email": self.email,
            "phone": self.phone,
            "services": self.services,
            "departments": self.departments,
            "leadership": self.leadership,
            "address": self.address,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of administration office entities.

        Args:
            count: The number of administration office entities to generate.

        Returns:
            A list of dictionaries containing the generated administration office entities.
        """
        offices = []
        for _ in range(count):
            offices.append(self.to_dict())
            self.reset()
        return offices

    # Property getters
    @property
    def office_id(self) -> str:
        """Get the office ID.

        Returns:
            A unique identifier for the office.
        """
        return self._office_id_generator.get()

    @property
    def name(self) -> str:
        """Get the office name.

        Returns:
            The office name.
        """
        return self._name_generator.get()

    @property
    def type(self) -> str:
        """Get the office type.

        Returns:
            The office type.
        """
        return self._type_generator.get()

    @property
    def jurisdiction(self) -> str:
        """Get the jurisdiction.

        Returns:
            The jurisdiction.
        """
        return self._jurisdiction_generator.get()

    @property
    def founding_year(self) -> int:
        """Get the founding year.

        Returns:
            The founding year.
        """
        return self._founding_year_generator.get()

    @property
    def staff_count(self) -> int:
        """Get the staff count.

        Returns:
            The number of staff members.
        """
        return self._staff_count_generator.get()

    @property
    def annual_budget(self) -> float:
        """Get the annual budget.

        Returns:
            The annual budget in dollars.
        """
        return self._annual_budget_generator.get()

    @property
    def hours_of_operation(self) -> dict[str, str]:
        """Get the hours of operation.

        Returns:
            A dictionary mapping days to hours.
        """
        return self._hours_of_operation_generator.get()

    @property
    def website(self) -> str:
        """Get the office website.

        Returns:
            The office website URL.
        """
        return self._website_generator.get()

    @property
    def email(self) -> str:
        """Get the office email address.

        Returns:
            The office email address.
        """
        return self._email_generator.get()

    @property
    def phone(self) -> str:
        """Get the office phone number.

        Returns:
            The office phone number.
        """
        return self._phone_generator.get()

    @property
    def services(self) -> list[str]:
        """Get the services offered.

        Returns:
            A list of services.
        """
        return self._services_generator.get()

    @property
    def departments(self) -> list[str]:
        """Get the departments.

        Returns:
            A list of departments.
        """
        return self._departments_generator.get()

    @property
    def leadership(self) -> dict[str, str]:
        """Get the office leadership.

        Returns:
            A dictionary mapping leadership positions to names.
        """
        return self._leadership_generator.get()

    @property
    def address(self) -> dict[str, Any]:
        """Get the office address.

        Returns:
            A dictionary containing the office's address information.
        """
        return self._address_entity.to_dict()

    # Generator methods
    def _generate_office_id(self) -> str:
        """Generate a unique office ID.

        Returns:
            A unique office ID.
        """
        import uuid

        return f"ADM-{uuid.uuid4().hex[:8].upper()}"

    def _generate_name(self) -> str:
        """Generate an office name.

        Returns:
            An office name.
        """
        import random
        
        # Get location information for naming
        city = self._address_entity.city
        state = self._address_entity.state
        
        # Generate office name based on type and jurisdiction
        office_type = self.type
        jurisdiction = self.jurisdiction
        
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

    def _generate_type(self) -> str:
        """Generate an office type.

        Returns:
            An office type.
        """
        import random
        
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

    def _generate_jurisdiction(self) -> str:
        """Generate a jurisdiction.

        Returns:
            A jurisdiction.
        """
        import random
        
        office_type = self.type
        city = self._address_entity.city
        state = self._address_entity.state
        
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

    def _generate_founding_year(self) -> int:
        """Generate a founding year.

        Returns:
            A founding year.
        """
        import random
        import datetime
        
        current_year = datetime.datetime.now().year
        office_type = self.type
        
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

    def _generate_staff_count(self) -> int:
        """Generate a staff count.

        Returns:
            A staff count.
        """
        import random
        
        office_type = self.type
        
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

    def _generate_annual_budget(self) -> float:
        """Generate an annual budget.

        Returns:
            An annual budget in dollars.
        """
        import random
        
        office_type = self.type
        staff_count = self.staff_count
        
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

    def _generate_hours_of_operation(self) -> dict[str, str]:
        """Generate hours of operation.

        Returns:
            A dictionary mapping days to hours.
        """
        import random
        
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

    def _generate_website(self) -> str:
        """Generate a website URL.

        Returns:
            A website URL.
        """
        # Derive from jurisdiction
        jurisdiction = self.jurisdiction.lower()
        
        # Clean up the jurisdiction for URL
        url_name = jurisdiction.replace("city of ", "")
        url_name = url_name.replace("state of ", "")
        url_name = url_name.replace(" county", "county")
        url_name = url_name.replace(" ", "")
        url_name = ''.join(c for c in url_name if c.isalnum())
        
        # Determine domain extension based on jurisdiction
        if "federal" in self.jurisdiction.lower():
            domain = ".gov"
        else:
            domain = ".gov"  # All US government entities use .gov
        
        return f"https://www.{url_name}{domain}"

    def _generate_email(self) -> str:
        """Generate an email address.

        Returns:
            An email address.
        """
        # Extract domain from website
        website = self.website
        domain = website.replace("https://www.", "")
        
        # Determine department from office type
        office_type = self.type.lower()
        
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

    def _generate_services(self) -> list[str]:
        """Generate a list of services offered.

        Returns:
            A list of services.
        """
        import random
        
        office_type = self.type.lower()
        
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
        num_services = random.randint(5, min(10, len(all_services)))
        return random.sample(all_services, num_services)

    def _generate_departments(self) -> list[str]:
        """Generate a list of departments.

        Returns:
            A list of departments.
        """
        import random
        
        office_type = self.type.lower()
        
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
        num_departments = random.randint(3, min(7, len(all_departments)))
        return random.sample(all_departments, num_departments)

    def _generate_leadership(self) -> dict[str, str]:
        """Generate leadership information.

        Returns:
            A dictionary mapping leadership positions to names.
        """
        import random
        
        # Get a person entity for name generation
        person_entity = self._class_factory_util.get_person_entity(locale=self._locale, dataset=self._dataset)
        
        office_type = self.type.lower()
        leadership = {}
        
        # Generate leader titles based on office type
        if "municipal" in office_type or "city" in office_type:
            leadership["Mayor"] = f"{person_entity.first_name} {person_entity.last_name}"
            leadership["City Manager"] = f"{person_entity.reset().first_name} {person_entity.last_name}"
        elif "county" in office_type:
            leadership["County Executive"] = f"{person_entity.first_name} {person_entity.last_name}"
            leadership["Board Chair"] = f"{person_entity.reset().first_name} {person_entity.last_name}"
        elif "state" in office_type:
            leadership["Agency Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            leadership["Deputy Director"] = f"{person_entity.reset().first_name} {person_entity.last_name}"
        elif "federal" in office_type:
            leadership["Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            leadership["Deputy Director"] = f"{person_entity.reset().first_name} {person_entity.last_name}"
        else:
            # Specialized offices
            if "tax" in office_type:
                leadership["Tax Commissioner"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "motor" in office_type or "dmv" in office_type:
                leadership["DMV Administrator"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "social" in office_type or "welfare" in office_type:
                leadership["Social Services Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "permit" in office_type or "licens" in office_type:
                leadership["Licensing Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "election" in office_type:
                leadership["Elections Supervisor"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "health" in office_type:
                leadership["Health Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "housing" in office_type:
                leadership["Housing Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "environment" in office_type:
                leadership["Environmental Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            elif "planning" in office_type:
                leadership["Planning Director"] = f"{person_entity.first_name} {person_entity.last_name}"
            else:
                leadership["Director"] = f"{person_entity.first_name} {person_entity.last_name}"
        
        # Add administrative positions that exist in nearly all offices
        leadership["Administrative Officer"] = f"{person_entity.reset().first_name} {person_entity.last_name}"
        
        # Randomly add more leadership positions
        possible_positions = [
            "Public Affairs Manager",
            "Chief Financial Officer",
            "Operations Manager",
            "HR Director",
            "Legal Counsel",
            "IT Director",
            "Chief of Staff",
        ]
        
        # Add 1-3 additional positions
        num_additional = random.randint(1, 3)
        selected_positions = random.sample(possible_positions, num_additional)
        
        for position in selected_positions:
            leadership[position] = f"{person_entity.reset().first_name} {person_entity.last_name}"
        
        return leadership