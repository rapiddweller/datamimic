# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.entities.entity_util import FieldGenerator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.file_util import FileUtil


class CountryEntity:
    """
    Represents a country entity with various attributes.

    This class provides methods to load and access country data from a CSV file.
    """

    def __init__(self, cls_factory_util: BaseClassFactoryUtil):
        """
        Initialize the CountryEntity.

        Args:
            cls_factory_util (BaseClassFactoryUtil): The class factory utility.
        """
        # Load file data
        self._data = FileUtil.read_csv_to_dict_of_tuples_without_header_and_fill_missing_value(
            Path(__file__).parent.joinpath("data/country.csv")
        )
        self._row_gen = FieldGenerator(
            lambda: self._data[cls_factory_util.get_data_generation_util().rnd_int(0, len(self._data) - 1)]
        )

    @property
    def iso_code(self):
        """
        Get the ISO code of the country.

        Returns:
            str: The ISO code of the country.
        """
        return self._row_gen.get()[0]

    @property
    def name(self):
        """
        Get the name of the country.

        Returns:
            str: The name of the country.
        """
        return self._row_gen.get()[4]

    @property
    def default_language_locale(self):
        """
        Get the default language locale of the country.

        Returns:
            str: The default language locale of the country.
        """
        return self._row_gen.get()[1]

    @property
    def phone_code(self):
        """
        Get the phone code of the country.

        Returns:
            str: The phone code of the country.
        """
        return self._row_gen.get()[2]

    @property
    def population(self):
        """
        Get the population of the country.

        Returns:
            int: The population of the country.
        """
        return int(self._row_gen.get()[5])

    def reset(self):
        """
        Reset the field generator.

        This method resets the field generator to its initial state.
        """
        self._row_gen.reset()
