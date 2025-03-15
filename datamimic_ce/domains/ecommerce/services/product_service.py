# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from typing import Optional

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.domains.ecommerce.models.product import Product


class ProductService(BaseDomainService[Product]):
    """Service for managing product data.

    This class provides methods for generating and operating on product data,
    including creating products, filtering products, and formatting outputs.
    """

    def __init__(self, dataset: Optional[str] = None):
        super().__init__(ProductGenerator(dataset), Product)
