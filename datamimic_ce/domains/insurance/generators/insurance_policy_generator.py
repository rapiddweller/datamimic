from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator
from datamimic_ce.domains.insurance.generators.insurance_company_generator import InsuranceCompanyGenerator
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator


class InsurancePolicyGenerator(BaseDomainGenerator):
    """Generator for insurance policy data."""

    def __init__(self, dataset: str | None = None):
        """Initialize the insurance policy generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"
        self._insurance_company_generator = InsuranceCompanyGenerator(dataset=dataset)
        self._insurance_product_generator = InsuranceProductGenerator(dataset=dataset)
        self._insurance_coverage_generator = InsuranceCoverageGenerator(dataset=dataset)
        self._person_generator = PersonGenerator(dataset=dataset)
        self._datetime_generator = DateTimeGenerator(random=True)

    @property
    def insurance_company_generator(self) -> InsuranceCompanyGenerator:
        return self._insurance_company_generator

    @property
    def insurance_product_generator(self) -> InsuranceProductGenerator:
        return self._insurance_product_generator

    @property
    def insurance_coverage_generator(self) -> InsuranceCoverageGenerator:
        return self._insurance_coverage_generator

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def datetime_generator(self) -> DateTimeGenerator:
        return self._datetime_generator
