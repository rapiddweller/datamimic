import pytest
from datamimic_ce.domains.insurance.models.insurance_coverage import InsuranceCoverage
from datamimic_ce.domains.insurance.services.insurance_coverage_service import InsuranceCoverageService

class TestInsuranceCoverage:
    _supported_datasets = ["US", "DE"]
    def _test_single_insurance_coverage(self, insurance_coverage: InsuranceCoverage):
        assert isinstance(insurance_coverage, InsuranceCoverage)
        assert isinstance(insurance_coverage.name, str)
        assert isinstance(insurance_coverage.code, str)
        assert isinstance(insurance_coverage.product_code, str)
        assert isinstance(insurance_coverage.description, str)
        assert isinstance(insurance_coverage.min_coverage, str)
        assert isinstance(insurance_coverage.max_coverage, str)

        assert insurance_coverage.name is not None
        assert insurance_coverage.code is not None
        assert insurance_coverage.product_code is not None
        assert insurance_coverage.description is not None
        assert insurance_coverage.min_coverage is not None
        assert insurance_coverage.max_coverage is not None

        assert insurance_coverage.name != ""
        assert insurance_coverage.code != ""
        assert insurance_coverage.product_code != ""
        assert insurance_coverage.description != ""
        assert insurance_coverage.min_coverage != ""
        assert insurance_coverage.max_coverage != ""

    def test_generate_single_insurance_coverage(self):
        insurance_coverage_service = InsuranceCoverageService()
        insurance_coverage = insurance_coverage_service.generate()
        self._test_single_insurance_coverage(insurance_coverage)

    def test_generate_multiple_insurance_coverages(self):
        insurance_coverage_service = InsuranceCoverageService()
        insurance_coverages = insurance_coverage_service.generate_batch(10)
        assert len(insurance_coverages) == 10
        for insurance_coverage in insurance_coverages:
            self._test_single_insurance_coverage(insurance_coverage)

    def test_insurance_coverage_property_cache(self):    
        insurance_coverage_service = InsuranceCoverageService()
        insurance_coverage = insurance_coverage_service.generate()
        assert insurance_coverage is not None
        assert insurance_coverage.name == insurance_coverage.name
        assert insurance_coverage.code == insurance_coverage.code
        assert insurance_coverage.product_code == insurance_coverage.product_code
        assert insurance_coverage.description == insurance_coverage.description
        assert insurance_coverage.min_coverage == insurance_coverage.min_coverage
        assert insurance_coverage.max_coverage == insurance_coverage.max_coverage

    @pytest.mark.flaky(reruns=10)
    def test_two_different_entities(self):
        insurance_coverage_service = InsuranceCoverageService()
        insurance_coverage1 = insurance_coverage_service.generate()
        insurance_coverage2 = insurance_coverage_service.generate()
        assert insurance_coverage1.name != insurance_coverage2.name 
        assert insurance_coverage1.code != insurance_coverage2.code
        assert insurance_coverage1.product_code != insurance_coverage2.product_code
        assert insurance_coverage1.description != insurance_coverage2.description
        assert insurance_coverage1.min_coverage != insurance_coverage2.min_coverage
        assert insurance_coverage1.max_coverage != insurance_coverage2.max_coverage     
        

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        insurance_coverage_service = InsuranceCoverageService(dataset=dataset)
        insurance_coverage = insurance_coverage_service.generate()
        self._test_single_insurance_coverage(insurance_coverage)

    def test_not_supported_dataset(self):
        insurance_coverage_service = InsuranceCoverageService(dataset="FR")
        coverage = insurance_coverage_service.generate()
        # Fallback to US dataset with a single warning log; should not raise
        assert isinstance(coverage.to_dict(), dict)

    def test_supported_datasets_static(self):
        codes = InsuranceCoverageService.supported_datasets()
        assert isinstance(codes, set) and len(codes) > 0
        assert "US" in codes and "DE" in codes
