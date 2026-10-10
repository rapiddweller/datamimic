"""The domain facade re-exports canonical shared service types."""

from datamimic_ce.domains import api
from datamimic_ce.domains.shared.demographics.config import DemographicConfig
from datamimic_ce.domains.shared.services.address_service import AddressService
from datamimic_ce.domains.shared.services.city_service import CityService
from datamimic_ce.domains.shared.services.company_service import CompanyService
from datamimic_ce.domains.shared.services.country_service import CountryService
from datamimic_ce.domains.shared.services.person_service import PersonService


def test_domain_api_exports_canonical_shared_services() -> None:
    for name, api_type, owner_type in (
        ("AddressService", api.AddressService, AddressService),
        ("CityService", api.CityService, CityService),
        ("CompanyService", api.CompanyService, CompanyService),
        ("CountryService", api.CountryService, CountryService),
        ("PersonService", api.PersonService, PersonService),
        ("DemographicConfig", api.DemographicConfig, DemographicConfig),
    ):
        assert api_type is owner_type
        assert name in api.__all__
