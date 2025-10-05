from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class CreditCardGenerator(BaseDomainGenerator):
    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        demographic_config: DemographicConfig | None = None,
    ):
        self._dataset = dataset or "US"
        self._rng: random.Random = rng or random.Random()
        #  ensure person data (names/emails/phones) follow the selected dataset (DE/US)
        if demographic_config is None:
            from datamimic_ce.domains.common.models.demographic_config import DemographicConfig as _DC

            demographic_config = _DC()
        self._person_generator = PersonGenerator(
            dataset=self._dataset, rng=self._rng, demographic_config=demographic_config
        )
        self._date_generator = DateTimeGenerator(random=True, rng=self._derive_rng())
        self._bank_account_generator = BankAccountGenerator(dataset=self._dataset, rng=self._rng)
        self._card_types_cache: list[tuple] | None = None
        self._card_specs: dict | None = None

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def date_generator(self) -> DateTimeGenerator:
        return self._date_generator

    @property
    def bank_account_generator(self) -> BankAccountGenerator:
        return self._bank_account_generator

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Provide deterministic child RNGs so seeded credit-card descriptors replay consistently.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    @property
    def dataset(self) -> str:
        return self._dataset

    def generate_card_type(self) -> str:
        #  keep API returning type, but use dataset-specific specs
        return self.get_card_specs()["type"]

    def _load_card_types(self) -> list[tuple]:
        if self._card_types_cache is None:
            file_path = dataset_path("finance", "credit_card", f"card_types_{self._dataset}.csv", start=Path(__file__))
            self._card_types_cache = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)[1:]
        return self._card_types_cache

    def get_card_specs(self) -> dict:
        """
        Pick and cache a weighted card specification from dataset file.
        Returns: {type, prefix, length:int, cvv_length:int}
        """
        if self._card_specs is not None:
            return self._card_specs
        rows = self._load_card_types()
        # columns: type,prefix,length,cvv_length,weight
        weights = [float(r[4]) for r in rows]
        chosen = self._rng.choices(rows, weights=weights, k=1)[0]
        self._card_specs = {
            "type": chosen[0],
            "prefix": str(chosen[1]),
            "length": int(chosen[2]),
            "cvv_length": int(chosen[3]),
        }
        return self._card_specs
