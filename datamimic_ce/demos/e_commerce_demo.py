# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
E-Commerce Demo

This demo showcases the usage of e-commerce related entities:
- ProductEntity: Generate product data
- OrderEntity: Generate order data
- InvoiceEntity: Generate invoice data
- PaymentEntity: Generate payment data
- TransactionEntity: Generate transaction data

These entities can be used to generate realistic e-commerce data for testing,
development, and demonstration purposes.
"""

import datetime
import json

from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


def demo_product_entity():
    """Demonstrate the ProductEntity."""
    print("\n=== Product Entity Demo ===")

    # Create a product entity
    product_entity = ClassFactoryCEUtil.get_product_entity(min_price=5.99, max_price=499.99)

    # Generate a single product
    print("\nSingle Product:")
    product = product_entity.to_dict()
    print(json.dumps(product, indent=2, default=str))

    # Generate a batch of products
    print("\nBatch of Products (first 2 shown):")
    products = product_entity.generate_batch(count=10)
    for i, product in enumerate(products[:2]):
        print(f"\nProduct {i + 1}:")
        print(json.dumps(product, indent=2, default=str))

    print(f"\nTotal products generated: {len(products)}")


def demo_order_entity():
    """Demonstrate the OrderEntity."""
    print("\n=== Order Entity Demo ===")

    # Create an order entity
    start_date = datetime.datetime.now() - datetime.timedelta(days=90)
    end_date = datetime.datetime.now()

    order_entity = ClassFactoryCEUtil.get_order_entity(
        min_products=1,
        max_products=5,
        min_product_price=9.99,
        max_product_price=299.99,
        start_date=start_date,
        end_date=end_date,
    )

    # Generate a single order
    print("\nSingle Order:")
    order = order_entity.to_dict()
    print(json.dumps(order, indent=2, default=str))

    # Generate a batch of orders
    print("\nBatch of Orders (first 2 shown):")
    orders = order_entity.generate_batch(count=10)
    for i, order in enumerate(orders[:2]):
        print(f"\nOrder {i + 1}:")
        print(json.dumps(order, indent=2, default=str))

    print(f"\nTotal orders generated: {len(orders)}")


def demo_invoice_entity():
    """Demonstrate the InvoiceEntity."""
    print("\n=== Invoice Entity Demo ===")

    # Create an invoice entity
    start_date = datetime.datetime.now() - datetime.timedelta(days=90)
    end_date = datetime.datetime.now()

    invoice_entity = ClassFactoryCEUtil.get_invoice_entity(
        min_amount=50.00, max_amount=2000.00, start_date=start_date, end_date=end_date
    )

    # Generate a single invoice
    print("\nSingle Invoice:")
    invoice = invoice_entity.to_dict()
    print(json.dumps(invoice, indent=2, default=str))

    # Generate a batch of invoices
    print("\nBatch of Invoices (first 2 shown):")
    invoices = invoice_entity.generate_batch(count=10)
    for i, invoice in enumerate(invoices[:2]):
        print(f"\nInvoice {i + 1}:")
        print(json.dumps(invoice, indent=2, default=str))

    print(f"\nTotal invoices generated: {len(invoices)}")


def demo_payment_entity():
    """Demonstrate the PaymentEntity."""
    print("\n=== Payment Entity Demo ===")

    # Create a payment entity
    start_date = datetime.datetime.now() - datetime.timedelta(days=90)
    end_date = datetime.datetime.now()

    payment_entity = ClassFactoryCEUtil.get_payment_entity(
        min_amount=10.00, max_amount=1500.00, start_date=start_date, end_date=end_date
    )

    # Generate a single payment
    print("\nSingle Payment:")
    payment = payment_entity.to_dict()
    print(json.dumps(payment, indent=2, default=str))

    # Generate a batch of payments
    print("\nBatch of Payments (first 2 shown):")
    payments = payment_entity.generate_batch(count=10)
    for i, payment in enumerate(payments[:2]):
        print(f"\nPayment {i + 1}:")
        print(json.dumps(payment, indent=2, default=str))

    print(f"\nTotal payments generated: {len(payments)}")


def demo_transaction_entity():
    """Demonstrate the TransactionEntity."""
    print("\n=== Transaction Entity Demo ===")

    # Create a transaction entity
    start_date = datetime.datetime.now() - datetime.timedelta(days=90)
    end_date = datetime.datetime.now()

    transaction_entity = ClassFactoryCEUtil.get_transaction_entity(
        min_amount=1.00, max_amount=1000.00, start_date=start_date, end_date=end_date
    )

    # Generate a single transaction
    print("\nSingle Transaction:")
    transaction = transaction_entity.to_dict()
    print(json.dumps(transaction, indent=2, default=str))

    # Generate a batch of transactions
    print("\nBatch of Transactions (first 2 shown):")
    transactions = transaction_entity.generate_batch(count=10)
    for i, transaction in enumerate(transactions[:2]):
        print(f"\nTransaction {i + 1}:")
        print(json.dumps(transaction, indent=2, default=str))

    print(f"\nTotal transactions generated: {len(transactions)}")


def demo_e_commerce_system():
    """Demonstrate a complete e-commerce system with related entities."""
    print("\n=== Complete E-Commerce System Demo ===")

    # Create all entities
    product_entity = ClassFactoryCEUtil.get_product_entity()
    order_entity = ClassFactoryCEUtil.get_order_entity()
    invoice_entity = ClassFactoryCEUtil.get_invoice_entity()
    payment_entity = ClassFactoryCEUtil.get_payment_entity()
    transaction_entity = ClassFactoryCEUtil.get_transaction_entity()

    # Generate sample data
    products = product_entity.generate_batch(count=5)
    orders = order_entity.generate_batch(count=3)
    invoices = invoice_entity.generate_batch(count=3)
    payments = payment_entity.generate_batch(count=3)
    transactions = transaction_entity.generate_batch(count=3)

    # Create a complete e-commerce system
    # Store as a dictionary (commented out to avoid unused variable warning)
    # e_commerce_system = {
    #     "products": products,
    #     "orders": orders,
    #     "users": users,
    #     "transactions": transactions,
    #     "reviews": reviews,
    # }

    # Return the individual components instead
    return products, orders, invoices, payments, transactions


def run_demo():
    """Run the e-commerce demo."""
    print("=== E-Commerce Entities Demo ===")
    print("This demo showcases the usage of e-commerce related entities.")

    # Demonstrate individual entities
    demo_product_entity()
    demo_order_entity()
    demo_invoice_entity()
    demo_payment_entity()
    demo_transaction_entity()

    # Demonstrate complete e-commerce system
    demo_e_commerce_system()


if __name__ == "__main__":
    run_demo()
