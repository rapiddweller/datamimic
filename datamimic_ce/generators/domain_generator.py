# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import string
from pathlib import Path

from datamimic_ce.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.file_util import FileUtil


class DomainGenerator(Generator):
    def __init__(self, generated_count: int):
        """
        Generate random domains.
        """
        # Prepare file path
        prefix_path = Path(__file__).parent
        web_path = prefix_path.joinpath("data/net/webmailDomain.csv")
        tld_path = prefix_path.joinpath("data/net/tld.csv")

        # Load file data
        self._web_iter = iter(FileUtil.select_records_from_wgt_file(web_path, count=generated_count))
        self._tld_iter = iter(FileUtil.select_records_from_wgt_file(tld_path, count=generated_count))

        self._company_name: str | None = None
        self._company_name_generator = CompanyNameGenerator()

    def generate(self) -> str:
        """
        create a domain
        """
        # Random generation mode selction
        random_mode = random.choices([0, 1, 2], k=1)[0]
        # web domain generate
        if random_mode == 0:
            res = next(self._web_iter)
        # random domain generate
        elif random_mode == 1:
            tld = next(self._tld_iter)
            random_name = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 12)))
            res = f"{random_name}.{tld}"
        # company domain generate
        else:
            company_name = self._company_name or self._company_name_generator.generate().lower()
            tld = next(self._tld_iter)
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
