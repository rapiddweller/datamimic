# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.common.data_loaders.phone_number_loader import PhoneNumberDataLoader
from datamimic_ce.generators.generator import Generator


class PhoneNumberGenerator(Generator):
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

        # Initialize data loader
        self._data_loader = PhoneNumberDataLoader(country_code=self._dataset)

        # Load country codes
        self._country_codes = self._data_loader.load_country_codes()

        # Set area code data
        if not is_mobile:
            if area_code:
                self._area_data = [area_code]
            else:
                # Load area codes from data loader
                area_codes = self._data_loader.load_area_codes()
                # Only get max 100 data
                self._area_data = random.sample(area_codes, 100) if len(area_codes) > 100 else area_codes

                # If we had to fall back to US data, update the dataset
                if self._dataset != "US" and not any(area_codes):
                    self._dataset = "US"

    def generate(self) -> str:
        """Generate a random phone number.

        Returns:
            A formatted phone number string
        """
        country_code = self._country_codes.get(self._dataset, "0")
        if country_code is None or country_code.strip() == "":
            country_code = "0"

        if self._is_mobile:
            area_code = str(random.randint(100, 999))
        else:
            area_code = "0" if not self._area_data else random.choice(self._area_data)

        local_number_length = 10 - len(area_code)
        local_number = "".join(random.choices("0123456789", k=local_number_length))

        return f"+{country_code}-{area_code}-{local_number}"
