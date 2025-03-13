# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Example script demonstrating order generation.

This script shows how to use the E-commerce domain models to generate order data.
"""

import datetime
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parents[3]))

from datamimic_ce.domains.ecommerce.models.order import Order
from datamimic_ce.utils.domain_class_util import DomainClassUtil


def main():
    """Generate sample order data and print it to the console."""
    domain_class_util = DomainClassUtil()
    
    # Create an order for the US dataset
    print("Generating an order for the US dataset:")
    order_us = Order(
        domain_class_util=domain_class_util,
        dataset="US",
        min_products=2,
        max_products=5,
    )
    order_data_us = order_us.to_dict()

    # Print order details
    print(f"Order ID: {order_data_us['order_id']}")
    print(f"Date: {order_data_us['date']}")
    print(f"Status: {order_data_us['status']}")
    print(f"Payment Method: {order_data_us['payment_method']}")
    print(f"Shipping Method: {order_data_us['shipping_method']}")
    print(f"Currency: {order_data_us['currency']}")
    print(f"Products: {len(order_data_us['product_list'])}")

    # Print the products in the order
    print("\nProducts in the order:")
    for i, product in enumerate(order_data_us["product_list"], 1):
        print(f"{i}. {product['name']} - {product['quantity']} x ${product['price']} = ${product['subtotal']}")

    # Print the order totals
    print("\nOrder Totals:")
    print(f"Subtotal: ${sum(p['subtotal'] for p in order_data_us['product_list']):.2f}")
    print(f"Tax: ${order_data_us['tax_amount']:.2f}")
    print(f"Shipping: ${order_data_us['shipping_amount']:.2f}")
    print(f"Discount: ${order_data_us['discount_amount']:.2f}")
    print(f"Total: ${order_data_us['total_amount']:.2f}")

    if order_data_us["coupon_code"]:
        print(f"Coupon Code: {order_data_us['coupon_code']}")

    if order_data_us["notes"]:
        print(f"Notes: {order_data_us['notes']}")

    # Create an order with a specific date range
    print("\n\nGenerating an order with a specific date range:")
    start_date = datetime.datetime(2022, 1, 1)
    end_date = datetime.datetime(2022, 12, 31)

    order_dated = Order(
        domain_class_util=domain_class_util,
        dataset="US",
        min_products=1,
        max_products=3,
        start_date=start_date,
        end_date=end_date,
    )
    order_data_dated = order_dated.to_dict()

    print(f"Order ID: {order_data_dated['order_id']}")
    print(f"Date: {order_data_dated['date']} (should be in 2022)")

    # Generate multiple orders
    print("\n\nGenerating multiple orders:")
    num_orders = 3
    orders = []

    for _ in range(num_orders):
        order = Order(domain_class_util=domain_class_util, dataset="US")
        orders.append(order.to_dict())
        order.reset()

    print(f"Generated {len(orders)} orders")

    # Print order IDs and dates
    for i, order_data in enumerate(orders, 1):
        print(
            f"{i}. Order {order_data['order_id']} - {order_data['date']} - {order_data['status']} - ${order_data['total_amount']:.2f}"
        )


if __name__ == "__main__":
    main()
