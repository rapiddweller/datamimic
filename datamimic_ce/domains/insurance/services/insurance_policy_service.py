# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Policy Service.

This module provides service functions for generating and managing insurance policies.
"""

import random
import string
import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany
from datamimic_ce.domains.insurance.models.insurance_policy import InsurancePolicy, PolicyCoverage, PolicyHolder
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceCoverage, InsuranceProduct
from datamimic_ce.domains.insurance.services.insurance_company_service import InsuranceCompanyService
from datamimic_ce.domains.insurance.services.insurance_product_service import InsuranceProductService


class InsurancePolicyService:
    """Service for generating and managing insurance policies."""
    
    def __init__(self, dataset: str = "US"):
        """Initialize the insurance policy service.
        
        Args:
            dataset: The country code (e.g., "US", "DE") to use for data generation.
        """
        self.dataset = dataset
        self.company_service = InsuranceCompanyService(dataset)
        self.product_service = InsuranceProductService(dataset)
        self.person_generator = PersonGenerator()
        self.address_generator = AddressGenerator(locale=dataset.lower() if dataset in ["US", "DE"] else "us")
    
    def generate_policy_number(self) -> str:
        """Generate a random policy number.
        
        Returns:
            A randomly generated policy number.
        """
        # Format: 2 letters + 8 digits
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        digits = ''.join(random.choices(string.digits, k=8))
        return f"{letters}-{digits}"
    
    def generate_policy_holder(self) -> PolicyHolder:
        """Generate a random policy holder.
        
        Returns:
            A PolicyHolder object with randomly generated data.
        """
        # Generate person data
        person_data = self.person_generator.generate()
        address_data = self.address_generator.generate()
        
        # Generate a random date of birth between 18 and 80 years ago
        age = random.randint(18, 80)
        dob = date.today() - timedelta(days=age * 365)
        
        # Create and return a PolicyHolder object
        return PolicyHolder(
            id=str(uuid.uuid4()),
            first_name=person_data.get("firstName", "John"),
            last_name=person_data.get("lastName", "Doe"),
            email=person_data.get("email", f"{person_data.get('firstName', 'John').lower()}.{person_data.get('lastName', 'Doe').lower()}@example.com"),
            phone=person_data.get("phoneNumber", "555-123-4567"),
            address=address_data.get("streetAddress", "123 Main St"),
            city=address_data.get("city", "Anytown"),
            state=address_data.get("state", "CA"),
            postal_code=address_data.get("zipCode", "12345"),
            country=self.dataset,
            date_of_birth=dob,
        )
    
    def generate_policy_coverage(self, coverage: InsuranceCoverage) -> PolicyCoverage:
        """Generate a policy coverage from a coverage definition.
        
        Args:
            coverage: The coverage definition to use
            
        Returns:
            A PolicyCoverage object for the policy.
        """
        # Generate a random coverage amount within the min and max range
        min_coverage = coverage.min_coverage
        max_coverage = coverage.max_coverage
        
        # Handle infinite coverage
        if max_coverage == float('inf'):
            if min_coverage > 0:
                # For infinite max, use a range of 1x to 5x the minimum
                coverage_amount = round(min_coverage * random.uniform(1.0, 5.0))
            else:
                # Fallback to a reasonable range if min is 0
                coverage_amount = round(random.uniform(10000, 1000000))
        else:
            # Normal case: range between min and max
            coverage_amount = round(random.uniform(min_coverage, max_coverage))
        
        # Generate a random deductible based on the coverage amount (typically 0-5% of coverage)
        deductible = round(coverage_amount * random.uniform(0, 0.05))
        
        # Create and return a PolicyCoverage object
        return PolicyCoverage(
            coverage_id=coverage.id,
            name=coverage.name,
            code=coverage.code,
            coverage_amount=coverage_amount,
            deductible=deductible,
        )
    
    def calculate_premium(self, product: InsuranceProduct, coverages: List[PolicyCoverage],
                         policy_holder: PolicyHolder) -> float:
        """Calculate a premium based on the product, coverages, and policy holder.
        
        Args:
            product: The insurance product
            coverages: The policy coverages
            policy_holder: The policy holder
            
        Returns:
            The calculated premium amount.
        """
        # Base premium depends on the product type
        if product.code == "AUTO":
            base_premium = 500
        elif product.code == "HOME":
            base_premium = 800
        elif product.code == "LIFE":
            base_premium = 300
        elif product.code == "HLTH":
            base_premium = 450
        else:
            base_premium = 600
        
        # Adjust based on total coverage
        total_coverage = sum(c.coverage_amount for c in coverages)
        coverage_factor = 1.0 + (total_coverage / 1000000) * 0.1  # 10% increase per $1M of coverage
        
        # Adjust based on policy holder age (example: higher for older people)
        today = date.today()
        age = today.year - policy_holder.date_of_birth.year - (
            (today.month, today.day) < (policy_holder.date_of_birth.month, policy_holder.date_of_birth.day)
        )
        age_factor = 1.0 + max(0, (age - 30) / 100)  # 1% increase per year over 30
        
        # Calculate the final premium
        premium = base_premium * coverage_factor * age_factor
        
        # Add a random variation factor (±20%)
        variation = random.uniform(0.8, 1.2)
        premium *= variation
        
        # Round to nearest dollar
        return round(premium, 2)
    
    def generate_policy_dates(self) -> Tuple[date, date]:
        """Generate random start and end dates for a policy.
        
        Returns:
            A tuple of (start_date, end_date).
        """
        # Generate a start date between 2 years ago and 1 month from now
        days_ago = random.randint(-30, 2 * 365)
        start_date = date.today() - timedelta(days=days_ago)
        
        # Generate an end date 6 months to 1 year after the start date
        days_duration = random.randint(180, 365)
        end_date = start_date + timedelta(days=days_duration)
        
        return start_date, end_date
    
    def generate_insurance_policy(
        self,
        company: Optional[InsuranceCompany] = None,
        product: Optional[InsuranceProduct] = None,
        policy_holder: Optional[PolicyHolder] = None,
    ) -> InsurancePolicy:
        """Generate a random insurance policy.
        
        Args:
            company: Optional predefined company to use
            product: Optional predefined product to use
            policy_holder: Optional predefined policy holder to use
            
        Returns:
            An InsurancePolicy object with randomly generated data.
        """
        # Generate a company if not provided
        if company is None:
            company = self.company_service.generate_insurance_company()
        
        # Generate a product if not provided
        if product is None:
            product = self.product_service.generate_insurance_product()
        
        # Generate a policy holder if not provided
        if policy_holder is None:
            policy_holder = self.generate_policy_holder()
        
        # Generate policy coverages from product coverages
        policy_coverages = [self.generate_policy_coverage(c) for c in product.coverages]
        
        # Generate policy dates
        start_date, end_date = self.generate_policy_dates()
        
        # Generate premium
        premium = self.calculate_premium(product, policy_coverages, policy_holder)
        
        # Choose a premium frequency
        premium_frequency = random.choice(["monthly", "quarterly", "annually"])
        
        # Adjust the premium based on the frequency
        if premium_frequency == "annually":
            premium *= 0.95  # 5% discount for annual payment
        elif premium_frequency == "quarterly":
            premium *= 0.98  # 2% discount for quarterly payment
        premium = round(premium, 2)
        
        # Determine policy status
        if start_date <= date.today() <= end_date:
            status = "active"
        elif date.today() < start_date:
            status = "pending"
        else:
            status = "expired"
        
        # Create and return an InsurancePolicy object
        return InsurancePolicy(
            id=str(uuid.uuid4()),
            policy_number=self.generate_policy_number(),
            company=company,
            product=product,
            policy_holder=policy_holder,
            coverages=policy_coverages,
            premium=premium,
            premium_frequency=premium_frequency,
            start_date=start_date,
            end_date=end_date,
            status=status,
            created_date=datetime.now() - timedelta(days=random.randint(0, 30)),
        )
    
    def generate_insurance_policies(self, count: int = 1) -> List[InsurancePolicy]:
        """Generate multiple random insurance policies.
        
        Args:
            count: The number of insurance policies to generate
            
        Returns:
            A list of InsurancePolicy objects with randomly generated data.
        """
        return [self.generate_insurance_policy() for _ in range(count)]