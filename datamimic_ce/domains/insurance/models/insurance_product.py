# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Product model.

This module defines the insurance product model for the insurance domain.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class InsuranceCoverage(BaseModel):
    """Insurance coverage information."""
    
    id: str = Field(..., description="Unique identifier for the insurance coverage")
    name: str = Field(..., description="The name of the coverage")
    code: str = Field(..., description="The code of the coverage")
    description: str = Field(..., description="Description of what the coverage provides")
    min_coverage: float = Field(..., description="Minimum coverage amount")
    max_coverage: float = Field(..., description="Maximum coverage amount, can be infinite")
    
    class Config:
        """Pydantic model configuration."""
        
        frozen = True


class InsuranceProduct(BaseModel):
    """Insurance product information."""
    
    id: str = Field(..., description="Unique identifier for the insurance product")
    type: str = Field(..., description="The type of insurance product")
    code: str = Field(..., description="The product code")
    description: str = Field(..., description="Description of the insurance product")
    coverages: List[InsuranceCoverage] = Field([], description="List of coverages included in the product")
    
    class Config:
        """Pydantic model configuration."""
        
        frozen = True