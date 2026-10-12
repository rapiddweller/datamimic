# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import pytest

from datamimic_ce.domains.shared.generators.city_generator import CityGenerator, CityRecord
from datamimic_ce.domains.shared.models.city import City
from datamimic_ce.domains.shared.services.city_service import CityService


class TestCityGenerator:
    _supported_dataset = [
        "AD",
        "AL",
        "AT",
        "AU",
        "BA",
        "BE",
        "BG",
        "BR",
        "CA",
        "CH",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GB",
        "GR",
        "HR",
        "HU",
        "IE",
        "IS",
        "IT",
        "LI",
        "LT",
        "LU",
        "LV",
        "MC",
        "NL",
        "NO",
        "NZ",
        "PL",
        "PT",
        "RO",
        "RU",
        "SE",
        "SI",
        "SK",
        "SM",
        "TH",
        "TR",
        "US",
        "US",
        "VA",
        "VE",
        "VN",
    ]

    def test_generate_with_dataset(self):
        for dataset in self._supported_dataset:
            city_service = CityService(dataset)
            for _ in range(100):
                generated_city = city_service.generate()
                # check generate city
                assert generated_city is not None, "can not generate city"
                assert isinstance(generated_city, City)
                # check generate city attributes
                assert generated_city.name is not None, "can not generate city name"
                assert isinstance(generated_city.name, str)
                assert generated_city.postal_code is not None, "can not generate city postal_code"
                assert isinstance(generated_city.postal_code, str)
                # TODO: add test for state
                # assert generated_city.state is not None, "can not generate city state"
                # assert isinstance(generated_city.state, str)
                # language is optional

    def test_city_with_name_extension(self):
        city_service = CityService()
        for _ in range(100):
            generated_city = city_service.generate()
            if generated_city.name_extension is not None:
                assert isinstance(generated_city.name_extension, str)

    @pytest.mark.parametrize(
        ("population", "expected"),
        [("290736", 290736), ("", None), (None, None)],
    )
    def test_population_nullable_conversion_and_dict(
        self,
        monkeypatch: pytest.MonkeyPatch,
        population: str | None,
        expected: int | None,
    ) -> None:
        record: CityRecord = {
            "name": "Karlsruhe",
            "postal_code": "76131",
            "area_code": "721",
            "state": "BW",
            "language": "de",
            "population": population,
            "name_extension": "",
            "country": "Deutschland",
            "country_code": "DE",
        }
        generator = CityGenerator(dataset="DE")
        monkeypatch.setattr(generator, "get_random_city", lambda: record)

        city = City(generator)
        result = city.to_dict()

        assert "population" in result
        assert result["population"] == expected
        assert type(result["population"]) is type(expected)

    def test_population_rejects_malformed_numeric_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        record: CityRecord = {
            "name": "Karlsruhe",
            "postal_code": "76131",
            "area_code": "721",
            "state": "BW",
            "language": "de",
            "population": "not-a-number",
            "name_extension": "",
            "country": "Deutschland",
            "country_code": "DE",
        }
        generator = CityGenerator(dataset="DE")
        monkeypatch.setattr(generator, "get_random_city", lambda: record)

        with pytest.raises(ValueError):
            City(generator).to_dict()
