# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDatamimicDemo:
    _test_dir = Path(__file__).resolve().parent

    def test_a_simple_script(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="a-simple-script/datamimic.xml")
        test_engine.test_with_timer()

    def test_b_simple_database(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="b-simple-database/datamimic.xml")
        test_engine.test_with_timer()

    def test_c_simple_anonymization(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="c-simple-anonymization/datamimic.xml")
        test_engine.test_with_timer()

    def test_d_simple_postprocess(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="d-simple-postprocess/datamimic.xml")
        test_engine.test_with_timer()

    def test_e_simple_composite_key(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="e-simple-compositekey/datamimic.xml")
        test_engine.test_with_timer()

    def test_f_simple_python(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="f-simple-python/datamimic.xml")
        test_engine.test_with_timer()

    def test_j_json(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="j-json/datamimic.xml")
        test_engine.test_with_timer()

    def test_h_converter(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="h-converter/datamimic.xml")
        test_engine.test_with_timer()

    def test_n_mongo(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="n-mongodb/datamimic.xml")
        test_engine.test_with_timer()

    def test_o_datetime(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="o-datetime/datamimic.xml")
        test_engine.test_with_timer()

    def test_k_watermark(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="k-watermark/datamimic.xml")
        test_engine.test_with_timer()

    def test_p_xml(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="p-xml/datamimic.xml")
        test_engine.test_with_timer()

    def test_g_entity(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="g-entity/datamimic.xml")
        test_engine.test_with_timer()

    def test_demo_custom_components(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="demo-custom-components/datamimic.xml")
        test_engine.test_with_timer()

    def test_demo_db_mapping(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="demo-db-mapping/datamimic.xml")
        test_engine.test_with_timer()

    def test_demo_condition(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="demo-condition/datamimic.xml")
        test_engine.test_with_timer()

    def test_demo_selector(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="demo-selector/datamimic.xml")
        test_engine.test_with_timer()