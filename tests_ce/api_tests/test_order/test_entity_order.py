# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import datetime

import pytest

from datamimic_ce.domains.common.models import Address
from datamimic_ce.domains.ecommerce.models.order import Order
from datamimic_ce.domains.ecommerce.services import OrderService


class TestEntityOrder:
    _supported_datasets = ["US",]

    def _check_order_data(self, order: Order):
        assert isinstance(order, Order)
        assert isinstance(order.order_id, str)
        assert isinstance(order.user_id, str)
        assert isinstance(order.product_list, list)
        assert isinstance(order.total_amount, float)
        assert isinstance(order.date, datetime.datetime)
        assert isinstance(order.status, str)
        assert isinstance(order.payment_method, str)
        assert isinstance(order.shipping_method, str)
        assert isinstance(order.shipping_address, Address)
        assert isinstance(order.billing_address, Address)
        assert isinstance(order.currency, str)
        assert isinstance(order.tax_amount, float)
        assert isinstance(order.shipping_amount, float)
        assert isinstance(order.discount_amount, float)
        assert isinstance(order.coupon_code, str | None)
        assert isinstance(order.notes, str | None)
        assert isinstance(order.to_dict(), dict)

        assert order.order_id is not None
        assert order.user_id is not None
        assert order.product_list is not None
        assert order.total_amount is not None
        assert order.date is not None
        assert order.status is not None
        assert order.payment_method is not None
        assert order.shipping_method is not None
        assert order.shipping_address is not None
        assert order.billing_address is not None
        assert order.currency is not None
        assert order.shipping_amount is not None
        assert order.tax_amount is not None
        assert order.discount_amount is not None
        assert order.coupon_code is not None if order.discount_amount > 0 else order.coupon_code is None
        assert order.to_dict() is not None

    def test_generate_single_order(self):
        order_service = OrderService()
        order = order_service.generate()
        self._check_order_data(order)

    def test_generate_multiple_order(self):
        order_service = OrderService()
        orders = order_service.generate_batch(100)
        assert len(orders) == 100
        for order in orders:
            self._check_order_data(order)

    def test_order_property_cache(self):
        order_service = OrderService()
        order = order_service.generate()
        assert order.order_id == order.order_id
        assert order.user_id == order.user_id
        assert order.product_list == order.product_list
        assert order.total_amount == order.total_amount
        assert order.date == order.date
        assert order.status == order.status
        assert order.payment_method == order.payment_method
        assert order.shipping_method == order.shipping_method   
        assert order.shipping_address == order.shipping_address
        assert order.billing_address == order.billing_address
        assert order.currency == order.currency
        assert order.tax_amount == order.tax_amount
        assert order.shipping_amount == order.shipping_amount
        assert order.discount_amount == order.discount_amount
        assert order.coupon_code == order.coupon_code
        assert order.notes == order.notes   

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        order_service = OrderService()
        order1 = order_service.generate()
        order2 = order_service.generate()
        assert order1.to_dict() != order2.to_dict()
        assert order1.order_id != order2.order_id
        assert order1.user_id != order2.user_id

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        order_service = OrderService(dataset=dataset)
        order = order_service.generate()
        self._check_order_data(order)

    def test_not_supported_dataset(self):
        random_dataset = "XX"
        # Raise FileNotFoundError because not found csv file of unsupported dataset
        # OR ValueError Address data not found
        with pytest.raises((FileNotFoundError, ValueError)):
            order_service = OrderService(dataset=random_dataset)
            order_service.generate()
