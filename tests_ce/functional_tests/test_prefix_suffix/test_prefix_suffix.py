# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestPrefixSuffix:
    _test_dir = Path(__file__).resolve().parent

    def test_default_prefix_suffix(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_default_prefix_suffix.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        key_test = result["key_test"]
        assert len(key_test) == 10
        for k in key_test:
            id = k["id"]
            assert k["country_name"] == "VietNam"
            assert k["country_name_with_id"] == f"VietNam_{id}"
            assert k["country_name_with_addition_underscore"] == "_VietNam_"
            assert k["country_name_with_double_addition_underscore"] == "__VietNam__"

        variable_test = result["variable_test"]
        assert len(variable_test) == 10
        for v in variable_test:
            id = v["id"]
            assert v["country_name"] == "VietNam"
            assert v["country_name_with_id"] == f"VietNam_{id}"
            assert v["country_name_with_addition_underscore"] == "_VietNam_"
            assert v["country_name_with_double_addition_underscore"] == "__VietNam__"

        source_script_test = result["source_script_test"]
        assert len(source_script_test) == 3
        for s in source_script_test:
            party_id_code = s["partyIdCode"]
            assert s["partyId"] == f"party_no_{party_id_code}"

        mongo_created_data = result["mongo_suffix_prefix_test"]
        mongo_id_set = set()
        mongo_name_set = set()

        for created_data in mongo_created_data:
            mongo_id_set.add(created_data["user_id"])
            mongo_name_set.add(created_data["user_name"])

        mongo_all_data = result["mongo_all_data"]
        count_bob = 0
        bob_id_set = set()
        assert len(mongo_all_data) == 10
        for m in mongo_all_data:
            assert m["id"] is not None and m["id"] in mongo_id_set
            assert m["name"] is not None and m["name"] in mongo_name_set
            if m["name"] == "Bob":
                count_bob += 1
                bob_id_set.add(m["id"])

        bob_data = result["bob_data"]
        assert len(bob_data) == count_bob
        for bob in bob_data:
            assert bob["user_id"] in bob_id_set
            assert bob["user_name"] == "Bob"
