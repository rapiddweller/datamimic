# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import string
from pathlib import Path

from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class DomainGenerator(BaseLiteralGenerator):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Generate random domain data for the requested dataset."""
        self._dataset = (dataset or "US").upper()  #  enforce ISO code so we always hit suffixed CSVs
        self._rng: random.Random = rng or random.Random()
        web_path = dataset_path("common", "net", f"webmailDomain_{self._dataset}.csv", start=Path(__file__))
        tld_path = dataset_path("common", "net", f"tld_{self._dataset}.csv", start=Path(__file__))

        # Load file data
        self._web_dataset = FileUtil.read_wgt_file(web_path)
        self._tld_dataset = FileUtil.read_wgt_file(tld_path)

        self._company_name: str | None = None
        # Share the deterministic RNG so seeded email/domain combos remain reproducible end-to-end.
        self._company_name_generator = CompanyNameGenerator(rng=self._rng)

    def generate(self) -> str:
        """
        create a domain
        """
        # Random generation mode selction
        random_mode = self._rng.choices([0, 1, 2], k=1)[0]
        # web domain generate
        if random_mode == 0:
            res = self._rng.choices(self._web_dataset[0], self._web_dataset[1], k=1)[0]
        # random domain generate
        elif random_mode == 1:
            tld = self._rng.choices(self._tld_dataset[0], self._tld_dataset[1], k=1)[0]
            random_name = "".join(self._rng.choices(string.ascii_lowercase, k=self._rng.randint(4, 12)))
            res = f"{random_name}.{tld}"
        # company domain generate
        else:
            company_name = self._company_name or self._company_name_generator.generate().lower()
            tld = self._rng.choices(self._tld_dataset[0], self._tld_dataset[1], k=1)[0]
            res = f"{company_name}.{tld}"

        return res

    def generate_with_company_name(self, company_name: str):
        """
        Generate with specific company name
        :param company_name:
        :return:
        """
        self._company_name = company_name
        return self.generate()
