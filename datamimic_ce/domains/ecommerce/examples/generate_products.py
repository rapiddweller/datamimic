# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script demonstrating product generation.

This script shows how to use the E-commerce domain models to generate product data.
"""

import json
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parents[3]))

from datamimic_ce.domains.ecommerce.models.product import Product
from datamimic_ce.domains.ecommerce.services.product_service import ProductService
from datamimic_ce.utils.domain_class_util import DomainClassUtil


def main():
    """Generate sample product data and print it to the console."""
    class_factory_util = DomainClassUtil()
    
    # Method 1: Using the Product model directly with US dataset
    print("Method 1: Using the Product model directly (US dataset)")
    product_us = Product(class_factory_util=class_factory_util, dataset="US")
    product_data_us = product_us.to_dict()
    print(json.dumps(product_data_us, indent=2))
    print()

    # Method 1b: Using the Product model with DE dataset
    print("Method 1b: Using the Product model with DE dataset")
    product_de = Product(class_factory_util=class_factory_util, dataset="DE")
    product_data_de = product_de.to_dict()
    print(json.dumps(product_data_de, indent=2))
    print()

    # Method 2: Using the ProductService
    print("Method 2: Using the ProductService (US dataset)")
    product_service = ProductService(class_factory_util=class_factory_util, dataset="US")

    # Generate a single product
    single_product = product_service.create_product()
    print("Single product:")
    print(json.dumps(single_product, indent=2))
    print()

    # Generate multiple products
    products = product_service.create_products(count=5)
    print(f"Generated {len(products)} products")

    # Filter products by category (if any match)
    electronics_products = product_service.filter_products_by_category(products, "ELECTRONICS")
    print(f"Found {len(electronics_products)} electronics products")

    if electronics_products:
        print("Example electronics product:")
        print(json.dumps(electronics_products[0], indent=2))

    # Get available categories
    categories = product_service.get_product_categories()
    print(f"Available categories: {', '.join(categories[:5])}...")

    # Compare currencies between US and DE
    print("\nComparing currencies between US and DE datasets:")
    us_service = ProductService(class_factory_util=class_factory_util, dataset="US")
    de_service = ProductService(class_factory_util=class_factory_util, dataset="DE")

    us_product = us_service.create_product()
    de_product = de_service.create_product()

    print(f"US product currency: {us_product['currency']}")
    print(f"DE product currency: {de_product['currency']}")


if __name__ == "__main__":
    main()
