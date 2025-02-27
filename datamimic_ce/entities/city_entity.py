# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Callable
from pathlib import Path
from typing import Any

from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.logger import logger
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.file_util import FileUtil


class CityEntity:
    """
    Represents a city entity with various attributes.

    This class provides methods to load and access city data from CSV files.
    """

    # Module-level cache to avoid repeated file I/O
    _CITY_DATA_CACHE: dict[str, tuple[dict[str, int], list[tuple]]] = {}
    _STATE_DATA_CACHE: dict[str, dict[str, str]] = {}
    _COUNTRY_NAME_CACHE: dict[str, str] = {}

    # Regional fallbacks for countries - same as AddressEntity but defined here for independence
    _REGIONAL_FALLBACKS: dict[str, tuple[str, ...]] = {
        # Western Europe fallbacks
        "DE": ("AT", "CH", "LU"),  # German-speaking
        "FR": ("BE", "CH", "LU", "MC"),  # French-speaking
        "IT": ("CH", "SM", "VA"),  # Italian-speaking
        "NL": ("BE", "LU"),  # Dutch-speaking
        # Nordic fallbacks
        "SE": ("NO", "DK", "FI"),  # Scandinavian
        "NO": ("SE", "DK", "FI"),
        "DK": ("NO", "SE", "DE"),
        "FI": ("SE", "EE"),
        # Eastern Europe fallbacks
        "PL": ("CZ", "SK", "DE"),
        "CZ": ("SK", "PL", "AT"),
        "SK": ("CZ", "PL", "HU"),
        "HU": ("SK", "RO", "AT"),
        # Balkan fallbacks
        "BA": ("HR", "RS", "SI"),  # Bosnia fallbacks
        "HR": ("SI", "BA", "AT"),
        "RS": ("BA", "BG", "RO"),
        # English-speaking fallbacks
        "US": ("CA", "GB", "AU"),
        "GB": ("IE", "US", "CA"),
        "CA": ("US", "GB"),
        "AU": ("NZ", "GB", "US"),
        "NZ": ("AU", "GB", "US"),
    }

    # Default dataset if none available
    _DEFAULT_DATASET = "US"

    # Chunk size for city data (for memory efficiency)
    _CHUNK_SIZE = 100

    def __init__(self, class_factory_util: BaseClassFactoryUtil, dataset: str = "US"):
        """
        Initialize the CityEntity.

        Args:
            class_factory_util (BaseClassFactoryUtil): The class factory utility.
            dataset (str): The dataset to be used. Defaults to "US".
        """
        self._dataset = dataset
        self._data_generation_util = class_factory_util.get_data_generation_util()

        # Load data with better error handling and caching
        self._load_data()

        # Set up chunked city data
        self._city_data_len = len(self._city_data)
        self._city_chunks = self._create_city_chunks()

        # Initialize field generators with optimized lambda functions
        self._init_field_generators(class_factory_util)

        # Initialize current chunk and index within chunk
        self._current_chunk_index = 0
        self._current_index_in_chunk = -1  # Start at -1 so first increment sets it to 0

    def _load_data(self) -> None:
        """
        Load city and state data with caching and fallback mechanisms.
        """
        # Check if we already have this dataset in cache
        if self._dataset in self._CITY_DATA_CACHE:
            self._city_header_dict, self._city_data = self._CITY_DATA_CACHE[self._dataset]
            self._state_dict = self._STATE_DATA_CACHE.get(self._dataset, {})
            self._country = self._COUNTRY_NAME_CACHE.get(self._dataset, "")
            return

        # Prepare data file path
        prefix_path = Path(__file__).parent
        city_file_path = prefix_path.joinpath(f"data/city/city_{self._dataset}.csv")
        state_file_path = prefix_path.joinpath(f"data/state/state_{self._dataset}.csv")

        # Try to load the requested dataset
        try:
            # Load city data
            self._city_header_dict, self._city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(
                city_file_path, delimiter=";"
            )
            # Load state data
            state_headers, state_data = FileUtil.read_csv_to_dict_of_tuples_with_header(state_file_path)

            # Build state dictionary
            self._state_dict = dict(
                zip(
                    [data[state_headers["id"]] for data in state_data],
                    [data[state_headers["name"]] for data in state_data],
                    strict=False,
                )
            )

            # Cache the data
            self._CITY_DATA_CACHE[self._dataset] = (self._city_header_dict, self._city_data)
            self._STATE_DATA_CACHE[self._dataset] = self._state_dict

        except FileNotFoundError:
            # Try regional fallbacks first
            fallback_tried = False
            for fallback in self._REGIONAL_FALLBACKS.get(self._dataset, ()):
                try:
                    fallback_city_path = prefix_path.joinpath(f"data/city/city_{fallback}.csv")
                    fallback_state_path = prefix_path.joinpath(f"data/state/state_{fallback}.csv")

                    # Check if files exist
                    if not fallback_city_path.exists() or not fallback_state_path.exists():
                        continue

                    logger.info(f"Using regional fallback '{fallback}' for dataset '{self._dataset}'")

                    # Load city data from fallback
                    self._city_header_dict, self._city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(
                        fallback_city_path, delimiter=";"
                    )
                    # Load state data from fallback
                    state_headers, state_data = FileUtil.read_csv_to_dict_of_tuples_with_header(fallback_state_path)

                    # Build state dictionary
                    self._state_dict = dict(
                        zip(
                            [data[state_headers["id"]] for data in state_data],
                            [data[state_headers["name"]] for data in state_data],
                            strict=False,
                        )
                    )

                    # Update dataset to fallback for country lookup
                    self._dataset = fallback
                    fallback_tried = True
                    break

                except Exception as e:
                    logger.warning(f"Error loading fallback {fallback}: {e}")
                    continue

            # If no fallbacks worked, use US as last resort
            if not fallback_tried:
                logger.warning(f"Dataset '{self._dataset}' not found, falling back to 'US'")
                self._dataset = self._DEFAULT_DATASET

                # Load US city data
                us_city_path = prefix_path.joinpath("data/city/city_US.csv")
                self._city_header_dict, self._city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(
                    us_city_path, delimiter=";"
                )

                # Load US state data
                us_state_path = prefix_path.joinpath("data/state/state_US.csv")
                state_headers, state_data = FileUtil.read_csv_to_dict_of_tuples_with_header(us_state_path)

                # Build state dictionary
                self._state_dict = dict(
                    zip(
                        [data[state_headers["id"]] for data in state_data],
                        [data[state_headers["name"]] for data in state_data],
                        strict=False,
                    )
                )

                # Cache the US data if not already cached
                if self._DEFAULT_DATASET not in self._CITY_DATA_CACHE:
                    self._CITY_DATA_CACHE[self._DEFAULT_DATASET] = (self._city_header_dict, self._city_data)
                    self._STATE_DATA_CACHE[self._DEFAULT_DATASET] = self._state_dict

        # Load country data (only if we don't have it cached)
        if self._dataset not in self._COUNTRY_NAME_CACHE:
            country_path = prefix_path.joinpath("data/country.csv")
            country_df = FileUtil.read_csv_to_list_of_tuples_without_header(country_path, delimiter=",")

            self._country = ""
            for c in country_df:
                if c[0] == self._dataset:
                    self._country = str(c[4])
                    # Cache the country name
                    self._COUNTRY_NAME_CACHE[self._dataset] = self._country
                    break
        else:
            self._country = self._COUNTRY_NAME_CACHE[self._dataset]

    def _create_city_chunks(self) -> list[list[tuple]]:
        """
        Create chunks of city data for memory-efficient processing.

        Returns:
            List of city data chunks.
        """
        chunks = []
        total_cities = len(self._city_data)

        # If small enough dataset, just use as a single chunk
        if total_cities <= self._CHUNK_SIZE:
            chunks.append(self._city_data)
            return chunks

        # Otherwise, create chunks of appropriate size
        for i in range(0, total_cities, self._CHUNK_SIZE):
            end_idx = min(i + self._CHUNK_SIZE, total_cities)
            chunks.append(self._city_data[i:end_idx])

        return chunks

    def _init_field_generators(self, class_factory_util: BaseClassFactoryUtil) -> None:
        """
        Initialize field generators for city properties.

        Args:
            class_factory_util: The class factory utility.
        """
        # Extract indices for various fields
        name_idx = self._city_header_dict.get("name")
        postal_code_idx = self._city_header_dict.get("postalCode")
        population_idx = self._city_header_dict.get("population")
        name_extension_idx = self._city_header_dict.get("nameExtension")
        state_id_idx = self._city_header_dict.get("state.id")
        language_idx = self._city_header_dict.get("language")
        area_code_idx = self._city_header_dict.get("areaCode")

        # Define a method to get the next city row with chunking for memory efficiency
        def get_next_city_row():
            self._current_index_in_chunk += 1

            # If we've reached the end of the current chunk, move to the next chunk
            current_chunk = self._city_chunks[self._current_chunk_index]
            if self._current_index_in_chunk >= len(current_chunk):
                # Reset index and increment chunk
                self._current_index_in_chunk = 0
                self._current_chunk_index = (self._current_chunk_index + 1) % len(self._city_chunks)
                current_chunk = self._city_chunks[self._current_chunk_index]

            return current_chunk[self._current_index_in_chunk]

        # Define method to get a random city row (not sequential)
        def get_random_city_row():
            chunk_idx = self._data_generation_util.rnd_int(0, len(self._city_chunks) - 1)
            chunk = self._city_chunks[chunk_idx]
            idx_in_chunk = self._data_generation_util.rnd_int(0, len(chunk) - 1)
            return chunk[idx_in_chunk]

        # Create field generators with necessary lambda functions
        generator_fn_dict: dict[str, Callable[..., Any]] = {
            "city_row": get_random_city_row,  # Use random by default
            "sequential_city_row": get_next_city_row,  # Sequential access option
            "name": lambda city_row: None if name_idx is None else city_row[name_idx],
            "postal_code": lambda city_row: None if postal_code_idx is None else city_row[postal_code_idx],
            "population": lambda city_row: None if population_idx is None else city_row[population_idx],
            "name_extension": lambda city_row: None if name_extension_idx is None else city_row[name_extension_idx],
            "state_id": lambda city_row: None if state_id_idx is None else city_row[state_id_idx],
            "language": lambda city_row: None if language_idx is None else city_row[language_idx],
            "area_code": lambda city_row: None if area_code_idx is None else city_row[area_code_idx],
        }
        self._field_generator = EntityUtil.create_field_generator_dict(generator_fn_dict)

    @property
    def name(self) -> str:
        """
        Get the name of the city.

        Returns:
            str: The name of the city.
        """
        result = self._field_generator["name"].get(self._field_generator["city_row"].get())
        assert result is not None, "City name cannot be None"
        return result

    @property
    def postal_code(self) -> str:
        """
        Get the postal code of the city.

        Returns:
            str: The postal code of the city.
        """
        result = self._field_generator["postal_code"].get(self._field_generator["city_row"].get())
        assert result is not None, "Postal code cannot be None"
        return result

    @property
    def area_code(self) -> str:
        """
        Get the area code of the city.

        Returns:
            str: The area code of the city.
        """
        result = self._field_generator["area_code"].get(self._field_generator["city_row"].get())
        assert result is not None, "Area code cannot be None"
        return result

    @property
    def state(self) -> str:
        """
        Get the state where the city is located.

        Returns:
            str: The state where the city is located.
        """
        result = self._state_dict.get(
            self._field_generator["state_id"].get(self._field_generator["city_row"].get()) or "",
            "",
        )
        return result  # Already has a default empty string, so no assertion needed

    @property
    def language(self) -> str | None:
        """
        Get the language spoken in the city.

        Returns:
            str | None: The language spoken in the city, or None if not available.
        """
        return self._field_generator["language"].get(self._field_generator["city_row"].get())

    @property
    def country(self) -> str:
        """
        Get the country where the city is located.

        Returns:
            str: The country where the city is located.
        """
        return self._country

    @property
    def country_code(self) -> str:
        """
        Get the country code of the city.

        Returns:
            str: The country code of the city.
        """
        assert self._dataset is not None, "Country code cannot be None"
        return self._dataset

    @property
    def population(self) -> str:
        """
        Get the population of the city.

        Returns:
            str: The population of the city.
        """
        result = self._field_generator["population"].get(self._field_generator["city_row"].get())
        if result is None:
            return "0"  # Return a default population value when None is returned
        return result

    @property
    def name_extension(self) -> str:
        """
        Get the name extension of the city.

        Returns:
            str: The name extension of the city.
        """
        result = self._field_generator["name_extension"].get(self._field_generator["city_row"].get())
        if result is None:
            return ""  # Return a default empty string when None is returned
        return result

    def get_sequential_city(self) -> dict[str, Any]:
        """
        Get cities sequentially for batch processing.

        Returns:
            Dict containing the next city's data in sequence
        """
        city_row = self._field_generator["sequential_city_row"].get()

        # Build a complete city record
        return {
            "name": self._field_generator["name"].get(city_row),
            "postal_code": self._field_generator["postal_code"].get(city_row),
            "area_code": self._field_generator["area_code"].get(city_row),
            "state_id": self._field_generator["state_id"].get(city_row),
            "state": self._state_dict.get(self._field_generator["state_id"].get(city_row) or "", ""),
            "language": self._field_generator["language"].get(city_row),
            "population": self._field_generator["population"].get(city_row),
            "name_extension": self._field_generator["name_extension"].get(city_row),
            "country": self._country,
            "country_code": self._dataset,
        }

    def reset(self):
        """
        Reset the field generators.

        This method resets all field generators to their initial state and
        resets the chunk indices for sequential access.
        """
        # Reset all field generators
        for key in self._field_generator:
            self._field_generator[key].reset()

        # Reset chunk tracking
        self._current_chunk_index = 0
        self._current_index_in_chunk = -1
