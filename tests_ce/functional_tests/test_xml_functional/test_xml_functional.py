# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestXmlFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_import_xml(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_import_xml.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        template_1 = result["template_1"]
        assert len(template_1) == 1
        for template in template_1:
            assert len(template["CodeList"]) == 4
            assert template["CodeList"]["Annotation"] is None
            assert len(template["CodeList"]["Identification"]) == 6
            assert len(template["CodeList"]["ColumnSet"]) == 2
            assert len(template["CodeList"]["SimpleCodeList"]) == 1
            row = template["CodeList"]["SimpleCodeList"]["Row"]
            assert len(row) == 7

    def test_export_xml(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_export_xml.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        task_id = engine.task_id
        file_path = self._test_dir.joinpath(f"output/{task_id}_xml_export_template_1/product_export_template_1_chunk_0.xml")
        tree = ET.parse(file_path)
        root = tree.getroot()

        assert root.tag == "CodeList"
        annotations = root.findall("Annotation")
        for annotation in annotations:
            assert len(annotation) == 0

        identifications = root.findall("Identification")
        for identification in identifications:
            assert len(identification) == 6

        column_sets = root.findall("ColumnSet")
        for column_set in column_sets:
            assert len(column_set) == 3

        simple_code_list = root.findall("SimpleCodeList")
        for simple_code in simple_code_list:
            assert len(simple_code) == 7

        rows = root.findall("Row")
        for row in rows:
            assert len(row) == 7

        # delete result folder
        folder_path = self._test_dir.joinpath("output")
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
