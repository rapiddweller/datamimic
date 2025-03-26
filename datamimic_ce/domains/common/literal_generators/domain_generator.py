# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import string
from pathlib import Path

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.utils.file_util import FileUtil


class DomainGenerator(BaseLiteralGenerator):
    def __init__(self):
        """
        Generate random domains.
        """
        # Prepare file path
        prefix_path = Path(__file__).parent.parent.parent.parent
        web_path = prefix_path.joinpath("domain_data/common/net/webmailDomain.csv")
        tld_path = prefix_path.joinpath("domain_data/common/net/tld.csv")

        # Load file data
        self._web_dataset = FileUtil.read_wgt_file(web_path)
        self._tld_dataset = FileUtil.read_wgt_file(tld_path)

        self._company_name = None
        self._company_name_generator = CompanyNameGenerator()

    def generate(self) -> str:
        """
        create a domain
        """
        # Random generation mode selction
        random_mode = random.choices([0, 1, 2], k=1)[0]
        # web domain generate
        if random_mode == 0:
            res = random.choices(self._web_dataset[0], self._web_dataset[1], k=1)[0]
        # random domain generate
        elif random_mode == 1:
            tld = random.choices(self._tld_dataset[0], self._tld_dataset[1], k=1)[0]
            random_name = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 12)))
            res = f"{random_name}.{tld}"
        # company domain generate
        else:
            company_name = self._company_name or self._company_name_generator.generate().lower()
            tld = random.choices(self._tld_dataset[0], self._tld_dataset[1], k=1)[0]
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
