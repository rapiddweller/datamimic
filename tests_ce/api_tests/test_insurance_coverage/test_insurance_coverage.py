import hashlib
import random

import pytest

from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
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

    def test_seeded_coverage_record_shape_and_sequence(self) -> None:
        rng = random.Random(20260930)
        generator = InsuranceCoverageGenerator(dataset="US", rng=rng)

        coverages = [generator.get_random_coverage() for _ in range(5)]

        assert list(coverages[0]) == [
            "name",
            "code",
            "product_code",
            "description",
            "min_coverage",
            "max_coverage",
        ]
        assert coverages[0]["min_coverage"] == "10000"
        assert coverages[0]["max_coverage"] == "200000"
        assert [coverage["code"] for coverage in coverages] == ["ADDL", "VARL", "UMOT", "MEDR", "UNIV"]
        assert all(isinstance(value, str) for coverage in coverages for value in coverage.values())
        assert hashlib.sha256(repr(rng.getstate()).encode()).hexdigest() == (
            "95cb6fb046e68136fea188d9363f79490997254967448c48609642335c7045fb"
        )

    def test_cached_coverage_data_and_to_dict_do_not_draw_again(self) -> None:
        rng = random.Random(75)
        coverage = InsuranceCoverage(InsuranceCoverageGenerator(dataset="US", rng=rng))

        data = coverage.coverage_data
        state_after_generation = rng.getstate()
        first_dict = coverage.to_dict()
        second_dict = coverage.to_dict()

        assert coverage.coverage_data is data
        assert first_dict == second_dict == data
        assert first_dict is not second_dict
        assert rng.getstate() == state_after_generation

    def test_dataset_extra_columns_are_not_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        row = {
            "name": "Test",
            "code": "TEST",
            "product_code": "TEST",
            "description": "Test coverage",
            "min_coverage": "00100",
            "max_coverage": "01000",
            "weight": "1.0",
            "source_note": "ignored",
        }
        monkeypatch.setattr(
            "datamimic_ce.domains.insurance.generators.insurance_coverage_generator.read_weighted_records",
            lambda *_args: ([1.0], [row]),
        )
        generator = InsuranceCoverageGenerator(dataset="US", rng=random.Random(1))

        coverage = generator.get_random_coverage()

        assert list(coverage) == [
            "name",
            "code",
            "product_code",
            "description",
            "min_coverage",
            "max_coverage",
        ]
        assert coverage["min_coverage"] == "00100"
        assert coverage["max_coverage"] == "01000"

    @pytest.mark.parametrize(
        "missing_field",
        ["name", "code", "product_code", "description", "min_coverage", "max_coverage"],
    )
    def test_missing_required_dataset_field_raises_key_error(
        self, monkeypatch: pytest.MonkeyPatch, missing_field: str
    ) -> None:
        row = {
            "name": "Test",
            "code": "TEST",
            "product_code": "TEST",
            "description": "Test coverage",
            "min_coverage": "00100",
            "max_coverage": "01000",
        }
        row.pop(missing_field)
        monkeypatch.setattr(
            "datamimic_ce.domains.insurance.generators.insurance_coverage_generator.read_weighted_records",
            lambda *_args: ([1.0], [row]),
        )
        generator = InsuranceCoverageGenerator(dataset="US", rng=random.Random(1))

        with pytest.raises(KeyError, match=missing_field):
            generator.get_random_coverage()

    @pytest.mark.parametrize(
        ("weights", "rows", "error"),
        [([], [], IndexError), ([0.0], [{"name": "Test"}], ValueError)],
    )
    def test_empty_or_all_zero_weight_rows_keep_existing_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        weights: list[float],
        rows: list[dict[str, str]],
        error: type[Exception],
    ) -> None:
        monkeypatch.setattr(
            "datamimic_ce.domains.insurance.generators.insurance_coverage_generator.read_weighted_records",
            lambda *_args: (weights, rows),
        )
        generator = InsuranceCoverageGenerator(dataset="US", rng=random.Random(1))

        with pytest.raises(error):
            generator.get_random_coverage()
