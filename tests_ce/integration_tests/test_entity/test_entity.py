# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


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

        noble_count = 0
        for customer in customers:
            if customer["gender"] == "female":
                assert customer["salutation"] == "Mrs."
                if customer["noble_title"] != "":
                    assert customer["noble_title"] in ["Baroness", "Countess", "Princess", "Queen"]
                    noble_count += 1
            if customer["gender"] == "male":
                assert customer["salutation"] == "Mr."
                if customer["noble_title"] != "":
                    assert customer["noble_title"] in ["Baron", "Count", "Prince", "King"]
                    noble_count += 1
            assert customer["given_name"] in customer["name"]
            assert customer["family_name"] in customer["name"]

        print(f"Noble's ratio: {noble_count/len(customers)}")
        default_noble_quota = 0.005
        noble_ratio = noble_count / len(customers)
        assert default_noble_quota * 0.8 < noble_ratio < default_noble_quota * 1.2

    def test_entity_product(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_product.xml")
        engine.test_with_timer()

    def test_entity_order(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_order.xml")
        engine.test_with_timer()

    def test_entity_invoice(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_invoice.xml")
        engine.test_with_timer()

    def test_entity_payment(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_payment.xml")
        engine.test_with_timer()

    def test_entity_transaction(self):
        """Test the TransactionEntity."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_transaction.xml")
        engine.test_with_timer()

    def test_entity_e_commerce(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_e_commerce.xml")
        engine.test_with_timer()

    def test_entity_user_account(self):
        """Test the UserAccountEntity."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_user_account.xml")
        engine.test_with_timer()

    def test_entity_crm(self):
        """Test the CRMEntity."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_crm.xml")
        engine.test_with_timer()

    def test_entity_digital_wallet(self):
        """Test the DigitalWalletEntity."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entity_digital_wallet.xml")
        engine.test_with_timer()
