# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Order model.

This module provides a model for representing an e-commerce order.
"""

import datetime
import random
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.product import Product


class Order(BaseEntity):
    """Model for representing an e-commerce order.

    This class provides a model for generating realistic order data including
    order IDs, product lists, shipping information, and payment details.
    """

    def __init__(self, order_generator: OrderGenerator):
        """Initialize the Order model.

        Args:
            order_generator: Order generator
        """
        super().__init__()
        self._order_generator = order_generator

    @property
    @property_cache
    def order_id(self) -> str:
        """Get the order ID.

        Returns:
            A unique order ID
        """
        return "ORD" + "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=8))

    @property
    @property_cache
    def user_id(self) -> str:
        """Get the user ID.

        Returns:
            A unique user ID
        """
        return "USER" + "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=8))

    @property
    @property_cache
    def product_list(self) -> list[Product]:
        """Get the list of products in the order.

        Returns:
            A list of products with quantities and prices
        """
        return [Product(self._order_generator.product_generator) for _ in range(random.randint(1, 10))]

    @product_list.setter
    def product_list(self, value: list[Product]) -> None:
        """Set the product list.

        Args:
            value: The list of products to set.
        """
        self._field_cache["product_list"] = value

    @property
    @property_cache
    def date(self) -> datetime.datetime:
        """Get the order date.

        Returns:
            A random date within the specified range
        """
        return datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))

    @property
    @property_cache
    def status(self) -> str:
        """Get the order status.

        Returns:
            An order status (e.g., PENDING, DELIVERED)
        """
        return self._order_generator.get_order_status()

    @status.setter
    def status(self, value: str) -> None:
        """Set the order status.

        Args:
            value: The order status to set.
        """
        self._field_cache["status"] = value

    @property
    @property_cache
    def payment_method(self) -> str:
        """Get the payment method.

        Returns:
            A payment method (e.g., CREDIT_CARD, PAYPAL)
        """
        return self._order_generator.get_payment_method()

    @property
    @property_cache
    def shipping_method(self) -> str:
        """Get the shipping method.

        Returns:
            A shipping method (e.g., STANDARD, EXPRESS)
        """
        return self._order_generator.get_shipping_method()

    @property
    @property_cache
    def shipping_address(self) -> Address:
        """Get the shipping address.

        Returns:
            A shipping address dictionary
        """
        # In a real implementation, this would use an Address model
        return Address(self._order_generator.address_generator)

    @shipping_address.setter
    def shipping_address(self, value: Address) -> None:
        """Set the shipping address.

        Args:
            value: The shipping address to set.
        """
        self._field_cache["shipping_address"] = value

    @property
    @property_cache
    def billing_address(self) -> Address:
        """Get the billing address.

        Returns:
            A billing address dictionary
        """
        # 80% chance billing address is same as shipping
        # Otherwise generate a different address
        return self.shipping_address if random.random() < 0.8 else Address(self._order_generator.address_generator)

    @property
    @property_cache
    def currency(self) -> str:
        """Get the currency code.

        Returns:
            A currency code (e.g., USD)
        """
        return self._order_generator.get_currency_code()

    @property
    @property_cache
    def tax_amount(self) -> float:
        """Get the tax amount.

        Returns:
            The tax amount for the order
        """
        # Calculate subtotal from product list
        subtotal = sum(product.price for product in self.product_list)
        # Apply tax rate (5-12%)
        tax_rate = random.uniform(0.05, 0.12)
        return round(subtotal * tax_rate, 2)

    @property
    @property_cache
    def shipping_amount(self) -> float:
        """Get the shipping amount.

        Returns:
            The shipping cost for the order
        """
        # Get shipping cost range for the selected shipping method
        return self._order_generator.get_shipping_amount(self.shipping_method)

    @property
    @property_cache
    def discount_amount(self) -> float:
        """Get the discount amount.

        Returns:
            The discount amount for the order
        """
        # 30% chance of having a discount
        if random.random() < 0.3:
            # Calculate subtotal from product list
            subtotal = sum(product.price for product in self.product_list)
            # Apply discount rate (5-25%)
            discount_rate = random.uniform(0.05, 0.25)
            return round(subtotal * discount_rate, 2)
        else:
            return 0.0

    @property
    @property_cache
    def coupon_code(self) -> str | None:
        """Get the coupon code.

        Returns:
            A coupon code if applicable, or None
        """
        if self.discount_amount > 0:
            # Generate a coupon code if there's a discount
            coupon_prefixes = ["SAVE", "DISCOUNT", "SPECIAL", "PROMO", "DEAL"]
            prefix = random.choice(coupon_prefixes)
            code = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
            return f"{prefix}{code}"
        return None

    @property
    @property_cache
    def notes(self) -> str | None:
        """Get order notes.

        Returns:
            Order notes if applicable, or None
        """
        # 20% chance of having notes
        notes = None
        if random.random() < 0.2:
            notes_options = [
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
            notes = random.choice(notes_options)
        return notes

    @property
    @property_cache
    def total_amount(self) -> float:
        """Get the total amount.

        Returns:
            The total amount for the order
        """
        # Calculate subtotal from product list
        subtotal = sum(product.price for product in self.product_list)
        # Add tax and shipping, subtract discount
        return round(subtotal + self.tax_amount + self.shipping_amount - self.discount_amount, 2)

    def to_dict(self) -> dict[str, Any]:
        """Convert the order to a dictionary.

        Returns:
            A dictionary representation of the order
        """
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
