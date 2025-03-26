# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.ecommerce.models.order import Order


class OrderService(BaseDomainService[Order]):
    """Service for managing order data.

    This class provides methods for generating and operating on order data,
    including creating orders, filtering orders, and formatting outputs.
    """

    def __init__(self, dataset: str = "US"):
        super().__init__(OrderGenerator(dataset), Order)
