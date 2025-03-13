# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Credit Card model.

This module defines the credit card model for the finance domain.
"""





import random
from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.finance.generators.credit_card_generators import CreditCardGenerator


class CreditCard(BaseEntity):
    def __init__(self, credit_card_generator: CreditCardGenerator):
        super().__init__()
        self._credit_card_generator = credit_card_generator
        
    
    @property
    @property_cache
    def card_type(self) -> str:
        return self._credit_card_generator.generate_card_type()
    
    @property
    @property_cache
    def card_number(self) -> str:
        return random.randint(1000000000000000, 9999999999999999)
    
    @property
    @property_cache
    def card_holder(self) -> str:
        return self._credit_card_generator.generate_card_holder()
    
    @property
    @property_cache
    def expiration_date(self) -> str:
        return self._credit_card_generator.generate_expiration_date()
    
    @property
    @property_cache
    def cvv(self) -> str:
        return self._credit_card_generator.generate_cvv()
    
    @property
    @property_cache
    def is_active(self) -> bool:
        return self._credit_card_generator.generate_is_active()
    
    @property
    @property_cache
    def credit_limit(self) -> float:
        return self._credit_card_generator.generate_credit_limit()
    
    @property
    @property_cache
    def current_balance(self) -> float:
        return self._credit_card_generator.generate_current_balance()
    
    @property
    @property_cache
    def issue_date(self) -> str:
        return self._credit_card_generator.generate_issue_date()
    
    @property
    @property_cache
    def bank_name(self) -> str:
        return self._credit_card_generator.generate_bank_name() 
    
    @property
    @property_cache
    def bank_code(self) -> str:
        return self._credit_card_generator.generate_bank_code()
    
    @property
    @property_cache
    def bic(self) -> str:
        return self._credit_card_generator.generate_bic()
    
    @property
    @property_cache
    def bin(self) -> str:
        return self._credit_card_generator.generate_bin()
    
    @property
    @property_cache
    def iban(self) -> str:  
        return self._credit_card_generator.generate_iban()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "card_type": self.card_type,
            "card_number": self.card_number,
            "card_holder": self.card_holder,
            "expiration_date": self.expiration_date,
            "cvv": self.cvv,
            "is_active": self.is_active,
            "credit_limit": self.credit_limit,
            "current_balance": self.current_balance,
            "issue_date": self.issue_date,
            "bank_name": self.bank_name,
            "bank_code": self.bank_code,
            "bic": self.bic,
            "bin": self.bin,
            "iban": self.iban
        }   
