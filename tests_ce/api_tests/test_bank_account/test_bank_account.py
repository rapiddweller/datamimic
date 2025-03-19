from datetime import datetime
import pytest
from datamimic_ce.domains.finance.services.bank_account_service import BankAccountService
from datamimic_ce.domains.finance.models.bank_account import BankAccount

class TestBankAccount:
    _supported_datasets = ["US", "DE"]
    def _test_single_bank_account(self, bank_account: BankAccount):
        assert isinstance(bank_account, BankAccount)
        assert isinstance(bank_account.account_number, str)
        assert isinstance(bank_account.iban, str)
        assert isinstance(bank_account.account_type, str)
        assert isinstance(bank_account.balance, float)
        assert isinstance(bank_account.currency, str)
        assert isinstance(bank_account.created_date, datetime)
        assert isinstance(bank_account.last_transaction_date, datetime)
        assert isinstance(bank_account.bank_name, str)
        assert isinstance(bank_account.bank_code, str)
        assert isinstance(bank_account.bic, str)
        assert isinstance(bank_account.bin, str)

        assert bank_account.account_number is not None
        assert bank_account.account_number != ""
        assert bank_account.iban is not None
        assert bank_account.iban != ""
        assert bank_account.account_type is not None
        assert bank_account.account_type != ""
        assert bank_account.balance is not None
        assert bank_account.balance != ""
        assert bank_account.currency is not None
        assert bank_account.currency != ""
        assert bank_account.created_date is not None
        assert bank_account.created_date != ""
        assert bank_account.bank_code != ""
        assert bank_account.bic is not None 
        assert bank_account.bin is not None
        assert bank_account.bin != ""

    def test_generate_single_bank_account(self):
        bank_account_service = BankAccountService()
        bank_account = bank_account_service.generate()
        self._test_single_bank_account(bank_account)

    def test_generate_multiple_bank_accounts(self): 
        bank_account_service = BankAccountService()
        bank_accounts = bank_account_service.generate_batch(10)
        assert len(bank_accounts) == 10
        for bank_account in bank_accounts:
            self._test_single_bank_account(bank_account)

    def test_bank_account_property_cache(self):
        bank_account_service = BankAccountService()
        bank_account = bank_account_service.generate()
        assert bank_account is not None
        assert bank_account.account_number == bank_account.account_number
        assert bank_account.iban == bank_account.iban
        assert bank_account.account_type == bank_account.account_type
        assert bank_account.bank_code == bank_account.bank_code
        assert bank_account.bic == bank_account.bic
        assert bank_account.bin == bank_account.bin
        assert bank_account.balance == bank_account.balance
        assert bank_account.currency == bank_account.currency
        assert bank_account.created_date == bank_account.created_date
        assert bank_account.last_transaction_date == bank_account.last_transaction_date
        assert bank_account.bank_name == bank_account.bank_name

    @pytest.mark.flaky(reruns=10)
    def test_two_different_entities(self):
        bank_account_service = BankAccountService()
        bank_account1 = bank_account_service.generate()
        bank_account2 = bank_account_service.generate()
        assert bank_account1 is not None
        assert bank_account2 is not None
        assert bank_account1.account_number != bank_account2.account_number
        assert bank_account1.iban != bank_account2.iban
        assert bank_account1.account_type != bank_account2.account_type
        assert bank_account1.bank_code != bank_account2.bank_code
        assert bank_account1.bic != bank_account2.bic
        assert bank_account1.bin != bank_account2.bin
        assert bank_account1.balance != bank_account2.balance
        assert bank_account1.currency != bank_account2.currency
        assert bank_account1.created_date != bank_account2.created_date
        assert bank_account1.last_transaction_date != bank_account2.last_transaction_date
        assert bank_account1.bank_name != bank_account2.bank_name

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        bank_account_service = BankAccountService(dataset=dataset)      
        bank_account = bank_account_service.generate()
        self._test_single_bank_account(bank_account)

    def test_not_supported_dataset(self):
        bank_account_service = BankAccountService(dataset="FR")
        bank_account = bank_account_service.generate()
        with pytest.raises(FileNotFoundError):
            bank_account.to_dict()