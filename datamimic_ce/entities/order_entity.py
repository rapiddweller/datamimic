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


class OrderEntity(Entity):
    """Generate order data.

    This class generates realistic order data including order IDs,
    user IDs, product lists, total amounts, dates, and statuses.
    """

    # Order statuses
    ORDER_STATUSES = [
        "PENDING",
        "PROCESSING",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED",
        "RETURNED",
        "REFUNDED",
        "ON_HOLD",
        "BACKORDERED",
        "COMPLETED",
    ]

    # Payment methods
    PAYMENT_METHODS = [
        "CREDIT_CARD",
        "DEBIT_CARD",
        "PAYPAL",
        "BANK_TRANSFER",
        "CASH_ON_DELIVERY",
        "GIFT_CARD",
        "STORE_CREDIT",
        "CRYPTOCURRENCY",
    ]

    # Shipping methods
    SHIPPING_METHODS = [
        "STANDARD",
        "EXPRESS",
        "OVERNIGHT",
        "TWO_DAY",
        "INTERNATIONAL",
        "LOCAL_PICKUP",
        "STORE_PICKUP",
        "FREIGHT",
        "DIGITAL_DELIVERY",
    ]

    # Currency codes
    CURRENCY_CODES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL"]

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        min_products: int = 1,
        max_products: int = 10,
        min_product_price: float = 0.99,
        max_product_price: float = 999.99,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        dataset: str | None = None,
    ):
        """Initialize the OrderEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code for localization
            min_products: Minimum number of products in an order
            max_products: Maximum number of products in an order
            min_product_price: Minimum price of a product
            max_product_price: Maximum price of a product
            start_date: Start date for order dates
            end_date: End date for order dates
            dataset: Optional dataset name
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._min_products = min_products
        self._max_products = max_products
        self._min_product_price = min_product_price
        self._max_product_price = max_product_price

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
                "order_id": self._generate_order_id,
                "user_id": self._generate_user_id,
                "product_list": self._generate_product_list,
                "total_amount": self._generate_total_amount,
                "date": self._generate_date,
                "status": self._generate_status,
                "payment_method": self._generate_payment_method,
                "shipping_method": self._generate_shipping_method,
                "shipping_address": self._generate_shipping_address,
                "billing_address": self._generate_billing_address,
                "currency": self._generate_currency,
                "tax_amount": self._generate_tax_amount,
                "shipping_amount": self._generate_shipping_amount,
                "discount_amount": self._generate_discount_amount,
                "coupon_code": self._generate_coupon_code,
                "notes": self._generate_notes,
            }
        )

    def _generate_order_id(self) -> str:
        """Generate a unique order ID."""
        return f"ORD-{uuid.uuid4().hex[:10].upper()}"

    def _generate_user_id(self) -> str:
        """Generate a random user ID."""
        return f"USER-{uuid.uuid4().hex[:8].upper()}"

    def _generate_product_list(self) -> list[dict[str, Any]]:
        """Generate a list of products in the order."""
        num_products = random.randint(self._min_products, self._max_products)
        products = []

        for _ in range(num_products):
            product_id = f"PROD-{uuid.uuid4().hex[:8].upper()}"
            price = round(random.uniform(self._min_product_price, self._max_product_price), 2)
            quantity = random.randint(1, 5)

            product = {
                "product_id": product_id,
                "name": f"Product {product_id[-4:]}",
                "price": price,
                "quantity": quantity,
                "subtotal": round(price * quantity, 2),
            }

            products.append(product)

        return products

    def _generate_total_amount(self) -> float:
        """Calculate the total amount of the order."""
        product_list = self.product_list
        subtotal = sum(product["subtotal"] for product in product_list)
        tax = self.tax_amount
        shipping = self.shipping_amount
        discount = self.discount_amount

        return round(subtotal + tax + shipping - discount, 2)

    def _generate_date(self) -> datetime.datetime:
        """Generate a random date within the specified range."""
        time_diff = self._end_date - self._start_date
        random_seconds = random.randint(0, int(time_diff.total_seconds()))
        return self._start_date + datetime.timedelta(seconds=random_seconds)

    def _generate_status(self) -> str:
        """Generate a random order status."""
        # Weight the statuses to make COMPLETED and DELIVERED more common
        weights = [0.1, 0.15, 0.15, 0.3, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
        return random.choices(self.ORDER_STATUSES, weights=weights, k=1)[0]

    def _generate_payment_method(self) -> str:
        """Generate a random payment method."""
        # Weight the payment methods to make CREDIT_CARD and DEBIT_CARD more common
        weights = [0.4, 0.3, 0.15, 0.05, 0.03, 0.03, 0.02, 0.02]
        return random.choices(self.PAYMENT_METHODS, weights=weights, k=1)[0]

    def _generate_shipping_method(self) -> str:
        """Generate a random shipping method."""
        # Weight the shipping methods to make STANDARD and EXPRESS more common
        weights = [0.5, 0.2, 0.05, 0.1, 0.05, 0.03, 0.03, 0.02, 0.02]
        return random.choices(self.SHIPPING_METHODS, weights=weights, k=1)[0]

    def _generate_shipping_address(self) -> dict[str, str]:
        """Generate a random shipping address."""
        # In a real implementation, this could use AddressEntity
        return {
            "street": f"{random.randint(1, 9999)} Main St",
            "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
            "postal_code": f"{random.randint(10000, 99999)}",
            "country": "US",
        }

    def _generate_billing_address(self) -> dict[str, str]:
        """Generate a random billing address."""
        # 80% chance billing address is same as shipping
        if random.random() < 0.8:
            return self.shipping_address

        # Otherwise generate a different address
        return {
            "street": f"{random.randint(1, 9999)} Oak St",
            "city": random.choice(["Boston", "Seattle", "Miami", "Denver", "Atlanta"]),
            "state": random.choice(["MA", "WA", "FL", "CO", "GA"]),
            "postal_code": f"{random.randint(10000, 99999)}",
            "country": "US",
        }

    def _generate_currency(self) -> str:
        """Generate a random currency code."""
        return random.choice(self.CURRENCY_CODES)

    def _generate_tax_amount(self) -> float:
        """Generate a tax amount based on the product list."""
        product_list = self.product_list
        subtotal = sum(product["subtotal"] for product in product_list)
        tax_rate = random.uniform(0.05, 0.12)  # 5% to 12% tax rate

        return round(subtotal * tax_rate, 2)

    def _generate_shipping_amount(self) -> float:
        """Generate a shipping amount based on the shipping method."""
        shipping_method = self.shipping_method

        # Base shipping costs by method
        shipping_costs = {
            "STANDARD": (5.0, 10.0),
            "EXPRESS": (15.0, 25.0),
            "OVERNIGHT": (25.0, 50.0),
            "TWO_DAY": (12.0, 20.0),
            "INTERNATIONAL": (30.0, 100.0),
            "LOCAL_PICKUP": (0.0, 0.0),
            "STORE_PICKUP": (0.0, 0.0),
            "FREIGHT": (50.0, 200.0),
            "DIGITAL_DELIVERY": (0.0, 0.0),
        }

        min_cost, max_cost = shipping_costs.get(shipping_method, (5.0, 15.0))
        return round(random.uniform(min_cost, max_cost), 2)

    def _generate_discount_amount(self) -> float:
        """Generate a discount amount."""
        # 30% chance of having a discount
        if random.random() < 0.3:
            product_list = self.product_list
            subtotal = sum(product["subtotal"] for product in product_list)
            discount_rate = random.uniform(0.05, 0.25)  # 5% to 25% discount
            return round(subtotal * discount_rate, 2)

        return 0.0

    def _generate_coupon_code(self) -> str | None:
        """Generate a coupon code if there's a discount."""
        if self.discount_amount > 0:
            coupon_prefixes = ["SAVE", "DISCOUNT", "SPECIAL", "PROMO", "DEAL"]
            prefix = random.choice(coupon_prefixes)
            code = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
            return f"{prefix}{code}"

        return None

    def _generate_notes(self) -> str | None:
        """Generate order notes."""
        # 20% chance of having notes
        if random.random() < 0.2:
            notes = [
                "Please leave at the front door",
                "Call before delivery",
                "Gift - please don't include receipt",
                "Fragile items - handle with care",
                "Please deliver after 5pm",
                "Ring doorbell upon delivery",
                "Contact customer before shipping",
                "Include gift message",
                "Expedite if possible",
                "Address has a gate code: 1234",
            ]
            return random.choice(notes)

        return None

    def reset(self) -> None:
        """Reset all field generators."""
        for generator in self._field_generators.values():
            generator.reset()

    @property
    def order_id(self) -> str:
        """Get the order ID."""
        value = self._field_generators["order_id"].get()
        assert value is not None, "order_id should not be None"
        return value

    @property
    def user_id(self) -> str:
        """Get the user ID."""
        value = self._field_generators["user_id"].get()
        assert value is not None, "user_id should not be None"
        return value

    @property
    def product_list(self) -> list[dict[str, Any]]:
        """Get the product list."""
        value = self._field_generators["product_list"].get()
        assert value is not None, "product_list should not be None"
        return value

    @property
    def total_amount(self) -> float:
        """Get the total amount."""
        value = self._field_generators["total_amount"].get()
        assert value is not None, "total_amount should not be None"
        return value

    @property
    def date(self) -> datetime.datetime:
        """Get the order date."""
        value = self._field_generators["date"].get()
        assert value is not None, "date should not be None"
        return value

    @property
    def status(self) -> str:
        """Get the order status."""
        value = self._field_generators["status"].get()
        assert value is not None, "status should not be None"
        return value

    @property
    def payment_method(self) -> str:
        """Get the payment method."""
        value = self._field_generators["payment_method"].get()
        assert value is not None, "payment_method should not be None"
        return value

    @property
    def shipping_method(self) -> str:
        """Get the shipping method."""
        value = self._field_generators["shipping_method"].get()
        assert value is not None, "shipping_method should not be None"
        return value

    @property
    def shipping_address(self) -> dict[str, str]:
        """Get the shipping address."""
        value = self._field_generators["shipping_address"].get()
        assert value is not None, "shipping_address should not be None"
        return value

    @property
    def billing_address(self) -> dict[str, str]:
        """Get the billing address."""
        value = self._field_generators["billing_address"].get()
        assert value is not None, "billing_address should not be None"
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
    def shipping_amount(self) -> float:
        """Get the shipping amount."""
        value = self._field_generators["shipping_amount"].get()
        assert value is not None, "shipping_amount should not be None"
        return value

    @property
    def discount_amount(self) -> float:
        """Get the discount amount."""
        value = self._field_generators["discount_amount"].get()
        assert value is not None, "discount_amount should not be None"
        return value

    @property
    def coupon_code(self) -> str | None:
        """Get the coupon code."""
        return self._field_generators["coupon_code"].get()

    @property
    def notes(self) -> str | None:
        """Get the order notes."""
        return self._field_generators["notes"].get()

    def to_dict(self) -> dict[str, Any]:
        """Convert the order entity to a dictionary."""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "product_list": self.product_list,
            "total_amount": self.total_amount,
            "date": self.date,
            "status": self.status,
            "payment_method": self.payment_method,
            "shipping_method": self.shipping_method,
            "shipping_address": self.shipping_address,
            "billing_address": self.billing_address,
            "currency": self.currency,
            "tax_amount": self.tax_amount,
            "shipping_amount": self.shipping_amount,
            "discount_amount": self.discount_amount,
            "coupon_code": self.coupon_code,
            "notes": self.notes,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of order entities.

        Args:
            count: Number of orders to generate

        Returns:
            List of order dictionaries
        """
        field_names = list(self._field_generators.keys())
        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
