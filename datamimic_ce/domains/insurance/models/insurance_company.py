# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Insurance Company model.

This module defines the insurance company model for the insurance domain.
"""

from typing import Optional

from pydantic import BaseModel, Field


class InsuranceCompany(BaseModel):
    """Insurance company information."""
    
    id: str = Field(..., description="Unique identifier for the insurance company")
    name: str = Field(..., description="The name of the insurance company")
    code: str = Field(..., description="The code of the insurance company")
    founded_year: str = Field(..., description="The year the insurance company was founded")
    headquarters: str = Field(..., description="The headquarters location of the insurance company")
    website: str = Field(..., description="The website of the insurance company")
    logo_url: Optional[str] = Field(None, description="URL to the company logo")
    
    class Config:
        """Pydantic model configuration."""
        
        frozen = True