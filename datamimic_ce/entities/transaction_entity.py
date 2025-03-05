# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil


class TransactionEntity(Entity):
    """Entity for generating synthetic transaction data.

    This class generates realistic transaction data including transaction IDs,
    dates, times, types, amounts, currencies, statuses, sources, destinations,
    descriptions, and metadata.
    """

    # Transaction types
    TRANSACTION_TYPES = [
        "PAYMENT",
        "DEPOSIT",
        "WITHDRAWAL",
        "TRANSFER",
        "REFUND",
        "FEE",
        "PURCHASE",
        "SALE",
        "EXCHANGE",
        "ADJUSTMENT",
    ]

    # Transaction statuses
    STATUSES = [
        "COMPLETED",
        "PENDING",
        "FAILED",
        "CANCELLED",
        "DECLINED",
        "REFUNDED",
        "PROCESSING",
        "AUTHORIZED",
        "SETTLED",
        "DISPUTED",
    ]

    # Currency codes
    CURRENCIES = [
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CAD",
        "AUD",
        "CHF",
        "CNY",
        "INR",
        "BTC",
        "ETH",
    ]

    # Source and destination types
    ACCOUNT_TYPES = [
        "BANK_ACCOUNT",
        "CREDIT_CARD",
        "DEBIT_CARD",
        "DIGITAL_WALLET",
        "CRYPTO_WALLET",
        "PAYMENT_GATEWAY",
        "CASH",
        "CHECK",
        "WIRE_TRANSFER",
        "MOBILE_PAYMENT",
    ]

    # Device types for metadata
    DEVICE_TYPES = [
        "DESKTOP",
        "LAPTOP",
        "MOBILE",
        "TABLET",
        "ATM",
        "POS_TERMINAL",
        "KIOSK",
        "SMART_WATCH",
        "SMART_TV",
        "IOT_DEVICE",
    ]

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        dataset: str | None = None,
        min_amount: float = 0.01,
        max_amount: float = 10000.00,
        transaction_type: str | None = None,
        currency: str | None = None,
        status: str | None = None,
    ):
        """Initialize the TransactionEntity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            min_amount: The minimum transaction amount.
            max_amount: The maximum transaction amount.
            transaction_type: The transaction type to use (if None, a random type will be generated).
            currency: The currency to use (if None, a random currency will be generated).
            status: The transaction status to use (if None, a random status will be generated).
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._data_generation_util = class_factory_util.get_data_generation_util()

        # Store custom parameters
        self._min_amount = min_amount
        self._max_amount = max_amount
        self._transaction_type = transaction_type
        self._currency = currency
        self._status = status
        self._locale = locale  # Ensure locale is stored correctly

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "transaction_id": self._generate_transaction_id,
                "date": self._generate_date,
                "time": self._generate_time,
                "type": self._generate_type,
                "amount": self._generate_amount,
                "currency": self._generate_currency,
                "status": self._generate_status,
                "source": self._generate_source,
                "destination": self._generate_destination,
                "description": self._generate_description,
                "metadata": self._generate_metadata,
            }
        )

    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID.

        Returns:
            A string representing the transaction ID.
        """
        return f"TXN-{random.randint(10000, 99999)}-{uuid.uuid4().hex[:8].upper()}"

    def _generate_date(self) -> str:
        """Generate a random transaction date within the last year.

        Returns:
            A string representing the date in YYYY-MM-DD format.
        """
        days_ago = random.randint(0, 365)  # Within the last year
        transaction_date = datetime.now() - timedelta(days=days_ago)
        return transaction_date.strftime("%Y-%m-%d")

    def _generate_time(self) -> str:
        """Generate a random transaction time.

        Returns:
            A string representing the time in HH:MM:SS format.
        """
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return f"{hour:02d}:{minute:02d}:{second:02d}"

    def _generate_amount(self) -> float:
        """Generate a random transaction amount."""
        return round(random.uniform(self._min_amount, self._max_amount), 2)

    def _generate_type(self) -> str:
        """Generate a random transaction type."""
        if self._transaction_type:
            return self._transaction_type
        return random.choice(self.TRANSACTION_TYPES)

    def _generate_status(self) -> str:
        """Generate a random transaction status."""
        if self._status:
            return self._status
        return random.choice(self.STATUSES)

    def _generate_currency(self) -> str:
        """Generate a random currency code."""
        if self._currency:
            return self._currency
        return random.choice(self.CURRENCIES)

    def _generate_source(self) -> str:
        """Generate a transaction source.

        Returns:
            A string representing the transaction source.
        """
        source_type = random.choice(self.ACCOUNT_TYPES)
        source_id = f"{source_type}-{random.randint(1000, 9999)}"
        return source_id

    def _generate_destination(self) -> str:
        """Generate a transaction destination.

        Returns:
            A string representing the transaction destination.
        """
        destination_type = random.choice(self.ACCOUNT_TYPES)
        destination_id = f"{destination_type}-{random.randint(1000, 9999)}"
        return destination_id

    def _generate_metadata(self) -> dict[str, Any]:
        """Generate transaction metadata.

        Returns:
            A dictionary containing transaction metadata.
        """
        # Generate a random IP address
        ip_octets = [str(random.randint(1, 255)) for _ in range(4)]
        ip_address = ".".join(ip_octets)

        # Generate a random device
        device = random.choice(self.DEVICE_TYPES)

        # Generate a random location
        cities = [
            "New York",
            "Los Angeles",
            "Chicago",
            "Houston",
            "Phoenix",
            "Philadelphia",
            "San Antonio",
            "San Diego",
        ]
        states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA"]
        location_idx = random.randint(0, len(cities) - 1)
        location = f"{cities[location_idx]}, {states[location_idx]}"

        # Generate a random user agent
        browsers = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]
        os_systems = ["Windows", "MacOS", "Linux", "iOS", "Android"]
        browser = random.choice(browsers)
        os_system = random.choice(os_systems)
        version = f"{random.randint(1, 20)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        user_agent = f"{browser}/{version} ({os_system})"

        return {
            "ip_address": ip_address,
            "device": device,
            "location": location,
            "user_agent": user_agent,
            "timestamp": f"{self.date} {self.time}",
        }

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
    def date(self) -> str:
        """Get the transaction date."""
        value = self._field_generators["date"].get()
        assert value is not None, "date should not be None"
        return value

    @property
    def time(self) -> str:
        """Get the transaction time."""
        value = self._field_generators["time"].get()
        assert value is not None, "time should not be None"
        return value

    @property
    def amount(self) -> float:
        """Get the transaction amount."""
        value = self._field_generators["amount"].get()
        assert value is not None, "amount should not be None"
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
    def source(self) -> str:
        """Get the transaction source."""
        value = self._field_generators["source"].get()
        assert value is not None, "source should not be None"
        return value

    @property
    def destination(self) -> str:
        """Get the transaction destination."""
        value = self._field_generators["destination"].get()
        assert value is not None, "destination should not be None"
        return value

    @property
    def description(self) -> str:
        """Get the transaction description."""
        value = self._field_generators["description"].get()
        assert value is not None, "description should not be None"
        return value

    @property
    def metadata(self) -> dict:
        """Get the transaction metadata."""
        value = self._field_generators["metadata"].get()
        assert value is not None, "metadata should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the transaction entity to a dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "date": self.date,
            "time": self.time,
            "type": self.type,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "source": self.source,
            "destination": self.destination,
            "description": self.description,
            "metadata": self.metadata,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of transaction entities.

        Args:
            count: Number of transactions to generate

        Returns:
            List of transaction dictionaries
        """
        field_names = [
            "transaction_id",
            "date",
            "time",
            "type",
            "amount",
            "currency",
            "status",
            "source",
            "destination",
            "description",
            "metadata",
        ]
        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
