# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
E-commerce services.

This module contains services for e-commerce entities to handle
business logic related to e-commerce operations.
"""

from .order_service import OrderService
from .product_service import ProductService

__all__ = ["ProductService", "OrderService"]
