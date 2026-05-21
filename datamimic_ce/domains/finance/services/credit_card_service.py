# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from random import Random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import AttributeSpec, specs
from datamimic_ce.domains.finance.generators.credit_card_generator import CreditCardGenerator
from datamimic_ce.domains.finance.models.credit_card import CreditCard


class CreditCardService(BaseDomainService[CreditCard]):
    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        rng: Random | None = None,
    ):
        super().__init__(
            CreditCardGenerator(
                dataset=dataset, demographic_config=demographic_config, rng=rng
            ),
            CreditCard,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return specs(
            ("card_type", "str", "Card type (e.g. Visa, Mastercard)."),
            ("card_number", "str", "Full card number."),
            ("card_provider", "str", "Card network provider."),
            ("card_holder", "str", "Cardholder name."),
            ("expiration_date", "datetime", "Card expiration date."),
            ("cvv", "str", "Card verification value."),
            ("cvc_number", "str", "Card verification code."),
            ("is_active", "bool", "Whether the card is active."),
            ("credit_limit", "float", "Credit limit amount."),
            ("current_balance", "float", "Current outstanding balance."),
            ("issue_date", "datetime", "Card issue date."),
            ("bank_name", "str", "Issuing bank name."),
            ("bank_code", "str", "Issuing bank code."),
            ("bic", "str", "Bank identifier code (BIC)."),
            ("bin", "str", "Bank identification number (BIN)."),
            ("iban", "str", "International bank account number."),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["finance/credit_card/card_types_{CC}.csv"], start=Path(__file__))
