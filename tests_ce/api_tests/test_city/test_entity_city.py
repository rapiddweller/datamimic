import random
import string
from typing import Optional
import pytest
from datamimic_ce.domains.common.models.city import City
from datamimic_ce.domains.common.services.city_service import CityService


class TestEntityCity:
    _supported_datasets = ["AD", "AL", "AT", "AU", "BA", "BE", "BG", "BR", "CA", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GB", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MC", "NL", "NO", "NZ", "PL", "PT", "RO", "RU", "SE", "SI", "SK", "SM", "TH", "TR", "UA", "US", "VA", "VE", "VN"]
    def _test_single_city(self, city: City):
        assert isinstance(city, City)
        assert isinstance(city.name, str)
        assert isinstance(city.country, str)
        assert isinstance(city.country_code, str)
        assert isinstance(city.state, str)
        assert isinstance(city.area_code, str)
        assert isinstance(city.postal_code, str)
        assert isinstance(city.name_extension, str) 
        assert isinstance(city.language, Optional[str])
        assert isinstance(city.population, Optional[int])

        assert city.name is not None
    def test_generate_single_city(self):
        city_service = CityService()
        city = city_service.generate()
        self._test_single_city(city)

    def test_generate_multiple_cities(self):
        city_service = CityService()
        cities = city_service.generate_batch(10)    
        assert len(cities) == 10    
        for city in cities:
            self._test_single_city(city)

    def test_city_property_cache(self):
        city_service = CityService()
        city = city_service.generate()
        assert city is not None
        assert city.name == city.name
        assert city.country == city.country
        assert city.country_code == city.country_code
        assert city.state == city.state
        assert city.area_code == city.area_code
        assert city.postal_code == city.postal_code
        assert city.name_extension == city.name_extension
        assert city.language == city.language
        assert city.population == city.population

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        city_service = CityService()
        city1 = city_service.generate()
        city2 = city_service.generate()
        assert city1.name != city2.name
        assert city1.country == city2.country
        assert city1.country_code == city2.country_code
        assert city1.state != city2.state
        assert city1.area_code != city2.area_code
        assert city1.postal_code != city2.postal_code
        assert city1.name_extension == "" or (city1.name_extension != city2.name_extension)
        assert city1.language == None or (city1.language != city2.language)
        assert city1.population == None or (city1.population != city2.population)

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        city_service = CityService(dataset=dataset)
        city = city_service.generate()   
        self._test_single_city(city)

    def test_not_supported_dataset(self):
        random_dataset = "XX"
        # Fallback to US dataset with a single warning log; should not raise
        city_service = CityService(dataset=random_dataset)
        city = city_service.generate()
        assert isinstance(city.to_dict(), dict)

    def test_supported_datasets_static(self):
        codes = CityService.supported_datasets()
        assert isinstance(codes, set) and len(codes) > 0
        assert "US" in codes and "DE" in codes
