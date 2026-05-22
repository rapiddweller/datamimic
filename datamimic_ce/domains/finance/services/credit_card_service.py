# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datetime import datetime
from random import Random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.finance.generators.credit_card_generator import CreditCardGenerator
from datamimic_ce.domains.finance.models.credit_card import CreditCard

CREDIT_CARD_SCHEMA = EntitySchema(
    "CreditCard",
    (
        field("card_type", str, "Card type (e.g. Visa, Mastercard)."),
        field("card_number", str, "Full card number."),
        field("card_provider", str, "Card network provider."),
        field("card_holder", str, "Cardholder name."),
        field("expiration_date", datetime, "Card expiration date."),
        field("cvv", str, "Card verification value."),
        field("cvc_number", str, "Card verification code."),
        field("is_active", bool, "Whether the card is active."),
        field("credit_limit", float, "Credit limit amount."),
        field("current_balance", float, "Current outstanding balance."),
        field("issue_date", datetime, "Card issue date."),
        field("bank_name", str, "Issuing bank name."),
        field("bank_code", str, "Issuing bank code."),
        field("bic", str, "Bank identifier code (BIC)."),
        field("bin", str, "Bank identification number (BIN)."),
        field("iban", str, "International bank account number."),
    ),
)


class CreditCardService(BaseDomainService[CreditCard]):
    DATASET_PATTERNS = ("finance/credit_card/card_types_{CC}.csv",)

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
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return CREDIT_CARD_SCHEMA.fields
