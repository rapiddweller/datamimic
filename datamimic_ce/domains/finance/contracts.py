# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Typed transaction payload contracts owned by the finance domain."""

from datetime import datetime

from typing_extensions import NotRequired, TypedDict


class TransactionTypeData(TypedDict):
    type: str
    direction: str


class CurrencyData(TypedDict):
    code: str
    symbol: str
    name: NotRequired[str]


class GeneratedTransactionData(TypedDict):
    type: str
    direction: str
    merchant: str
    merchant_category: str
    amount: float
    currency_code: str
    currency_symbol: str
    status: str
    channel: str
    location: str
    reference_number: str
    description: str


class BankAccountData(TypedDict):
    account_number: str
    iban: str
    account_type: str
    balance: float
    currency: str
    created_date: datetime
    last_transaction_date: datetime
    bank_name: str
    bank_code: str
    bic: str
    bin: str


class TransactionData(TypedDict):
    transaction_id: str
    transaction_date: datetime
    amount: float
    transaction_type: str
    description: str
    reference_number: str
    status: str
    currency: str
    currency_symbol: str
    merchant_name: str
    merchant_category: str
    location: str
    is_international: bool
    channel: str
    direction: str
    account: NotRequired[BankAccountData]
