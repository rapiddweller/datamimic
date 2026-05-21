# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.finance.models.bank import Bank

BANK_SCHEMA = EntitySchema(
    "Bank",
    (
        field("name", str, "Bank name."),
        field("swift_code", str, "SWIFT code."),
        field("routing_number", str, "Routing number."),
        field("bank_code", str, "Bank code."),
        field("bic", str, "Bank identifier code (BIC)."),
        field("bin", str, "Bank identification number (BIN)."),
        field("customer_service_phone", str, "Customer service phone number."),
    ),
)


class BankService(BaseDomainService[Bank]):
    DATASET_PATTERNS = ("finance/bank/banks_{CC}.csv",)

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(BankGenerator(dataset=dataset, rng=rng), Bank)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return BANK_SCHEMA.fields
