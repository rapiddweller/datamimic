# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
import uuid
from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil


class TransactionEntity(Entity):
    """Generate transaction data.

    This class generates realistic transaction data including transaction IDs,
    amounts, timestamps, types, and status.
    """

    # Transaction types
    TRANSACTION_TYPES = [
        "PURCHASE",
        "REFUND",
        "TRANSFER",
        "DEPOSIT",
        "WITHDRAWAL",
        "PAYMENT",
        "SUBSCRIPTION",
        "FEE",
        "INTEREST",
        "ADJUSTMENT",
    ]

    # Transaction statuses
    TRANSACTION_STATUSES = [
        "PENDING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "DECLINED",
        "PROCESSING",
        "AUTHORIZED",
        "SETTLED",
        "DISPUTED",
        "REFUNDED",
    ]

    # Currency codes
    CURRENCY_CODES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL"]

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        min_amount: float = 0.01,
        max_amount: float = 10000.00,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        dataset: str | None = None,
    ):
        """Initialize the TransactionEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code for localization
            min_amount: Minimum transaction amount
            max_amount: Maximum transaction amount
            start_date: Start date for transaction timestamps
            end_date: End date for transaction timestamps
            dataset: Optional dataset name
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._min_amount = min_amount
        self._max_amount = max_amount

        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.datetime.now() - datetime.timedelta(days=365)
        if end_date is None:
            end_date = datetime.datetime.now()

        self._start_date = start_date
        self._end_date = end_date

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "transaction_id": self._generate_transaction_id,
                "amount": self._generate_amount,
                "timestamp": self._generate_timestamp,
                "type": self._generate_type,
                "status": self._generate_status,
                "currency": self._generate_currency,
                "description": self._generate_description,
                "reference_id": self._generate_reference_id,
                "fee": self._generate_fee,
            }
        )

    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID."""
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"

    def _generate_amount(self) -> float:
        """Generate a random transaction amount."""
        return round(random.uniform(self._min_amount, self._max_amount), 2)

    def _generate_timestamp(self) -> datetime.datetime:
        """Generate a random timestamp within the specified range."""
        time_diff = self._end_date - self._start_date
        random_seconds = random.randint(0, int(time_diff.total_seconds()))
        return self._start_date + datetime.timedelta(seconds=random_seconds)

    def _generate_type(self) -> str:
        """Generate a random transaction type."""
        return random.choice(self.TRANSACTION_TYPES)

    def _generate_status(self) -> str:
        """Generate a random transaction status."""
        return random.choice(self.TRANSACTION_STATUSES)

    def _generate_currency(self) -> str:
        """Generate a random currency code."""
        return random.choice(self.CURRENCY_CODES)

    def _generate_description(self) -> str:
        """Generate a transaction description based on the type."""
        transaction_type = self.type
        descriptions = {
            "PURCHASE": [
                "Online purchase",
                "Retail store purchase",
                "Digital goods",
                "Subscription renewal",
                "In-app purchase",
            ],
            "REFUND": [
                "Refund for returned item",
                "Service cancellation refund",
                "Partial refund",
                "Overpayment refund",
            ],
            "TRANSFER": [
                "Funds transfer",
                "Account transfer",
                "Wire transfer",
                "P2P transfer",
                "International transfer",
            ],
            "DEPOSIT": ["Cash deposit", "Check deposit", "Direct deposit", "ATM deposit", "Mobile deposit"],
            "WITHDRAWAL": ["ATM withdrawal", "Cash withdrawal", "Bank withdrawal", "Scheduled withdrawal"],
            "PAYMENT": ["Bill payment", "Loan payment", "Credit card payment", "Utility payment", "Rent payment"],
            "SUBSCRIPTION": [
                "Monthly subscription",
                "Annual subscription",
                "Service subscription",
                "Content subscription",
            ],
            "FEE": ["Service fee", "Late payment fee", "Processing fee", "Foreign transaction fee", "ATM fee"],
            "INTEREST": ["Interest payment", "Interest earned", "Interest charged", "Accrued interest"],
            "ADJUSTMENT": ["Account adjustment", "Balance adjustment", "Correction", "Dispute adjustment"],
        }

        return random.choice(descriptions.get(transaction_type, ["Transaction"]))

    def _generate_reference_id(self) -> str:
        """Generate a reference ID for the transaction."""
        return f"REF-{uuid.uuid4().hex[:8].upper()}"

    def _generate_fee(self) -> float:
        """Generate a transaction fee."""
        # Generate a fee that's a small percentage of the transaction amount
        return round(self.amount * random.uniform(0.01, 0.05), 2)

    def reset(self) -> None:
        """Reset all field generators."""
        for generator in self._field_generators.values():
            generator.reset()

    @property
    def transaction_id(self) -> str:
        """Get the transaction ID."""
        value = self._field_generators["transaction_id"].get()
        assert value is not None, "transaction_id should not be None"
        return value

    @property
    def amount(self) -> float:
        """Get the transaction amount."""
        value = self._field_generators["amount"].get()
        assert value is not None, "amount should not be None"
        return value

    @property
    def timestamp(self) -> datetime.datetime:
        """Get the transaction timestamp."""
        value = self._field_generators["timestamp"].get()
        assert value is not None, "timestamp should not be None"
        return value

    @property
    def type(self) -> str:
        """Get the transaction type."""
        value = self._field_generators["type"].get()
        assert value is not None, "type should not be None"
        return value

    @property
    def status(self) -> str:
        """Get the transaction status."""
        value = self._field_generators["status"].get()
        assert value is not None, "status should not be None"
        return value

    @property
    def currency(self) -> str:
        """Get the transaction currency."""
        value = self._field_generators["currency"].get()
        assert value is not None, "currency should not be None"
        return value

    @property
    def description(self) -> str:
        """Get the transaction description."""
        value = self._field_generators["description"].get()
        assert value is not None, "description should not be None"
        return value

    @property
    def reference_id(self) -> str:
        """Get the reference ID."""
        value = self._field_generators["reference_id"].get()
        assert value is not None, "reference_id should not be None"
        return value

    @property
    def fee(self) -> float:
        """Get the transaction fee."""
        value = self._field_generators["fee"].get()
        assert value is not None, "fee should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the transaction entity to a dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "type": self.type,
            "status": self.status,
            "currency": self.currency,
            "description": self.description,
            "reference_id": self.reference_id,
            "fee": self.fee,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of transaction entities.

        Args:
            count: Number of transactions to generate

        Returns:
            List of transaction dictionaries
        """
        field_names = list(self._field_generators.keys())
        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
