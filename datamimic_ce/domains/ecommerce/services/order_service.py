# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime as dt
import random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import (
    ADDRESS_GROUP_SPEC,
    AttributeSpec,
    group,
    specs,
)
from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.order import Order


class OrderService(BaseDomainService[Order]):
    """Service for managing order data.

    This class provides methods for generating and operating on order data,
    including creating orders, filtering orders, and formatting outputs.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        reference_now: dt.datetime | None = None,
    ):
        super().__init__(
            OrderGenerator(dataset, rng=rng, reference_now=reference_now),
            Order,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return (
            *specs(
                ("order_id", "str", "Unique order identifier."),
                ("user_id", "str", "Identifier of the ordering user."),
                ("product_list", "list", "List of ordered products."),
                ("total_amount", "float", "Order total amount."),
                ("date", "datetime", "Order date and time."),
                ("status", "str", "Order status."),
                ("payment_method", "str", "Payment method."),
                ("shipping_method", "str", "Shipping method."),
            ),
            group("shipping_address", "Structured shipping address.", ADDRESS_GROUP_SPEC.children),
            group("billing_address", "Structured billing address.", ADDRESS_GROUP_SPEC.children),
            *specs(
                ("currency", "str", "Order currency code."),
                ("tax_amount", "float", "Tax amount."),
                ("shipping_amount", "float", "Shipping cost."),
                ("discount_amount", "float", "Discount amount."),
                ("coupon_code", "str | None", "Applied coupon code, if any."),
                ("notes", "str | None", "Order notes, if any."),
            ),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "ecommerce/order_statuses_{CC}.csv",
            "ecommerce/payment_methods_{CC}.csv",
            "ecommerce/shipping_methods_{CC}.csv",
            "ecommerce/currencies_{CC}.csv",
            # Additional order assets used by generator helpers
            "ecommerce/order/coupon_prefixes_{CC}.csv",
            "ecommerce/order/notes_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
