# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Order model.

This module provides a model for representing an e-commerce order.
"""

import datetime
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple, cast

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import property_cache
from datamimic_ce.domains.ecommerce.data_loaders.order_loader import OrderDataLoader
from datamimic_ce.domains.ecommerce.data_loaders.product_loader import ProductDataLoader
from datamimic_ce.domains.ecommerce.models.product import Product
from datamimic_ce.domains.ecommerce.utils.random_utils import generate_id, weighted_choice


class Order(BaseEntity):
    """Model for representing an e-commerce order.

    This class provides a model for generating realistic order data including
    order IDs, product lists, shipping information, and payment details.
    """

    def __init__(
        self,
        locale: str = "en",
        min_products: int = 1,
        max_products: int = 10,
        min_product_price: float = 0.99,
        max_product_price: float = 999.99,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        dataset: Optional[str] = None,
    ):
        """Initialize the Order model.

        Args:
            locale: Locale code for localization
            min_products: Minimum number of products in an order
            max_products: Maximum number of products in an order
            min_product_price: Minimum price of a product
            max_product_price: Maximum price of a product
            start_date: Start date for order dates (defaults to 1 year ago)
            end_date: End date for order dates (defaults to now)
            dataset: Optional dataset code (country code)
        """
        super().__init__(locale, dataset)
        self._min_products = min_products
        self._max_products = max_products
        self._min_product_price = min_product_price
        self._max_product_price = max_product_price
        self._dataset = dataset
        
        # Set default dates if not provided
        if start_date is None:
            start_date = datetime.datetime.now() - datetime.timedelta(days=365)
        if end_date is None:
            end_date = datetime.datetime.now()
        
        self._start_date = start_date
        self._end_date = end_date
        
        # Initialize product model for generating product data
        self._product_model = Product(
            locale=locale,
            min_price=min_product_price,
            max_price=max_product_price,
            dataset=dataset,
        )
        
        # Initialize cached properties
        self._order_id = None
        self._user_id = None
        self._product_list = None
        self._total_amount = None
        self._date = None
        self._status = None
        self._payment_method = None
        self._shipping_method = None
        self._shipping_address = None
        self._billing_address = None
        self._currency = None
        self._tax_amount = None
        self._shipping_amount = None
        self._discount_amount = None
        self._coupon_code = None
        self._notes = None

    @property
    def order_id(self) -> str:
        """Get the order ID.

        Returns:
            A unique order ID
        """
        if self._order_id is None:
            self._order_id = generate_id("ORD", 8)
        return self._order_id

    @property
    def user_id(self) -> str:
        """Get the user ID.

        Returns:
            A unique user ID
        """
        if self._user_id is None:
            self._user_id = generate_id("USER", 8)
        return self._user_id

    @property_cache
    def product_list(self) -> List[Dict[str, Any]]:
        """Get the list of products in the order.

        Returns:
            A list of products with quantities and prices
        """
        num_products = random.randint(self._min_products, self._max_products)
        products = []
        
        for _ in range(num_products):
            # Generate a product
            product_data = self._product_model.to_dict()
            self._product_model.reset()
            
            # Extract needed fields and add quantity and subtotal
            quantity = random.randint(1, 5)
            price = product_data["price"]
            
            order_product = {
                "product_id": product_data["product_id"],
                "name": product_data["name"],
                "price": price,
                "category": product_data["category"],
                "quantity": quantity,
                "subtotal": round(price * quantity, 2),
            }
            
            products.append(order_product)
        
        return products

    @property
    def date(self) -> datetime.datetime:
        """Get the order date.

        Returns:
            A random date within the specified range
        """
        if self._date is None:
            time_diff = self._end_date - self._start_date
            random_seconds = random.randint(0, int(time_diff.total_seconds()))
            self._date = self._start_date + datetime.timedelta(seconds=random_seconds)
        return self._date

    @property
    def status(self) -> str:
        """Get the order status.

        Returns:
            An order status (e.g., PENDING, DELIVERED)
        """
        if self._status is None:
            statuses = OrderDataLoader.get_order_statuses(self._dataset)
            self._status = weighted_choice(statuses)
        return self._status

    @property
    def payment_method(self) -> str:
        """Get the payment method.

        Returns:
            A payment method (e.g., CREDIT_CARD, PAYPAL)
        """
        if self._payment_method is None:
            methods = OrderDataLoader.get_payment_methods(self._dataset)
            self._payment_method = weighted_choice(methods)
        return self._payment_method

    @property
    def shipping_method(self) -> str:
        """Get the shipping method.

        Returns:
            A shipping method (e.g., STANDARD, EXPRESS)
        """
        if self._shipping_method is None:
            methods = OrderDataLoader.get_shipping_methods(self._dataset)
            self._shipping_method = weighted_choice(methods)
        return self._shipping_method

    @property_cache
    def shipping_address(self) -> Dict[str, str]:
        """Get the shipping address.

        Returns:
            A shipping address dictionary
        """
        # In a real implementation, this would use an Address model
        return {
            "street": f"{random.randint(1, 9999)} Main St",
            "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
            "postal_code": f"{random.randint(10000, 99999)}",
            "country": "US",
        }

    @property_cache
    def billing_address(self) -> Dict[str, str]:
        """Get the billing address.

        Returns:
            A billing address dictionary
        """
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

    @property
    def currency(self) -> str:
        """Get the currency code.

        Returns:
            A currency code (e.g., USD)
        """
        if self._currency is None:
            currencies = ProductDataLoader.get_currencies(self._dataset)
            self._currency = weighted_choice(currencies)
        return self._currency

    @property
    def tax_amount(self) -> float:
        """Get the tax amount.

        Returns:
            The tax amount for the order
        """
        if self._tax_amount is None:
            # Calculate subtotal from product list
            subtotal = sum(product["subtotal"] for product in self.product_list)
            # Apply tax rate (5-12%)
            tax_rate = random.uniform(0.05, 0.12)
            self._tax_amount = round(subtotal * tax_rate, 2)
        return self._tax_amount

    @property
    def shipping_amount(self) -> float:
        """Get the shipping amount.

        Returns:
            The shipping cost for the order
        """
        if self._shipping_amount is None:
            # Get shipping cost range for the selected shipping method
            min_cost, max_cost = OrderDataLoader.get_shipping_cost_range(
                self.shipping_method, self._dataset
            )
            self._shipping_amount = round(random.uniform(min_cost, max_cost), 2)
        return self._shipping_amount

    @property
    def discount_amount(self) -> float:
        """Get the discount amount.

        Returns:
            The discount amount for the order
        """
        if self._discount_amount is None:
            # 30% chance of having a discount
            if random.random() < 0.3:
                # Calculate subtotal from product list
                subtotal = sum(product["subtotal"] for product in self.product_list)
                # Apply discount rate (5-25%)
                discount_rate = random.uniform(0.05, 0.25)
                self._discount_amount = round(subtotal * discount_rate, 2)
            else:
                self._discount_amount = 0.0
        return self._discount_amount

    @property
    def coupon_code(self) -> Optional[str]:
        """Get the coupon code.

        Returns:
            A coupon code if applicable, or None
        """
        if self._coupon_code is None and self.discount_amount > 0:
            # Generate a coupon code if there's a discount
            coupon_prefixes = ["SAVE", "DISCOUNT", "SPECIAL", "PROMO", "DEAL"]
            prefix = random.choice(coupon_prefixes)
            code = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
            self._coupon_code = f"{prefix}{code}"
        return self._coupon_code

    @property
    def notes(self) -> Optional[str]:
        """Get order notes.

        Returns:
            Order notes if applicable, or None
        """
        if self._notes is None:
            # 20% chance of having notes
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
                self._notes = random.choice(notes_options)
        return self._notes

    @property
    def total_amount(self) -> float:
        """Get the total amount.

        Returns:
            The total amount for the order
        """
        if self._total_amount is None:
            # Calculate subtotal from product list
            subtotal = sum(product["subtotal"] for product in self.product_list)
            # Add tax and shipping, subtract discount
            self._total_amount = round(
                subtotal + self.tax_amount + self.shipping_amount - self.discount_amount, 2
            )
        return self._total_amount

    def reset(self) -> None:
        """Reset all cached values."""
        self._order_id = None
        self._user_id = None
        if hasattr(self.product_list, "reset_cache"):
            self.product_list.reset_cache(self)
        self._total_amount = None
        self._date = None
        self._status = None
        self._payment_method = None
        self._shipping_method = None
        if hasattr(self.shipping_address, "reset_cache"):
            self.shipping_address.reset_cache(self)
        if hasattr(self.billing_address, "reset_cache"):
            self.billing_address.reset_cache(self)
        self._currency = None
        self._tax_amount = None
        self._shipping_amount = None
        self._discount_amount = None
        self._coupon_code = None
        self._notes = None

    def to_dict(self) -> Dict[str, Any]:
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