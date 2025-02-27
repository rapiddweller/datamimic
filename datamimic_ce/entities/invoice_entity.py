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


class InvoiceEntity(Entity):
    """Generate invoice data.

    This class generates realistic invoice data including invoice IDs,
    order IDs, dates, amounts, and statuses.
    """

    # Invoice statuses
    INVOICE_STATUSES = [
        "DRAFT",
        "SENT",
        "VIEWED",
        "PAID",
        "PARTIALLY_PAID",
        "OVERDUE",
        "CANCELLED",
        "REFUNDED",
        "DISPUTED",
        "VOIDED",
    ]

    # Payment terms
    PAYMENT_TERMS = ["NET_7", "NET_15", "NET_30", "NET_45", "NET_60", "DUE_ON_RECEIPT", "END_OF_MONTH", "CUSTOM"]

    # Currency codes
    CURRENCY_CODES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL"]

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        min_amount: float = 10.00,
        max_amount: float = 10000.00,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        dataset: str | None = None,
    ):
        """Initialize the InvoiceEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code for localization
            min_amount: Minimum invoice amount
            max_amount: Maximum invoice amount
            start_date: Start date for invoice dates
            end_date: End date for invoice dates
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
                "invoice_id": self._generate_invoice_id,
                "order_id": self._generate_order_id,
                "customer_id": self._generate_customer_id,
                "date": self._generate_date,
                "due_date": self._generate_due_date,
                "amount": self._generate_amount,
                "status": self._generate_status,
                "payment_terms": self._generate_payment_terms,
                "currency": self._generate_currency,
                "tax_amount": self._generate_tax_amount,
                "discount_amount": self._generate_discount_amount,
                "shipping_amount": self._generate_shipping_amount,
                "subtotal": self._generate_subtotal,
                "total": self._generate_total,
                "notes": self._generate_notes,
                "payment_method": self._generate_payment_method,
                "billing_address": self._generate_billing_address,
            }
        )

    def _generate_invoice_id(self) -> str:
        """Generate a unique invoice ID."""
        return f"INV-{uuid.uuid4().hex[:8].upper()}"

    def _generate_order_id(self) -> str:
        """Generate a random order ID."""
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"

    def _generate_customer_id(self) -> str:
        """Generate a random customer ID."""
        return f"CUST-{uuid.uuid4().hex[:8].upper()}"

    def _generate_date(self) -> datetime.datetime:
        """Generate a random date within the specified range."""
        time_diff = self._end_date - self._start_date
        random_seconds = random.randint(0, int(time_diff.total_seconds()))
        return self._start_date + datetime.timedelta(seconds=random_seconds)

    def _generate_due_date(self) -> datetime.datetime:
        """Generate a due date based on the invoice date and payment terms."""
        invoice_date = self.date
        payment_terms = self.payment_terms

        # Calculate due date based on payment terms
        if payment_terms == "NET_7":
            return invoice_date + datetime.timedelta(days=7)
        elif payment_terms == "NET_15":
            return invoice_date + datetime.timedelta(days=15)
        elif payment_terms == "NET_30":
            return invoice_date + datetime.timedelta(days=30)
        elif payment_terms == "NET_45":
            return invoice_date + datetime.timedelta(days=45)
        elif payment_terms == "NET_60":
            return invoice_date + datetime.timedelta(days=60)
        elif payment_terms == "DUE_ON_RECEIPT":
            return invoice_date
        elif payment_terms == "END_OF_MONTH":
            # End of the month in which the invoice was issued
            next_month = invoice_date.replace(day=28) + datetime.timedelta(days=4)
            return next_month.replace(day=1) - datetime.timedelta(days=1)
        else:  # CUSTOM
            # Random number of days between 1 and 90
            return invoice_date + datetime.timedelta(days=random.randint(1, 90))

    def _generate_amount(self) -> float:
        """Generate a random invoice amount."""
        return round(random.uniform(self._min_amount, self._max_amount), 2)

    def _generate_status(self) -> str:
        """Generate a random invoice status."""
        # Weight the statuses to make PAID and SENT more common
        weights = [0.05, 0.2, 0.1, 0.4, 0.05, 0.1, 0.03, 0.03, 0.02, 0.02]
        return random.choices(self.INVOICE_STATUSES, weights=weights, k=1)[0]

    def _generate_payment_terms(self) -> str:
        """Generate random payment terms."""
        # Weight the payment terms to make NET_30 more common
        weights = [0.1, 0.15, 0.4, 0.1, 0.05, 0.1, 0.05, 0.05]
        return random.choices(self.PAYMENT_TERMS, weights=weights, k=1)[0]

    def _generate_currency(self) -> str:
        """Generate a random currency code."""
        return random.choice(self.CURRENCY_CODES)

    def _generate_tax_amount(self) -> float:
        """Generate a tax amount based on the subtotal."""
        subtotal = self.subtotal
        tax_rate = random.uniform(0.05, 0.12)  # 5% to 12% tax rate

        return round(subtotal * tax_rate, 2)

    def _generate_discount_amount(self) -> float:
        """Generate a discount amount."""
        # 30% chance of having a discount
        if random.random() < 0.3:
            subtotal = self.subtotal
            discount_rate = random.uniform(0.05, 0.2)  # 5% to 20% discount
            return round(subtotal * discount_rate, 2)

        return 0.0

    def _generate_shipping_amount(self) -> float:
        """Generate a shipping amount."""
        # 70% chance of having shipping charges
        if random.random() < 0.7:
            return round(random.uniform(5.0, 50.0), 2)

        return 0.0

    def _generate_subtotal(self) -> float:
        """Generate a subtotal amount."""
        # Subtotal is the base amount before tax, shipping, and discounts
        return round(self.amount * 0.85, 2)  # Approximately 85% of total

    def _generate_total(self) -> float:
        """Calculate the total invoice amount."""
        subtotal = self.subtotal
        tax = self.tax_amount
        shipping = self.shipping_amount
        discount = self.discount_amount

        return round(subtotal + tax + shipping - discount, 2)

    def _generate_notes(self) -> str | None:
        """Generate invoice notes."""
        # 25% chance of having notes
        if random.random() < 0.25:
            notes = [
                "Please pay by the due date",
                "Thank you for your business",
                "Late payment subject to 1.5% monthly interest",
                "Contact accounting for questions",
                "Payment plans available upon request",
                "Please include invoice number with payment",
                "This is a corrected invoice",
                "Tax exempt - certificate on file",
                "Discount applied for early payment",
                "Final invoice for services rendered",
            ]
            return random.choice(notes)

        return None

    def _generate_payment_method(self) -> str | None:
        """Generate a payment method if the invoice is paid."""
        if self.status in ["PAID", "PARTIALLY_PAID", "REFUNDED"]:
            payment_methods = [
                "Credit Card",
                "Bank Transfer",
                "Check",
                "PayPal",
                "Cash",
                "Wire Transfer",
                "Direct Debit",
                "Cryptocurrency",
            ]
            return random.choice(payment_methods)

        return None

    def _generate_billing_address(self) -> dict[str, str]:
        """Generate a random billing address."""
        return {
            "street": f"{random.randint(1, 9999)} Main St",
            "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
            "postal_code": f"{random.randint(10000, 99999)}",
            "country": "US",
        }

    def reset(self) -> None:
        """Reset all field generators."""
        for generator in self._field_generators.values():
            generator.reset()

    @property
    def invoice_id(self) -> str:
        """Get the invoice ID."""
        value = self._field_generators["invoice_id"].get()
        assert value is not None, "invoice_id should not be None"
        return value

    @property
    def order_id(self) -> str:
        """Get the order ID."""
        value = self._field_generators["order_id"].get()
        assert value is not None, "order_id should not be None"
        return value

    @property
    def customer_id(self) -> str:
        """Get the customer ID."""
        value = self._field_generators["customer_id"].get()
        assert value is not None, "customer_id should not be None"
        return value

    @property
    def date(self) -> datetime.datetime:
        """Get the invoice date."""
        value = self._field_generators["date"].get()
        assert value is not None, "date should not be None"
        return value

    @property
    def due_date(self) -> datetime.datetime:
        """Get the due date."""
        value = self._field_generators["due_date"].get()
        assert value is not None, "due_date should not be None"
        return value

    @property
    def amount(self) -> float:
        """Get the invoice amount."""
        value = self._field_generators["amount"].get()
        assert value is not None, "amount should not be None"
        return value

    @property
    def status(self) -> str:
        """Get the invoice status."""
        value = self._field_generators["status"].get()
        assert value is not None, "status should not be None"
        return value

    @property
    def payment_terms(self) -> str:
        """Get the payment terms."""
        value = self._field_generators["payment_terms"].get()
        assert value is not None, "payment_terms should not be None"
        return value

    @property
    def currency(self) -> str:
        """Get the currency code."""
        value = self._field_generators["currency"].get()
        assert value is not None, "currency should not be None"
        return value

    @property
    def tax_amount(self) -> float:
        """Get the tax amount."""
        value = self._field_generators["tax_amount"].get()
        assert value is not None, "tax_amount should not be None"
        return value

    @property
    def discount_amount(self) -> float:
        """Get the discount amount."""
        value = self._field_generators["discount_amount"].get()
        assert value is not None, "discount_amount should not be None"
        return value

    @property
    def shipping_amount(self) -> float:
        """Get the shipping amount."""
        value = self._field_generators["shipping_amount"].get()
        assert value is not None, "shipping_amount should not be None"
        return value

    @property
    def subtotal(self) -> float:
        """Get the subtotal amount."""
        value = self._field_generators["subtotal"].get()
        assert value is not None, "subtotal should not be None"
        return value

    @property
    def total(self) -> float:
        """Get the total amount."""
        value = self._field_generators["total"].get()
        assert value is not None, "total should not be None"
        return value

    @property
    def notes(self) -> str | None:
        """Get the invoice notes."""
        return self._field_generators["notes"].get()

    @property
    def payment_method(self) -> str | None:
        """Get the payment method."""
        return self._field_generators["payment_method"].get()

    @property
    def billing_address(self) -> dict[str, str]:
        """Get the billing address."""
        value = self._field_generators["billing_address"].get()
        assert value is not None, "billing_address should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the invoice entity to a dictionary."""
        return {
            "invoice_id": self.invoice_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "date": self.date,
            "due_date": self.due_date,
            "amount": self.amount,
            "status": self.status,
            "payment_terms": self.payment_terms,
            "currency": self.currency,
            "tax_amount": self.tax_amount,
            "discount_amount": self.discount_amount,
            "shipping_amount": self.shipping_amount,
            "subtotal": self.subtotal,
            "total": self.total,
            "notes": self.notes,
            "payment_method": self.payment_method,
            "billing_address": self.billing_address,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of invoice entities.

        Args:
            count: Number of invoices to generate

        Returns:
            List of invoice dictionaries
        """
        field_names = list(self._field_generators.keys())
        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
