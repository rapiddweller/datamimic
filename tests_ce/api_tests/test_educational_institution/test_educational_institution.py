import pytest

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution
from datamimic_ce.domains.public_sector.services.educational_institution_service import EducationalInstitutionService


class TestEntityEducationalInstitution:
    _supported_datasets = ["US", "DE"]

    def _test_single_educational_institution(self, educational_institution: EducationalInstitution):
        assert isinstance(educational_institution, EducationalInstitution)
        assert isinstance(educational_institution.institution_id, str)
        assert isinstance(educational_institution.type, str)
        assert isinstance(educational_institution.level, str)
        assert isinstance(educational_institution.founding_year, int)
        assert isinstance(educational_institution.student_count, int)
        assert isinstance(educational_institution.staff_count, int)
        assert isinstance(educational_institution.website, str)
        assert isinstance(educational_institution.email, str)
        assert isinstance(educational_institution.phone, str)
        assert isinstance(educational_institution.address, Address)
        assert isinstance(educational_institution.programs, list)
        assert isinstance(educational_institution.accreditations, list)
        assert isinstance(educational_institution.facilities, list)
        assert educational_institution.address is not None and educational_institution.address != ""
        assert educational_institution.institution_id is not None and educational_institution.institution_id != ""
        assert educational_institution.type is not None and educational_institution.type != ""
        assert educational_institution.level is not None and educational_institution.level != ""
        assert educational_institution.founding_year is not None and educational_institution.founding_year != ""
        assert educational_institution.student_count is not None and educational_institution.student_count != ""
        assert educational_institution.staff_count is not None and educational_institution.staff_count != ""
        assert educational_institution.website is not None and educational_institution.website != ""
        assert educational_institution.email is not None and educational_institution.email != ""
        assert educational_institution.phone is not None and educational_institution.phone != ""
        assert educational_institution.address is not None and educational_institution.address != ""
        assert educational_institution.programs is not None and educational_institution.programs != ""
        assert educational_institution.accreditations is not None and educational_institution.accreditations != ""
        assert educational_institution.facilities is not None and educational_institution.facilities != ""

    def test_generate_single_educational_institution(self):
        educational_institution_service = EducationalInstitutionService()
        educational_institution = educational_institution_service.generate()
        self._test_single_educational_institution(educational_institution)

    def test_generate_multiple_educational_institutions(self):
        educational_institution_service = EducationalInstitutionService()
        educational_institutions = educational_institution_service.generate_batch(10)
        assert len(educational_institutions) == 10
        for educational_institution in educational_institutions:
            self._test_single_educational_institution(educational_institution)

    def test_educational_institution_property_cache(self):
        educational_institution_service = EducationalInstitutionService()
        educational_institution = educational_institution_service.generate()
        assert educational_institution.institution_id == educational_institution.institution_id
        assert educational_institution.name == educational_institution.name
        assert educational_institution.type == educational_institution.type
        assert educational_institution.level == educational_institution.level
        assert educational_institution.founding_year == educational_institution.founding_year
        assert educational_institution.student_count == educational_institution.student_count
        assert educational_institution.staff_count == educational_institution.staff_count
        assert educational_institution.website == educational_institution.website
        assert educational_institution.email == educational_institution.email
        assert educational_institution.phone == educational_institution.phone
        assert educational_institution.address == educational_institution.address
        assert educational_institution.programs == educational_institution.programs
        assert educational_institution.accreditations == educational_institution.accreditations
        assert educational_institution.facilities == educational_institution.facilities

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        educational_institution_service = EducationalInstitutionService()
        educational_institution1 = educational_institution_service.generate()
        educational_institution2 = educational_institution_service.generate()
        assert educational_institution1.institution_id != educational_institution2.institution_id
        assert educational_institution1.name != educational_institution2.name
        assert educational_institution1.type != educational_institution2.type
        assert educational_institution1.level != educational_institution2.level
        assert educational_institution1.founding_year != educational_institution2.founding_year
        assert educational_institution1.student_count != educational_institution2.student_count
        assert educational_institution1.staff_count != educational_institution2.staff_count
        assert educational_institution1.website != educational_institution2.website
        assert educational_institution1.email != educational_institution2.email
        assert educational_institution1.phone != educational_institution2.phone
        assert educational_institution1.address != educational_institution2.address
        assert educational_institution1.programs != educational_institution2.programs
        assert educational_institution1.accreditations != educational_institution2.accreditations
        assert educational_institution1.facilities != educational_institution2.facilities

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_educational_institution_dataset(self, dataset):
        educational_institution_service = EducationalInstitutionService(dataset=dataset)
        educational_institution = educational_institution_service.generate()
        self._test_single_educational_institution(educational_institution)

    def test_not_supported_dataset(self):
        # Fallback to US dataset with a single warning log; should not raise
        educational_institution_service = EducationalInstitutionService(dataset="XX")
        educational_institution = educational_institution_service.generate()
        assert isinstance(educational_institution.to_dict(), dict)

    def test_supported_datasets_static(self):
        codes = EducationalInstitutionService.supported_datasets()
        assert isinstance(codes, set) and len(codes) > 0
        assert "US" in codes and "DE" in codes
