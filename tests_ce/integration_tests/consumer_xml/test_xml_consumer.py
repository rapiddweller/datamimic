#  Copyright (c) 2023 Rapiddweller Asia Co., Ltd.
#  All rights reserved.
#  #
#  This software and related documentation are provided under a license
#  agreement containing restrictions on use and disclosure and are
#  protected by intellectual property laws. Except as expressly permitted
#  in your license agreement or allowed by law, you may not use, copy,
#  reproduce, translate, broadcast, modify, license, transmit, distribute,
#  exhibit, perform, publish, or display any part, in any form, or by any means.
#  #
#  This software is the confidential and proprietary information of
#  Rapiddweller Asia Co., Ltd. ("Confidential Information"). You shall not
#  disclose such Confidential Information and shall use it only in accordance
#  with the terms of the license agreement you entered into with Rapiddweller Asia Co., Ltd.
#

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestConsumerXmlMinio:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_single_item_xml_with_source_sp(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_single_item_xml_with_source_sp.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_single_item_xml_with_source_mp(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_single_item_xml_with_source_mp.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_generate_single_item_xml(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_generate_single_item_xml.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_single_item_xml_source_scripted(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_single_item_xml_source_scripted.xml")
        await test_engine.test_with_timer()
