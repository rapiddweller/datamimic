# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestExporter:
    def test_multi_json(self, project_dir):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=project_dir, filename="multi_json.xml")
            test_engine.test_with_timer()

    def test_single_csv(self, project_dir):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=project_dir, filename="single_csv.xml")
            test_engine.test_with_timer()

    def test_single_combined(self, project_dir):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=project_dir, filename="single_combine_all.xml")
            test_engine.test_with_timer()

    def test_single_cascaded_cases(self, project_dir):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=project_dir, filename="single_cascaded_cases.xml")
            test_engine.test_with_timer()

    def test_multi_xml(self, project_dir):
        test_engine = DataMimicTest(test_dir=project_dir, filename="multi_xml.xml")
        test_engine.test_with_timer()
