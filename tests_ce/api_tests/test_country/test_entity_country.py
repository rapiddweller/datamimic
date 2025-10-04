
import pytest
from datamimic_ce.domains.common.models.country import Country
from datamimic_ce.domains.common.services.country_service import CountryService


class TestEntityCountry:
    _supported_datasets = ["US", "CA", "GB", "FR", "DE", "IT", "ES", "PT", "NL", "BE", "CH", "AT", "AU", "NZ", "PL", "CZ", "SK", "TR", "UA", "RU"]
    def _test_single_country(self, country: Country):
        assert isinstance(country, Country)
        assert isinstance(country.iso_code, str)
        assert isinstance(country.name, str)
        assert isinstance(country.default_language_locale, str)
        assert isinstance(country.phone_code, str)
        assert isinstance(country.population, str)

        assert country.iso_code is not None and country.iso_code != ""
        assert country.name is not None and country.name != ""
        assert country.default_language_locale is not None and country.default_language_locale != ""
        assert country.phone_code is not None and country.phone_code != ""
        assert country.population is not None and country.population != ""

    def test_generate_single_country(self):
        country_service = CountryService()
        country = country_service.generate()
        self._test_single_country(country)

    def test_generate_multiple_countries(self):
        country_service = CountryService()
        countries = country_service.generate_batch(10)
        assert len(countries) == 10
        for country in countries:
            self._test_single_country(country)

    def test_country_property_cache(self):
        country_service = CountryService()
        country = country_service.generate()
        country_data = country.country_data
        assert country_data["iso_code"] == country.iso_code
        assert country_data["name"] == country.name
        assert country_data["default_language_locale"] == country.default_language_locale
        assert country_data["phone_code"] == country.phone_code
        assert country_data["population"] == country.population

    @pytest.mark.flaky(reruns=3)
    def test_different_entities(self):
        country_service = CountryService()
        country1 = country_service.generate()
        country2 = country_service.generate()
        assert country1.iso_code != country2.iso_code
        assert country1.name != country2.name
        assert country1.default_language_locale != country2.default_language_locale
        assert country1.phone_code != country2.phone_code
        assert country1.population != country2.population

    def test_supported_datasets_static(self):
        codes = CountryService.supported_datasets()
        assert isinstance(codes, set) and len(codes) > 0
        assert "US" in codes and "DE" in codes
