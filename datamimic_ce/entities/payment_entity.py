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


class PaymentEntity(Entity):
    """Generate payment data.

    This class generates realistic payment data including payment IDs,
    payment methods, statuses, amounts, and timestamps.
    """

    # Payment methods
    PAYMENT_METHODS = [
        "CREDIT_CARD",
        "DEBIT_CARD",
        "BANK_TRANSFER",
        "PAYPAL",
        "APPLE_PAY",
        "GOOGLE_PAY",
        "CRYPTOCURRENCY",
        "CASH",
        "CHECK",
        "GIFT_CARD",
        "STORE_CREDIT",
        "VENMO",
        "ZELLE",
        "WIRE_TRANSFER",
        "MONEY_ORDER",
    ]

    # Payment statuses
    PAYMENT_STATUSES = [
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

    # Payment processors
    PAYMENT_PROCESSORS = [
        "STRIPE",
        "PAYPAL",
        "SQUARE",
        "ADYEN",
        "BRAINTREE",
        "WORLDPAY",
        "AUTHORIZE.NET",
        "CHECKOUT.COM",
        "KLARNA",
        "AFFIRM",
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
        """Initialize the PaymentEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code for localization
            min_amount: Minimum payment amount
            max_amount: Maximum payment amount
            start_date: Start date for payment timestamps
            end_date: End date for payment timestamps
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
                "payment_id": self._generate_payment_id,
                "method": self._generate_method,
                "status": self._generate_status,
                "amount": self._generate_amount,
                "timestamp": self._generate_timestamp,
                "currency": self._generate_currency,
                "processor": self._generate_processor,
                "invoice_id": self._generate_invoice_id,
                "customer_id": self._generate_customer_id,
                "description": self._generate_description,
                "fee": self._generate_fee,
            }
        )

    def _generate_payment_id(self) -> str:
        """Generate a unique payment ID."""
        return f"PAY-{uuid.uuid4().hex[:12].upper()}"

    def _generate_method(self) -> str:
        """Generate a random payment method."""
        return random.choice(self.PAYMENT_METHODS)

    def _generate_status(self) -> str:
        """Generate a random payment status."""
        return random.choice(self.PAYMENT_STATUSES)

    def _generate_amount(self) -> float:
        """Generate a random payment amount."""
        return round(random.uniform(self._min_amount, self._max_amount), 2)

    def _generate_timestamp(self) -> datetime.datetime:
        """Generate a random timestamp within the specified range."""
        time_diff = self._end_date - self._start_date
        random_seconds = random.randint(0, int(time_diff.total_seconds()))
        return self._start_date + datetime.timedelta(seconds=random_seconds)

    def _generate_currency(self) -> str:
        """Generate a random currency code."""
        return random.choice(self.CURRENCY_CODES)

    def _generate_processor(self) -> str:
        """Generate a random payment processor."""
        return random.choice(self.PAYMENT_PROCESSORS)

    def _generate_invoice_id(self) -> str:
        """Generate a random invoice ID."""
        return f"INV-{uuid.uuid4().hex[:8].upper()}"

    def _generate_customer_id(self) -> str:
        """Generate a random customer ID."""
        return f"CUST-{uuid.uuid4().hex[:8].upper()}"

    def _generate_description(self) -> str:
        """Generate a payment description based on the method."""
        payment_method = self.method
        descriptions = {
            "CREDIT_CARD": [
                "Credit card payment",
                "Card payment",
                "Visa payment",
                "Mastercard payment",
                "Amex payment",
            ],
            "DEBIT_CARD": ["Debit card payment", "Direct debit", "Bank card payment"],
            "BANK_TRANSFER": ["Bank transfer", "ACH transfer", "Direct deposit", "Electronic funds transfer"],
            "PAYPAL": ["PayPal payment", "PayPal transfer", "Online payment"],
            "APPLE_PAY": ["Apple Pay payment", "Mobile payment", "Contactless payment"],
            "GOOGLE_PAY": ["Google Pay payment", "Mobile payment", "Contactless payment"],
            "CRYPTOCURRENCY": ["Bitcoin payment", "Ethereum payment", "Crypto payment", "Digital currency payment"],
            "CASH": ["Cash payment", "In-person payment", "Cash transaction"],
            "CHECK": ["Check payment", "Paper check", "Personal check"],
            "GIFT_CARD": ["Gift card payment", "Store credit", "Gift certificate"],
            "STORE_CREDIT": ["Store credit", "Account credit", "Credit balance"],
            "VENMO": ["Venmo payment", "Mobile transfer", "P2P payment"],
            "ZELLE": ["Zelle payment", "Bank-to-bank transfer", "P2P payment"],
            "WIRE_TRANSFER": ["Wire transfer", "Bank wire", "International transfer"],
            "MONEY_ORDER": ["Money order", "Postal money order", "Bank money order"],
        }

        return random.choice(descriptions.get(payment_method, ["Payment"]))

    def _generate_fee(self) -> float:
        """Generate a payment processing fee."""
        # Generate a fee that's a small percentage of the payment amount
        return round(self.amount * random.uniform(0.01, 0.05), 2)

    def reset(self) -> None:
        """Reset all field generators."""
        for generator in self._field_generators.values():
            generator.reset()

    @property
    def payment_id(self) -> str:
        """Get the payment ID."""
        value = self._field_generators["payment_id"].get()
        assert value is not None, "payment_id should not be None"
        return value

    @property
    def method(self) -> str:
        """Get the payment method."""
        value = self._field_generators["method"].get()
        assert value is not None, "method should not be None"
        return value

    @property
    def status(self) -> str:
        """Get the payment status."""
        value = self._field_generators["status"].get()
        assert value is not None, "status should not be None"
        return value

    @property
    def amount(self) -> float:
        """Get the payment amount."""
        value = self._field_generators["amount"].get()
        assert value is not None, "amount should not be None"
        return value

    @property
    def timestamp(self) -> datetime.datetime:
        """Get the payment timestamp."""
        value = self._field_generators["timestamp"].get()
        assert value is not None, "timestamp should not be None"
        return value

    @property
    def currency(self) -> str:
        """Get the payment currency."""
        value = self._field_generators["currency"].get()
        assert value is not None, "currency should not be None"
        return value

    @property
    def processor(self) -> str:
        """Get the payment processor."""
        value = self._field_generators["processor"].get()
        assert value is not None, "processor should not be None"
        return value

    @property
    def invoice_id(self) -> str:
        """Get the invoice ID."""
        value = self._field_generators["invoice_id"].get()
        assert value is not None, "invoice_id should not be None"
        return value

    @property
    def customer_id(self) -> str:
        """Get the customer ID."""
        value = self._field_generators["customer_id"].get()
        assert value is not None, "customer_id should not be None"
        return value

    @property
    def description(self) -> str:
        """Get the payment description."""
        value = self._field_generators["description"].get()
        assert value is not None, "description should not be None"
        return value

    @property
    def fee(self) -> float:
        """Get the payment processing fee."""
        value = self._field_generators["fee"].get()
        assert value is not None, "fee should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the payment entity to a dictionary."""
        return {
            "payment_id": self.payment_id,
            "method": self.method,
            "status": self.status,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "currency": self.currency,
            "processor": self.processor,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "description": self.description,
            "fee": self.fee,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of payment entities.

        Args:
            count: Number of payments to generate

        Returns:
            List of payment dictionaries
        """
        field_names = list(self._field_generators.keys())
        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
