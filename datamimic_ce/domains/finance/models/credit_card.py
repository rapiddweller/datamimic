# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Credit Card model.

This module defines the credit card model for the finance domain.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, validator


class CreditCardType(BaseModel):
    """Credit card type information."""

    type: str = Field(..., description="The type/brand of credit card (e.g., VISA, MASTERCARD)")
    prefixes: list[str] = Field(..., description="Valid prefixes for this card type")
    length: int = Field(16, description="Standard length of card numbers for this type")
    cvv_length: int = Field(3, description="Standard CVV length for this type")

    class Config:
        """Pydantic model configuration."""

        frozen = True


class CreditCard(BaseModel):
    """Credit card information."""

    id: str = Field(..., description="Unique identifier for the credit card")
    card_number: str = Field(..., description="The credit card number")
    card_holder: str = Field(..., description="The name of the cardholder")
    card_type: CreditCardType = Field(..., description="The type of credit card")
    expiration_month: int = Field(..., description="The expiration month (1-12)")
    expiration_year: int = Field(..., description="The expiration year (YYYY)")
    cvv: str = Field(..., description="The CVV security code")
    is_active: bool = Field(True, description="Whether the card is active")
    credit_limit: float = Field(..., description="The credit limit on the card")
    current_balance: float = Field(0.0, description="The current balance on the card")
    issue_date: date = Field(..., description="The date the card was issued")
    bank_name: str = Field(..., description="The name of the issuing bank")

    @property
    def expiration_date_str(self) -> str:
        """Get the expiration date as a formatted string (MM/YY)."""
        return f"{self.expiration_month:02d}/{self.expiration_year % 100:02d}"

    @property
    def is_expired(self) -> bool:
        """Check if the card is expired based on the current date."""
        now = datetime.now()
        if self.expiration_year < now.year:
            return True
        return bool(self.expiration_year == now.year and self.expiration_month < now.month)

    @property
    def masked_card_number(self) -> str:
        """Get a masked version of the card number, showing only the last 4 digits."""
        if len(self.card_number) <= 4:
            return self.card_number
        return "X" * (len(self.card_number) - 4) + self.card_number[-4:]

    @validator("expiration_month")
    def validate_expiration_month(cls, v):
        """Validate that the expiration month is between 1 and 12."""
        if not 1 <= v <= 12:
            raise ValueError("Expiration month must be between 1 and 12")
        return v

    class Config:
        """Pydantic model configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }
