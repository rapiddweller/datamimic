# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from datamimic_ce.interfaces.python.factory import DataMimicTestFactory

_test_dir = Path(__file__).resolve().parent
with TemporaryDirectory() as temporary_directory:
    project = shutil.copytree(
        _test_dir, Path(temporary_directory) / "project", ignore=shutil.ignore_patterns("output", "__pycache__")
    )
    customer_factory = DataMimicTestFactory(project / "datamimic.xml", "customers")
    customer = customer_factory.create()  # DataMimicTestFactory create only generate 1 entity
for order in customer["orders"]:
    order_id = order.get("oId")
    for line in order["line_items"]:
        print(f"oId:{order_id}_lId:{line.get('lId')}")
