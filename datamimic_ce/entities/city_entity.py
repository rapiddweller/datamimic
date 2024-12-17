# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.logger import logger
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.file_util import FileUtil


class CityEntity:
    """
    Represents a city entity with various attributes.

    This class provides methods to load and access city data from CSV files.
    """

    def __init__(self, class_factory_util: BaseClassFactoryUtil, dataset: str = "US"):
        """
        Initialize the CityEntity.

        Args:
            class_factory_util (BaseClassFactoryUtil): The class factory utility.
            dataset (str): The dataset to be used. Defaults to "US".
        """
        self._dataset = dataset
        # Prepare data file path
        prefix_path = Path(__file__).parent
        city_file_path = prefix_path.joinpath(f"data/city/city_{dataset}.csv")
        state_file_path = prefix_path.joinpath(f"data/state/state_{dataset}.csv")

        try:
            # Load city data
            self._city_header_dict, self._city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(
                city_file_path, delimiter=";"
            )
            # Load state data
            state_headers, state_data = FileUtil.read_csv_to_dict_of_tuples_with_header(state_file_path)
        except FileNotFoundError:
            # Load US datasets
            logger.warning(f"Not support dataset: {dataset}, dataset change to 'US'")
            self._dataset = "US"

            # Load US city data
            us_city_path = prefix_path.joinpath("data/city/city_US.csv")
            self._city_header_dict, self._city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(
                us_city_path, delimiter=";"
            )

            # Load US state data
            us_state_path = prefix_path.joinpath("data/state/state_US.csv")
            state_headers, state_data = FileUtil.read_csv_to_dict_of_tuples_with_header(us_state_path)

        # Init state dict
        self._state_dict = dict(
            zip(
                [data[state_headers["id"]] for data in state_data],
                [data[state_headers["name"]] for data in state_data],
                strict=False,
            )
        )

        # Load country data
        country_path = prefix_path.joinpath("data/country.csv")
        country_df = FileUtil.read_csv_to_list_of_tuples_without_header(country_path, delimiter=",")

        self._country = ""
        for c in country_df:
            if c[0] == self._dataset:
                self._country = str(c[4])
                break

        self._city_data_len = len(self._city_data)

        name_idx = self._city_header_dict.get("name")
        postal_code_idx = self._city_header_dict.get("postalCode")
        population_idx = self._city_header_dict.get("population")
        name_extension_idx = self._city_header_dict.get("nameExtension")
        state_id_idx = self._city_header_dict.get("state.id")
        language_idx = self._city_header_dict.get("language")

        generator_fn_dict = {
            "city_row": lambda: self._city_data[
                class_factory_util.get_data_generation_util().rnd_int(0, self._city_data_len - 1)
            ],
            "name": lambda city_row: None if name_idx is None else city_row[name_idx],
            "postal_code": lambda city_row: None if postal_code_idx is None else city_row[postal_code_idx],
            "population": lambda city_row: None if population_idx is None else city_row[population_idx],
            "name_extension": lambda city_row: None if name_extension_idx is None else city_row[name_extension_idx],
            "state_id": lambda city_row: None if state_id_idx is None else city_row[state_id_idx],
            "language": lambda city_row: None if language_idx is None else city_row[language_idx],
        }
        self._field_generator = EntityUtil.create_field_generator_dict(generator_fn_dict)

    @property
    def name(self):
        """
        Get the name of the city.

        Returns:
            str: The name of the city.
        """
        return self._field_generator["name"].get(self._field_generator["city_row"].get())

    @property
    def postal_code(self):
        """
        Get the postal code of the city.

        Returns:
            str: The postal code of the city.
        """
        return self._field_generator["postal_code"].get(self._field_generator["city_row"].get())

    @property
    def area_code(self):
        """
        Get the area code of the city.

        Returns:
            str: The area code of the city.
        """
        return self._field_generator["postal_code"].get(self._field_generator["city_row"].get())

    @property
    def state(self):
        """
        Get the state where the city is located.

        Returns:
            str: The state where the city is located.
        """
        return self._state_dict.get(
            self._field_generator["state_id"].get(self._field_generator["city_row"].get()),
            "",
        )

    @property
    def language(self):
        """
        Get the language spoken in the city.

        Returns:
            str: The language spoken in the city.
        """
        return self._field_generator["language"].get(self._field_generator["city_row"].get())

    @property
    def country(self):
        """
        Get the country where the city is located.

        Returns:
            str: The country where the city is located.
        """
        return self._country

    @property
    def country_code(self):
        """
        Get the country code of the city.

        Returns:
            str: The country code of the city.
        """
        return self._dataset

    @property
    def population(self):
        """
        Get the population of the city.

        Returns:
            str: The population of the city.
        """
        return self._field_generator["population"].get(self._field_generator["city_row"].get())

    @property
    def name_extension(self):
        """
        Get the name extension of the city.

        Returns:
            str: The name extension of the city.
        """
        return self._field_generator["name_extension"].get(self._field_generator["city_row"].get())

    def reset(self):
        """
        Reset the field generators.

        This method resets all field generators to their initial state.
        """
        # TODO: split city data to many chunks
        for key in self._field_generator:
            self._field_generator[key].reset()
