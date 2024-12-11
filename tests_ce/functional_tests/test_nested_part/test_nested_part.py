# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestNestedPart:
    @pytest.fixture
    def test_dir(self):
        return Path(__file__).resolve().parent

    def test_nested_part_with_csv_source_scripted(self, test_dir):
        """
        Test if the output of generation match the expect result.
        For example check if the age column is a number , which mean the source script is evaluate correctly
        Args:
            test_dir (): current test dir
        """
        engine = DataMimicTest(
            test_dir=test_dir, filename="test_nested_part_csv_source_scripted.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()
        customer = result["customer"]
        data = result["data"]

        assert len(customer) == 6
        assert len(data) == 24

        ids = ["0001", "0002", "0003", "0004"]
        phones = ["Y", "N", " ", "Y"]
        times = [
            "2022-09-15 14:12:00.008",
            "2022-10-10 10:12:36.112",
            "2023-01-29 22:49:33.997",
            "2023-02-15 03:30:27.845",
        ]
        sms = ["No", "Yes", "No", "Yes"]
        email = ["Yes", "No", "No", "No"]
        for x in range(0, 24):
            cs_id = data[x]["cs_id"]
            assert cs_id == ids[int(x % 4)]

            send_info = data[x]["send_info"]
            assert len(send_info) == 2
            for s in range(0, 2):
                assert send_info[s]["phone"] == phones[int(x % 4)]
                assert send_info[s]["time"] == times[int(x % 4)]

                contact = send_info[s]["contact"]
                assert len(contact) == 3
                for c in range(0, 3):
                    assert contact[c]["email"] == email[int(s % 2)]
                    assert contact[c]["SMS"] == sms[int(s % 2)]

    def test_nested_part_with_memstore(self, test_dir):
        engine = DataMimicTest(test_dir=test_dir, filename="test_nested_part_memstore.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        people = result.get("people")
        assert len(people) == 10

        person_name = ["Alice", "Bob", "Cathay"]
        person_pet = ["alice_pet", "bob_pet", "cathay_pet"]
        for p in people:
            csv_1 = p.get("csv_1")
            assert len(csv_1) == 1
            assert csv_1[0]["name"] == "Alice"
            assert csv_1[0]["pet_file"] == "alice_pet"

            csv_2 = csv_1[0].get("csv_2")
            assert len(csv_2) == 5
            for idx_2 in range(len(csv_2)):
                assert csv_2[idx_2]["name"] == person_name[(idx_2 % 3)]
                assert csv_2[idx_2]["pet_file"] == person_pet[(idx_2 % 3)]

                csv_3 = csv_2[idx_2]["csv_3"]
                assert len(csv_3) == 10
                for idx_3 in range(len(csv_3)):
                    assert csv_3[idx_3]["name"] == person_name[(idx_3 % 3)]
                    assert csv_3[idx_3]["pet_file"] == person_pet[(idx_3 % 3)]
                    assert csv_3[idx_3]["id"] == str(idx_3 + 1)
