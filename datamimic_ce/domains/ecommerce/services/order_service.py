# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.order import Order


class OrderService(BaseDomainService[Order]):
    """Service for managing order data.

    This class provides methods for generating and operating on order data,
    including creating orders, filtering orders, and formatting outputs.
    """

    def __init__(self, dataset: str | None = None):
        #  Prefer generator to own normalization. Pass through when provided,
        # fallback to "US" for backward compatibility with generator signature.
        super().__init__(OrderGenerator(dataset or "US"), Order)

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
