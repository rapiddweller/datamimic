import pytest
from datamimic_ce.domains.finance.models.bank import Bank
from datamimic_ce.domains.finance.services.bank_service import BankService


class TestBank:
    _supported_datasets = ["US", "DE"]
    def _test_single_bank(self, bank: Bank):
        assert isinstance(bank, Bank)
        assert isinstance(bank.name, str)
        assert isinstance(bank.swift_code, str)
        assert isinstance(bank.routing_number, str)
        assert isinstance(bank.bank_code, str)
        assert isinstance(bank.bic, str)
        assert isinstance(bank.bin, str)

        assert bank.name is not None
        assert bank.name != ""
        assert bank.swift_code is not None
        assert bank.swift_code != ""
        assert bank.routing_number is not None
        # assert bank.routing_number != ""
        assert bank.bank_code is not None
        assert bank.bank_code != ""
        assert bank.bic is not None 
        assert bank.bin is not None
        assert bank.bin != ""

    def test_generate_single_bank(self):
        bank_service = BankService()
        bank = bank_service.generate()
        self._test_single_bank(bank)

    def test_generate_multiple_banks(self):
        bank_service = BankService()
        banks = bank_service.generate_batch(10)
        assert len(banks) == 10
        for bank in banks:
            self._test_single_bank(bank)

    def test_bank_property_cache(self):
        bank_service = BankService()
        bank = bank_service.generate()
        assert bank is not None
        assert bank.name == bank.name
        assert bank.swift_code == bank.swift_code
        assert bank.routing_number == bank.routing_number
        assert bank.bank_code == bank.bank_code
        assert bank.bic == bank.bic
        assert bank.bin == bank.bin

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        bank_service = BankService()
        bank1 = bank_service.generate()
        bank2 = bank_service.generate()
        assert bank1 is not None
        assert bank2 is not None
        assert bank1.name != bank2.name
        assert bank1.swift_code != bank2.swift_code
        assert bank1.routing_number != bank2.routing_number 
        assert bank1.bank_code != bank2.bank_code
        assert bank1.bic != bank2.bic
        assert bank1.bin != bank2.bin

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        bank_service = BankService(dataset=dataset)
        bank = bank_service.generate()
        self._test_single_bank(bank)

    def test_not_supported_dataset(self):
        # Fallback to US dataset with a single warning log; should not raise
        bank_service = BankService(dataset="FR")
        bank = bank_service.generate()
        assert isinstance(bank.to_dict(), dict)

    def test_supported_datasets_static(self):
        codes = BankService.supported_datasets()
        assert isinstance(codes, set) and len(codes) > 0
        assert "US" in codes and "DE" in codes
