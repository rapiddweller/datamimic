# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestConsumerJsonMinio:
    def test_json_consumer(self, project_dir):
        engine = DataMimicTest(test_dir=project_dir, filename="test_json_consumer.xml")
        engine.test_with_timer()
