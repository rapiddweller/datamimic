# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.utils.file_util import FileUtil


class TestEntity:
    _test_dir = Path(__file__).resolve().parent

    def _capture_descriptor(self, filename: str) -> dict:
        """Execute a descriptor and capture entity output for assertions."""

        # Reuse a single capture path so deterministic checks can assert generated payloads.
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename=filename,
            capture_test_result=True,
        )
        engine.test_with_timer()
        return engine.capture_result()

    def _capture_descriptor_twice(self, filename: str) -> tuple[dict, dict]:
        """Convenience helper to assert seeded reproducibility."""

        # Some descriptors expose rngSeed toggles that we need to compare across runs.
        first = self._capture_descriptor(filename)
        second = self._capture_descriptor(filename)
        return first, second

    def test_entity_person(self):
        res_a, res_b = self._capture_descriptor_twice("test_entity_person.xml")
        cohort_a = res_a.get("seeded_person_cohort", [])
        cohort_b = res_b.get("seeded_person_cohort", [])

        assert cohort_a == cohort_b, "Seeded cohort should replay deterministically"
        assert len(cohort_a) == 5
        assert all(28 <= row["age"] <= 35 for row in cohort_a)
        assert all(row["full_name"] and row["email"] for row in cohort_a)

    def test_entity_address(self):
        res_a, res_b = self._capture_descriptor_twice("test_entity_address.xml")
        households_a = res_a.get("seeded_households", [])
        households_b = res_b.get("seeded_households", [])

        assert households_a == households_b, "Seeded households should be reproducible"
        assert households_a, "Expected seeded households to be generated"
        assert all(30 <= row["resident_age"] <= 45 for row in households_a)
        assert all(row["street"] and row["city"] and row["country"] for row in households_a)

    def test_entity_bank_account(self):
        result = self._capture_descriptor("test_entity_bank_account.xml")
        fr_accounts = result.get("fr_bank_accounts", [])

        assert fr_accounts, "Expected FR bank accounts to be generated"
        assert all(account["iban"].startswith("FR") for account in fr_accounts)
        assert all(len(account["account_number"]) > 0 for account in fr_accounts)

    def test_entity_bank(self):
        result = self._capture_descriptor("test_entity_bank.xml")
        de_banks = result.get("seeded_de_banks", [])

        assert de_banks, "Expected DE banks to be generated"
        assert all(bank["bic"][4:6] == "DE" for bank in de_banks)
        assert all(bank["bank_code"] for bank in de_banks)

    def test_entity_city(self):
        result = self._capture_descriptor("test_entity_city.xml")
        de_cities = result.get("de_cities", [])

        assert de_cities, "Expected DE cities to be generated"
        assert all(city["country"] == "Deutschland" for city in de_cities)
        assert all(city["population"] is None or city["population"] >= 0 for city in de_cities)

    def test_entity_company(self):
        result = self._capture_descriptor("test_entity_company.xml")
        de_companies = result.get("de_companies", [])

        assert de_companies, "Expected DE companies to be generated"
        assert all(company["country"] == "Deutschland" for company in de_companies)
        assert all(company["sector"] for company in de_companies)

    def test_entity_country(self):
        result = self._capture_descriptor("test_entity_country.xml")
        fr_countries = result.get("fr_countries", [])

        assert fr_countries, "Expected FR country subset"
        valid_iso = {"FR", "BE", "CH", "CA", "MC", "LU"}
        assert all(country["iso_code"] in valid_iso for country in fr_countries)
        assert all(country["population"] for country in fr_countries)

    def test_entity_credit_card(self):
        res_a, res_b = self._capture_descriptor_twice("test_entity_credit_card.xml")
        seeded_cards_a = res_a.get("seeded_credit_cards", [])
        seeded_cards_b = res_b.get("seeded_credit_cards", [])

        assert seeded_cards_a == seeded_cards_b
        assert seeded_cards_a, "Expected seeded credit cards"
        assert all(32 <= card["card_holder_age"] <= 40 for card in seeded_cards_a)
        assert all(card["card_number"] for card in seeded_cards_a)

    def test_entity_person_relative_attribute(self):
        default_dataset = "US"
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="test_entity_person_relative_attribute.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result()
        customers = result.get("customer")
        dataset_root = Path(__file__).parent.parent.parent.parent / "datamimic_ce/domains/domain_data/common/person"
        file_name_male = dataset_root / f"givenName_male_{default_dataset}.csv"
        file_name_female = dataset_root / f"givenName_female_{default_dataset}.csv"
        male_data, wgt = FileUtil.read_wgt_file(file_name_male)
        female_data, wgt = FileUtil.read_wgt_file(file_name_female)

        noble_count = 0
        for customer in customers:
            if customer["gender"] == "female":
                assert customer["given_name"] in female_data
                assert customer["salutation"] == "Mrs."
                if customer["noble_title"] != "":
                    assert customer["noble_title"] in [
                        "Baroness",
                        "Countess",
                        "Princess",
                        "Queen",
                    ]
                    noble_count += 1
            if customer["gender"] == "male":
                assert customer["given_name"] in male_data
                assert customer["salutation"] == "Mr."
                if customer["noble_title"] != "":
                    assert customer["noble_title"] in [
                        "Baron",
                        "Count",
                        "Prince",
                        "King",
                    ]
                    noble_count += 1
            assert customer["given_name"].lower() or customer["given_name"][0] in customer["email"]
            assert customer["family_name"].lower() in customer["email"]
            assert customer["given_name"] in customer["name"]
            assert customer["family_name"] in customer["name"]

        print(f"Noble's ratio: {noble_count / len(customers)}")

        seeded_nobles = result.get("seeded_nobles", [])
        assert seeded_nobles, "Expected seeded nobles to be generated"
        assert all(40 <= noble["age"] <= 55 for noble in seeded_nobles)
        assert any(noble["noble_title"] for noble in seeded_nobles)
        assert all(noble["name"] for noble in seeded_nobles)

    def test_entities_seeded_patients(self):
        result_a, result_b = self._capture_descriptor_twice("test_entities.xml")
        patients_a = result_a.get("seeded_patients", [])
        patients_b = result_b.get("seeded_patients", [])

        assert patients_a == patients_b, "Seeded patients should be reproducible"
        assert patients_a, "Expected seeded patients"
        assert all(60 <= row["age"] <= 70 for row in patients_a)
        assert all(
            any("diabetes" in cond.lower() for cond in row.get("conditions", []))
            for row in patients_a
        )
        assert all(
            all("hypertension" not in cond.lower() for cond in row.get("conditions", []))
            for row in patients_a
        )

    def test_doctor_seeded_reproducible(self):
        res_a, res_b = self._capture_descriptor_twice("doctor.xml")

        assert res_a["doctors"] == res_b["doctors"]
        assert res_a["vn_doctors"] == res_b["vn_doctors"]
        assert all(doc["certifications"] for doc in res_a["doctors"])

    def test_patient_demographics(self):
        res_a, res_b = self._capture_descriptor_twice("patient.xml")

        seniors = res_a["seeded_senior_patients"]
        assert seniors == res_b["seeded_senior_patients"]

        assert seniors, "Expected seeded senior cohort to be populated"
        assert all(70 <= row["age"] <= 80 for row in seniors)
        assert all(
            all("hypertension" not in cond.lower() for cond in row.get("conditions", []))
            for row in seniors
        )
        assert any(
            any("diabetes" in cond.lower() for cond in row.get("conditions", [])) for row in seniors
        )

    def test_encounter_seed_replay(self):
        res_a, res_b = self._capture_descriptor_twice("encounter.xml")

        encounters = res_a["encounters"]
        assert encounters == res_b["encounters"]
        ages = [row["patient_age"] for row in encounters]
        assert ages and min(ages) >= 45 and max(ages) <= 65
        assert all(row["device_usage_logs"] for row in encounters)

    def test_policy_seeded_holder(self):
        res_a, res_b = self._capture_descriptor_twice("policy.xml")

        policies = res_a["insurance_policies"]
        assert policies == res_b["insurance_policies"]
        ages = [row["policy_holder"]["age"] for row in policies]
        assert ages and all(30 <= age <= 65 for age in ages)
        assert all(row["coverages"] for row in policies)

    def test_bank_account_transactions(self):
        result = self._capture_descriptor("bank_account.xml")
        accounts = result["bank_accounts"]
        assert accounts, "Expected bank accounts to be generated"
        for account in accounts:
            transactions = account["transactions"]
            assert len(transactions) == 5
            assert all(tx["account"]["account_number"] == account["account_number"] for tx in transactions)

    def test_customer_locale_splits(self):
        result_a, result_b = self._capture_descriptor_twice("customer.xml")

        assert len(result_a["customers"]) == 50
        assert result_a["customers"] == result_b["customers"]

        us_states = {row["state"] for row in result_a["us_customers"]}
        assert us_states, "US customers should expose state data"

        allowed_us_payments = {"CreditCard", "PayPal", "ApplePay", "CashOnDelivery"}
        assert set(row["preferred_payment"] for row in result_a["us_customers"]).issubset(allowed_us_payments)

        assert all("bundesland" in row for row in result_a["de_customers"])
        german_payments = {row["preferred_payment"] for row in result_a["de_customers"]}
        assert german_payments.issubset({"Klarna", "SEPA", "BankTransfer", "PayPal"})

    def test_bank_descriptor(self):
        result = self._capture_descriptor("bank.xml")
        banks = result["banks"]
        assert banks, "Expected banks to be generated"
        assert all(bank["bic"] and bank["swift_code"] for bank in banks)

    def test_hospital_multiregion_profiles(self):
        result = self._capture_descriptor("hospital.xml")
        hospitals = result["hospitals"]
        vn_hospitals = result["vn_hospitals"]
        de_hospitals = result["de_hospitals"]

        assert hospitals and vn_hospitals and de_hospitals
        assert all(row["departments"] for row in hospitals)
        assert all(row["staff_count"] for row in vn_hospitals)
        assert all(row["bed_count"] for row in de_hospitals)

    def test_medical_device_usage_logs(self):
        result = self._capture_descriptor("medical_device.xml")
        devices = result["medical_devices"]
        assert devices, "Expected medical devices"
        assert all(device["usage_logs"] and device["maintenance_history"] for device in devices)

    def test_medical_procedure_flags(self):
        result = self._capture_descriptor("medical_procedure.xml")
        procedures = result["medical_procedures"]
        assert procedures, "Expected medical procedures"
        assert any(proc["requires_anesthesia"] for proc in procedures)
        assert any(proc["is_surgical"] for proc in procedures)

    def test_order_locale_formatting(self):
        result = self._capture_descriptor("order.xml")

        assert result["orders"], "Expected orders"
        assert result["us_orders"], "Expected US orders"
        assert result["de_orders"], "Expected DE orders"

        us_totals = {row["total_formatted"] for row in result["us_orders"]}
        assert all(total.startswith("$") for total in us_totals)

        de_totals = {row["total_formatted"] for row in result["de_orders"]}
        assert all(total.endswith(" €") for total in de_totals)

    def test_insurance_product_coverages(self):
        result = self._capture_descriptor("product.xml")
        products = result["insurance_products"]
        assert products, "Expected insurance products"
        assert all(product["coverages"] for product in products)

    def test_transaction_dataset_switch(self):
        result = self._capture_descriptor("transaction.xml")
        tx_us = result["transactions"]
        tx_de = result["transactions_de"]
        assert tx_us and tx_de
        assert any(tx["currency"] == "EUR" for tx in tx_de)
        assert any(tx["currency"] == "USD" for tx in tx_us)

    def test_insurance_company_generation(self):
        result = self._capture_descriptor("company.xml")
        companies = result["insurance_companies"]
        assert companies, "Expected insurance companies"
        assert all(company["website"].startswith("http") for company in companies)

    def test_administration_office_seeded(self):
        # Seeded administration offices ensure regression coverage for all adapter-backed fields.
        res_a, res_b = self._capture_descriptor_twice("administration_office.xml")
        offices_a = res_a["administration_offices"]
        offices_b = res_b["administration_offices"]

        assert offices_a == offices_b, "Administration offices should replay deterministically"
        assert len(offices_a) == 3
        for office in offices_a:
            assert office["office_id"].startswith("ADM")
            assert office["name"] and office["type"]
            assert office["jurisdiction"]
            assert office["annual_budget"] > 0
            assert office["hours_of_operation"].get("Monday")
            assert office["services"] and office["departments"]
            assert office["leadership"]
            address = office["address"]
            assert address["street"] and address["city"]
            assert address["country"]

    def test_educational_institution_seeded(self):
        # Cover educational institution dataset plumbing with deterministic runs and attribute checks.
        res_a, res_b = self._capture_descriptor_twice("educational_institution.xml")
        institutions_a = res_a["educational_institutions"]

        assert institutions_a == res_b["educational_institutions"]
        assert len(institutions_a) == 3
        for institution in institutions_a:
            assert institution["institution_id"].startswith("EDU")
            assert institution["name"] and institution["type"] and institution["level"]
            assert institution["founding_year"] >= 1700
            assert institution["student_count"] >= institution["staff_count"]
            assert institution["programs"] and institution["facilities"]
            assert institution["accreditations"]
            address = institution["address"]
            assert address["postal_code"] and address["city"]

    def test_police_officer_seeded(self):
        # Public-sector guardrail for police officer entity covering seeded determinism and key attributes.
        res_a, res_b = self._capture_descriptor_twice("police_officer.xml")
        officers_a = res_a["police_officers"]

        assert officers_a == res_b["police_officers"]
        assert len(officers_a) == 4
        for officer in officers_a:
            assert officer["officer_id"].startswith("OFF")
            assert len(officer["badge_number"]) == 4 and officer["badge_number"].isdigit()
            assert officer["rank"] and officer["department"]
            assert officer["certifications"] and officer["languages"]
            assert officer["years_of_service"] >= 0
            assert officer["email"] and officer["phone"]
            address = officer["address"]
            assert address["city"] and address["country"]

    def test_insurance_coverage_seeded(self):
        # Keep insurance coverage selections deterministic and complete via seeded descriptor runs.
        res_a, res_b = self._capture_descriptor_twice("insurance_coverage.xml")
        coverages_a = res_a["insurance_coverages"]

        assert coverages_a == res_b["insurance_coverages"]
        assert len(coverages_a) == 6
        for coverage in coverages_a:
            assert coverage["code"]
            assert coverage["product_code"]
            assert coverage["name"]
            assert coverage["description"]
            assert coverage["min_coverage"]
            assert coverage["max_coverage"]

    def test_person_demographic_config_seeded(self):
        # Keep person demographic coverage descriptor-driven while verifying deterministic age bounds.
        res_a, res_b = self._capture_descriptor_twice("person_demographic.xml")
        cohort_a = res_a["seeded_persons_fixed_age"]

        assert cohort_a == res_b["seeded_persons_fixed_age"]
        assert all(person["age"] == 45 for person in cohort_a)
        assert all(person["transaction_profile"] is None for person in cohort_a)
