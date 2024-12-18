# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import csv
import random
from pathlib import Path

from datamimic_ce.generators.generator import Generator
from datamimic_ce.logger import logger


class PhoneNumberGenerator(Generator):
    """
    Generator a random Phone Number
    Attributes:
        dataset:  Country ISO code (e.g. "US")
        area_code: phone area code
        is_mobile: True if generate mobile number
    """

    def __init__(
        self,
        dataset: str | None = "US",
        area_code: str | None = None,
        is_mobile: bool = False,
    ):
        self._dataset = (dataset or "US").upper()
        prefix_path = Path(__file__).parent.parent
        country_file_path = prefix_path.joinpath("entities/data/country.csv")
        try:
            with open(f"{country_file_path}") as file:
                country_reader = csv.reader(file, delimiter=",")
                country_codes = {}
                for country_reader_row in country_reader:
                    country_codes[country_reader_row[0]] = country_reader_row[2]
            self._country_codes = country_codes
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File not found: {country_file_path}") from err

        # use later when generate
        self._is_mobile = is_mobile

        if not is_mobile:
            if area_code:
                self._area_data = [area_code]
            else:
                prefix_path = Path(__file__).parent.parent
                city_file_name = f"entities/data/city/city_{dataset}.csv"
                city_file_path = prefix_path.joinpath(city_file_name)

                try:
                    with open(f"{city_file_path}") as file:
                        city_reader = csv.DictReader(file, delimiter=";")
                        area_codes = []
                        for city_reader_row in city_reader:
                            area_codes.append(city_reader_row["areaCode"])
                    # only get max 100 data
                    self._area_data = random.sample(area_codes, 100) if len(area_codes) > 100 else area_codes

                except FileNotFoundError:
                    # Load US datasets
                    logger.warning(f"Not support dataset: {dataset}, dataset change to 'US'")
                    city_file_path = prefix_path.joinpath("entities/data/city/city_US.csv")

                    with open(f"{city_file_path}") as file:
                        city_reader = csv.DictReader(file, delimiter=";")
                        area_codes = []
                        for city_reader_row in city_reader:
                            area_codes.append(city_reader_row["areaCode"])
                    # only get max 100 data
                    self._area_data = random.sample(area_codes, 100) if len(area_codes) > 100 else area_codes
                    self._dataset = "US"

    def generate(self) -> str:
        country_code = self._country_codes[self._dataset]
        if country_code is None or country_code.strip() == "":
            country_code = "0"

        if self._is_mobile:
            area_code = str(random.randint(100, 999))
        else:
            area_code = "0" if not self._area_data else random.choice(self._area_data)

        local_number_length = 10 - len(area_code)
        local_number = "".join(random.choices("0123456789", k=local_number_length))

        return f"+{country_code}-{area_code}-{local_number}"
