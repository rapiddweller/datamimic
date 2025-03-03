# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Bank Account model.

This module defines the bank account model for the finance domain.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class Bank(BaseModel):
    """Bank information associated with a bank account."""

    name: str = Field(..., description="The name of the bank")
    swift_code: str = Field(..., description="The SWIFT/BIC code of the bank")
    routing_number: str | None = Field(None, description="The routing number (US specific)")

    class Config:
        """Pydantic model configuration."""

        frozen = True


class BankAccount(BaseModel):
    """Bank account information."""

    id: str = Field(..., description="Unique identifier for the bank account")
    account_number: str = Field(..., description="The account number")
    iban: str | None = Field(None, description="International Bank Account Number")
    account_type: str = Field(..., description="The type of account (e.g., CHECKING, SAVINGS)")
    bank: Bank = Field(..., description="The bank associated with this account")
    balance: float = Field(0.0, description="Current balance of the account")
    currency: str = Field("USD", description="The currency code for the account")
    created_date: datetime = Field(..., description="Date when the account was created")
    last_transaction_date: datetime | None = Field(None, description="Date of the last transaction")

    class Config:
        """Pydantic model configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }
