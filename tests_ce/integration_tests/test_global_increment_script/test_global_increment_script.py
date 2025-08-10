# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.factory.datamimic_test_factory import DataMimicTestFactory

_test_dir = Path(__file__).resolve().parent
customer_factory = DataMimicTestFactory(_test_dir/"datamimic.xml", "customers")

customer = customer_factory.create()  # DataMimicTestFactory create only generate 1 entity
for order in customer["orders"]:
    order_id = order.get("oId")
    for line in order["line_items"]:
        print(f"oId:{order_id}_lId:{line.get('lId')}")