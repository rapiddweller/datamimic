import random
import string
import pytest
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.services.address_service import AddressService


class TestEntityAddress:
    _supported_datasets = ["AD", "AL", "AT", "AU", "BA", "BE", "BG", "BR", "CA", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GB", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MC", "NL", "NO", "NZ", "PL", "PT", "RO", "RU", "SE", "SI", "SK", "SM", "TH", "TR", "UA", "US", "VA", "VE", "VN"]
    def _test_single_address(self, address: Address):
        assert isinstance(address, Address)
        assert isinstance(address.street, str)
        assert isinstance(address.house_number, str)
        assert isinstance(address.city, str)
        assert isinstance(address.state, str)
        assert isinstance(address.zip_code, str)
        assert isinstance(address.country, str)
        assert isinstance(address.country_code, str)
        assert isinstance(address.phone, str)
        assert isinstance(address.mobile_phone, str)
        assert isinstance(address.fax, str)
        assert isinstance(address.organization, str)

        assert address.street is not None
        assert address.house_number is not None
        assert address.city is not None
        assert address.state is not None
        assert address.zip_code is not None
        assert address.country is not None
        assert address.country_code is not None
        assert address.phone is not None
        assert address.mobile_phone is not None
        assert address.fax is not None
        assert address.organization is not None 
        
    def test_generate_single_address(self):
        address_service = AddressService()
        address = address_service.generate()
        self._test_single_address(address)

    def test_generate_multiple_addresses(self):
        address_service = AddressService()
        addresses = address_service.generate_batch(10)
        assert len(addresses) == 10
        for address in addresses:
            self._test_single_address(address)

    def test_address_property_cache(self):
        address_service = AddressService()
        address = address_service.generate()
        assert address.street == address.street
        assert address.house_number == address.house_number
        assert address.city == address.city
        assert address.state == address.state
        assert address.zip_code == address.zip_code
        assert address.country == address.country
        assert address.country_code == address.country_code
        assert address.phone == address.phone
        assert address.mobile_phone == address.mobile_phone
        assert address.fax == address.fax
        assert address.organization == address.organization

    def test_two_different_entities(self):
        address_service = AddressService()
        address1 = address_service.generate()
        address2 = address_service.generate()
        assert address1.street != address2.street
        assert address1.house_number != address2.house_number
        assert address1.city != address2.city
        assert address1.state != address2.state
        assert address1.zip_code != address2.zip_code
        assert address1.country == address2.country
        assert address1.country_code == address2.country_code
        assert address1.phone != address2.phone
        assert address1.mobile_phone != address2.mobile_phone
        assert address1.fax != address2.fax
        assert address1.organization != address2.organization

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        address_service = AddressService(dataset=dataset)
        address = address_service.generate()
        self._test_single_address(address)

    def test_not_supported_dataset(self):
        random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        while random_dataset in self._supported_datasets:
            random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        # Raise ValueError because Street name data not found for unsupported dataset
        with pytest.raises(ValueError):
            address_service = AddressService(dataset=random_dataset)
