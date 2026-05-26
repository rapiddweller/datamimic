# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datetime import datetime
from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import (
    EntitySchema,
    FieldSpec,
    address_group,
    field,
)
from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.order import Order

ORDER_SCHEMA = EntitySchema(
    "Order",
    (
        field("order_id", str, "Unique order identifier."),
        field("user_id", str, "Identifier of the ordering user."),
        field("product_list", list, "List of ordered products."),
        field("total_amount", float, "Order total amount."),
        field("date", datetime, "Order date and time."),
        field("status", str, "Order status."),
        field("payment_method", str, "Payment method."),
        field("shipping_method", str, "Shipping method."),
        address_group("shipping_address", "Structured shipping address."),
        address_group("billing_address", "Structured billing address."),
        field("currency", str, "Order currency code."),
        field("tax_amount", float, "Tax amount."),
        field("shipping_amount", float, "Shipping cost."),
        field("discount_amount", float, "Discount amount."),
        field("coupon_code", str, "Applied coupon code, if any.", optional=True),
        field("notes", str, "Order notes, if any.", optional=True),
    ),
)


class OrderService(BaseDomainService[Order]):
    """Service for managing order data.

    This class provides methods for generating and operating on order data,
    including creating orders, filtering orders, and formatting outputs.
    """

    DATASET_PATTERNS = (
        "ecommerce/order_statuses_{CC}.csv",
        "ecommerce/payment_methods_{CC}.csv",
        "ecommerce/shipping_methods_{CC}.csv",
        "ecommerce/currencies_{CC}.csv",
        # Additional order assets used by generator helpers
        "ecommerce/order/coupon_prefixes_{CC}.csv",
        "ecommerce/order/notes_{CC}.csv",
    )

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
        reference_now: datetime | None = None,
    ):
        super().__init__(
            OrderGenerator(dataset=dataset, rng=rng, reference_now=reference_now),
            Order,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return ORDER_SCHEMA.fields
