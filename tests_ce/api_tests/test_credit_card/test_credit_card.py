import pytest
import datetime
from datamimic_ce.domains.finance.models.credit_card import CreditCard
from datamimic_ce.domains.finance.services.credit_card_service import CreditCardService


class TestCreditCard:
    _supported_datasets = ["US", "DE"]
    def _test_single_credit_card(self, credit_card: CreditCard):
        assert isinstance(credit_card, CreditCard)
        assert isinstance(credit_card.card_number, str)
        assert isinstance(credit_card.card_type, str)
        assert isinstance(credit_card.expiration_date, datetime.datetime)
        assert isinstance(credit_card.cvv, str)
        assert isinstance(credit_card.cvc_number, str)
        assert isinstance(credit_card.is_active, bool)
        assert isinstance(credit_card.credit_limit, float)
        assert isinstance(credit_card.current_balance, float)
        assert isinstance(credit_card.issue_date, datetime.datetime)
        assert isinstance(credit_card.bank_name, str)
        assert isinstance(credit_card.bank_code, str)
        assert isinstance(credit_card.bic, str)
        assert isinstance(credit_card.bin, str)
        assert isinstance(credit_card.iban, str)

        assert credit_card.card_number is not None
        assert credit_card.card_number != ""
        assert credit_card.card_type is not None
        assert credit_card.card_type != ""
        assert credit_card.expiration_date is not None
        assert credit_card.expiration_date != ""
        assert credit_card.cvv is not None
        assert credit_card.cvv != ""
        assert credit_card.cvc_number is not None
        assert credit_card.cvc_number != ""
        assert credit_card.is_active is not None
        assert credit_card.is_active != ""
        assert credit_card.credit_limit is not None
        assert credit_card.bank_code != ""
        assert credit_card.bic is not None 
        assert credit_card.bin is not None
        assert credit_card.bin != ""

    def test_generate_single_credit_card(self):
        credit_card_service = CreditCardService()
        credit_card = credit_card_service.generate()
        self._test_single_credit_card(credit_card)

    def test_generate_multiple_credit_cards(self):
        credit_card_service = CreditCardService()
        credit_cards = credit_card_service.generate_batch(10)
        assert len(credit_cards) == 10
        for credit_card in credit_cards:
            self._test_single_credit_card(credit_card)

    def test_credit_card_property_cache(self):
        credit_card_service = CreditCardService()
        credit_card = credit_card_service.generate()
        assert credit_card is not None
        assert credit_card.card_number == credit_card.card_number
        assert credit_card.card_type == credit_card.card_type
        assert credit_card.expiration_date == credit_card.expiration_date
        assert credit_card.cvv == credit_card.cvv
        assert credit_card.cvc_number == credit_card.cvc_number
        assert credit_card.is_active == credit_card.is_active
        assert credit_card.credit_limit == credit_card.credit_limit
        assert credit_card.current_balance == credit_card.current_balance
        assert credit_card.issue_date == credit_card.issue_date
        assert credit_card.bank_name == credit_card.bank_name
        assert credit_card.bank_code == credit_card.bank_code
        assert credit_card.bic == credit_card.bic
        assert credit_card.bin == credit_card.bin
        assert credit_card.iban == credit_card.iban

    def test_two_different_entities(self):
        credit_card_service = CreditCardService()
        credit_card1 = credit_card_service.generate()
        credit_card2 = credit_card_service.generate()
        assert credit_card1 is not None
        assert credit_card2 is not None
        assert credit_card1.card_number != credit_card2.card_number
        assert credit_card1.expiration_date != credit_card2.expiration_date
        assert credit_card1.cvv != credit_card2.cvv
        assert credit_card1.cvc_number != credit_card2.cvc_number
        assert credit_card1.is_active != credit_card2.is_active
        assert credit_card1.credit_limit != credit_card2.credit_limit
        assert credit_card1.current_balance != credit_card2.current_balance
        assert credit_card1.issue_date != credit_card2.issue_date
        assert credit_card1.bank_name != credit_card2.bank_name
        assert credit_card1.bank_code != credit_card2.bank_code
        assert credit_card1.bic != credit_card2.bic
        assert credit_card1.bin != credit_card2.bin
        assert credit_card1.iban != credit_card2.iban

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        credit_card_service = CreditCardService(dataset=dataset)
        credit_card = credit_card_service.generate()
        self._test_single_credit_card(credit_card)

    def test_not_supported_dataset(self):
        credit_card_service = CreditCardService(dataset="FR")
        credit_card = credit_card_service.generate()
        with pytest.raises(FileNotFoundError):
            credit_card.to_dict()