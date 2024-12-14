# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestXMLTemplate:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_xml_template(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_xml_template.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_xml_template_2(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_xml_template_2.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_simple_xml_generate(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_simple_xml_generate.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_xml_template_script(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_xml_template_script.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_casting_xml_value(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_casting_xml_value.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()
