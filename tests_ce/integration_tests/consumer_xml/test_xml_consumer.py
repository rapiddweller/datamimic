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


class TestConsumerXmlMinio:
    _test_dir = Path(__file__).resolve().parent

    def test_single_item_xml_with_source_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_single_item_xml_with_source_sp.xml")
        engine.test_with_timer()

    def test_single_item_xml_with_source_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_single_item_xml_with_source_mp.xml")
        engine.test_with_timer()

    def test_generate_single_item_xml(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_generate_single_item_xml.xml")
        engine.test_with_timer()

    def test_single_item_xml_source_scripted(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_single_item_xml_source_scripted.xml")
        engine.test_with_timer()
