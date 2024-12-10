# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.utils.file_util import FileUtil


class TestEntity:
    _test_dir = Path(__file__).resolve().parent

    def test_entity_person(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_person.xml")
        engine.test_with_timer()

    def test_entity_address(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_address.xml")
        engine.test_with_timer()

    def test_entity_bank_account(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_bank_account.xml")
        engine.test_with_timer()

    def test_entity_bank(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_bank.xml")
        engine.test_with_timer()

    def test_entity_city(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_city.xml")
        engine.test_with_timer()

    def test_entity_company(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_company.xml")
        engine.test_with_timer()

    def test_entity_country(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_country.xml")
        engine.test_with_timer()

    def test_entity_credit_card(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_credit_card.xml")
        engine.test_with_timer()

    def test_entity_person_relative_attribute(self):
        default_dataset = "US"
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_entity_person_relative_attribute.xml", capture_test_result=True
        )
        engine.test_with_timer()
        customers = engine.capture_result().get("customer")
        file_name_male = Path(__file__).parent.parent.parent.parent.joinpath(
            f"datamimic_ce/generators/data/person/givenName_male_{default_dataset}.csv"
        )
        file_name_female = Path(__file__).parent.parent.parent.parent.joinpath(
            f"datamimic_ce/generators/data/person/givenName_female_{default_dataset}.csv"
        )
        male_data, wgt = FileUtil.read_wgt_file(file_name_male)
        female_data, wgt = FileUtil.read_wgt_file(file_name_female)

        noble_count = 0
        for customer in customers:
            if customer["gender"] == "female":
                assert customer["given_name"] in female_data
                assert customer["salutation"] == "Mrs."
                if customer["noble_title"] != "":
                    assert customer["noble_title"] in ["Baroness", "Countess", "Princess", "Queen"]
                    noble_count += 1
            if customer["gender"] == "male":
                assert customer["given_name"] in male_data
                assert customer["salutation"] == "Mr."
                if customer["noble_title"] != "":
                    assert customer["noble_title"] in ["Baron", "Count", "Prince", "King"]
                    noble_count += 1
            assert customer["given_name"].lower() or customer["given_name"][0] in customer["email"]
            assert customer["family_name"].lower() in customer["email"]
            assert customer["given_name"] in customer["name"]
            assert customer["family_name"] in customer["name"]

        print(f"Noble's ratio: {noble_count/len(customers)}")
        default_noble_quota = 0.005
        noble_ratio = noble_count / len(customers)
        assert default_noble_quota * 0.8 < noble_ratio < default_noble_quota * 1.2
