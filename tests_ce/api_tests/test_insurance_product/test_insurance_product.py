import pytest

from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage
from datamimic_ce.domains.insurance.models.insurance_product import InsuranceProduct
from datamimic_ce.domains.insurance.services.insurance_product_service import InsuranceProductService

class TestInsuranceProduct:
    _supported_datasets = ["US", "DE"]
    def _test_single_insurance_product(self, insurance_product: InsuranceProduct):
        assert isinstance(insurance_product, InsuranceProduct)
        assert isinstance(insurance_product.id, str)
        assert isinstance(insurance_product.type, str)
        assert isinstance(insurance_product.code, str)
        assert isinstance(insurance_product.description, str)
        assert isinstance(insurance_product.coverages, list)
        assert isinstance(insurance_product.coverages[0], InsuranceCoverage)

        assert insurance_product.id is not None
        assert insurance_product.type is not None
        assert insurance_product.code is not None
        assert insurance_product.description is not None
        assert insurance_product.coverages is not None

        assert insurance_product.id != ""
        assert insurance_product.type != ""
        assert insurance_product.code != ""
        assert insurance_product.description != ""
        assert insurance_product.coverages != []

    def test_generate_single_insurance_product(self):
        insurance_product_service = InsuranceProductService()
        insurance_product = insurance_product_service.generate()
        self._test_single_insurance_product(insurance_product)

    def test_generate_multiple_insurance_products(self):
        insurance_product_service = InsuranceProductService()
        insurance_products = insurance_product_service.generate_batch(10)
        assert len(insurance_products) == 10
        for insurance_product in insurance_products:
            self._test_single_insurance_product(insurance_product)

    def test_insurance_product_property_cache(self):    
        insurance_product_service = InsuranceProductService() 
        insurance_product = insurance_product_service.generate()
        assert insurance_product is not None
        assert insurance_product.id == insurance_product.id
        assert insurance_product.type == insurance_product.type
        assert insurance_product.code == insurance_product.code
        assert insurance_product.description == insurance_product.description
        assert insurance_product.coverages == insurance_product.coverages

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        insurance_product_service = InsuranceProductService(dataset=dataset)
        insurance_product = insurance_product_service.generate()
        self._test_single_insurance_product(insurance_product)

    def test_not_supported_dataset(self):
        insurance_product_service = InsuranceProductService(dataset="FR")
        product = insurance_product_service.generate()
        with pytest.raises(FileNotFoundError):
            product.to_dict()