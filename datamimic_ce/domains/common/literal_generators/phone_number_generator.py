# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class PhoneNumberGenerator(BaseLiteralGenerator):
    """
    Generator for random phone numbers.

    This class generates random phone numbers based on country and area codes
    loaded from data files through the PhoneNumberDataLoader.

    Attributes:
        dataset: Country ISO code (e.g. "US")
        area_code: phone area code
        is_mobile: True if generate mobile number
    """

    def __init__(
        self,
        dataset: str | None = "US",
        area_code: str | None = None,
        is_mobile: bool = False,
    ):
        """Initialize the PhoneNumberGenerator.

        Args:
            dataset: Country ISO code (e.g. "US")
            area_code: Specific area code to use (optional)
            is_mobile: Whether to generate a mobile number
        """
        self._dataset = (dataset or "US").upper()
        self._is_mobile = is_mobile

        from datamimic_ce.domains.common.generators import CountryGenerator

        country_generator = CountryGenerator()
        country_data = country_generator.get_country_by_iso_code(self._dataset)
        self._country_code = country_data[2]

        self._is_mobile = is_mobile
        self._area_code = area_code
        if area_code is not None:
            self._area_code = area_code
        else:
            from datamimic_ce.domains.common.generators import CityGenerator

            self._city_generator = CityGenerator(dataset=self._dataset)

    def generate(self) -> str:
        """Generate a random phone number.

        Returns:
            A formatted phone number string
        """
        if self._area_code is not None:
            area_code = self._area_code
        else:
            if self._is_mobile:
                area_code = str(random.randint(100, 999))
            else:
                area_code = self._city_generator.get_random_city()["area_code"]

        local_number_length = 10 - len(area_code)
        local_number = "".join(random.choices("0123456789", k=local_number_length))

        return f"+{self._country_code}-{area_code}-{local_number}"
