# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Policy model.

This module defines the insurance policy model for the insurance domain.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from datamimic_ce.domains.insurance.models.insurance_company import InsuranceCompany
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceCoverage, InsuranceProduct


class PolicyHolder(BaseModel):
    """Policy holder information."""
    
    id: str = Field(..., description="Unique identifier for the policy holder")
    first_name: str = Field(..., description="First name of the policy holder")
    last_name: str = Field(..., description="Last name of the policy holder")
    email: str = Field(..., description="Email address of the policy holder")
    phone: str = Field(..., description="Phone number of the policy holder")
    address: str = Field(..., description="Address of the policy holder")
    city: str = Field(..., description="City of the policy holder")
    state: str = Field(..., description="State/province of the policy holder")
    postal_code: str = Field(..., description="Postal code of the policy holder")
    country: str = Field(..., description="Country of the policy holder")
    date_of_birth: date = Field(..., description="Date of birth of the policy holder")
    
    class Config:
        """Pydantic model configuration."""
        
        frozen = True
        json_encoders = {
            date: lambda v: v.isoformat(),
        }


class PolicyCoverage(BaseModel):
    """Policy coverage information."""
    
    coverage_id: str = Field(..., description="Reference to the coverage definition")
    name: str = Field(..., description="Name of the coverage")
    code: str = Field(..., description="Code of the coverage")
    coverage_amount: float = Field(..., description="The amount of coverage")
    deductible: float = Field(..., description="The deductible amount")
    
    class Config:
        """Pydantic model configuration."""
        
        frozen = True


class InsurancePolicy(BaseModel):
    """Insurance policy information."""
    
    id: str = Field(..., description="Unique identifier for the insurance policy")
    policy_number: str = Field(..., description="The policy number")
    company: InsuranceCompany = Field(..., description="The insurance company")
    product: InsuranceProduct = Field(..., description="The insurance product")
    policy_holder: PolicyHolder = Field(..., description="The policy holder")
    coverages: List[PolicyCoverage] = Field(..., description="List of coverages included in the policy")
    premium: float = Field(..., description="The premium amount")
    premium_frequency: str = Field("monthly", description="The frequency of premium payments (monthly, quarterly, annually)")
    start_date: date = Field(..., description="The start date of the policy")
    end_date: date = Field(..., description="The end date of the policy")
    status: str = Field("active", description="The status of the policy (active, expired, cancelled)")
    created_date: datetime = Field(..., description="The date the policy was created")
    
    @property
    def is_active(self) -> bool:
        """Check if the policy is currently active.
        
        Returns:
            True if the policy is active, False otherwise
        """
        return self.status == "active" and self.start_date <= date.today() <= self.end_date
    
    @property
    def total_coverage(self) -> float:
        """Calculate the total coverage amount across all coverages.
        
        Returns:
            The total coverage amount
        """
        return sum(coverage.coverage_amount for coverage in self.coverages)
    
    @property
    def annual_premium(self) -> float:
        """Calculate the annual premium amount.
        
        Returns:
            The annual premium amount
        """
        if self.premium_frequency == "monthly":
            return self.premium * 12
        elif self.premium_frequency == "quarterly":
            return self.premium * 4
        else:  # annually
            return self.premium
    
    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        """Validate that the end date is after the start date."""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v
    
    class Config:
        """Pydantic model configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }