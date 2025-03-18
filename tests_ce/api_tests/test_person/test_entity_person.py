

from datetime import datetime
import pytest
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.common.services.person_service import PersonService


class TestEntityPerson:
    _supported_datasets = []
    def _test_single_person(self, person: Person):
        assert isinstance(person, Person)
        assert isinstance(person.gender, str)
        assert isinstance(person.given_name, str)
        assert isinstance(person.family_name, str)
        assert isinstance(person.name, str)
        assert isinstance(person.age, int)
        assert isinstance(person.email, str)
        assert isinstance(person.phone, str)
        assert isinstance(person.address, Address)
        assert isinstance(person.birthdate, datetime)
        assert isinstance(person.academic_title, str)
        assert isinstance(person.salutation, str)
        assert isinstance(person.nobility_title, str)

        assert person.gender.upper() in ["MALE", "FEMALE", "OTHER"]
        assert person.given_name is not None and person.given_name != ""
        assert person.family_name is not None and person.family_name != ""
        assert person.name is not None and person.name != ""
        assert person.age is not None and person.age != ""
        assert person.email is not None and person.email != ""
        assert person.phone is not None and person.phone != ""
        assert person.address is not None
        assert person.birthdate is not None 
        assert person.academic_title is not None and person.academic_title != ""
        assert person.salutation is not None and person.salutation != ""
        assert person.nobility_title is not None
        
    def test_generate_single_person(self):
        person_service = PersonService()
        person = person_service.generate()
        self._test_single_person(person)

    def test_generate_multiple_persons(self):
        person_service = PersonService()
        persons = person_service.generate_batch(10)
        assert len(persons) == 10
        for person in persons:
            self._test_single_person(person)

    def test_person_property_cache(self):
        person_service = PersonService()
        person = person_service.generate()
        person_data = person.person_data
        assert person_data["gender"] == person.gender
        assert person_data["given_name"] == person.given_name
        assert person_data["family_name"] == person.family_name
        assert person_data["email"] == person.email
        assert person_data["phone"] == person.phone
        assert person_data["address"] == person.address
        assert person_data["birthdate"] == person.birthdate
        assert person_data["academic_title"] == person.academic_title
        assert person_data["salutation"] == person.salutation
        assert person_data["nobility_title"] == person.nobility_title

    def test_different_entities(self):
        person_service = PersonService()
        person1 = person_service.generate()
        person2 = person_service.generate()
        assert person1.given_name != person2.given_name
        assert person1.family_name != person2.family_name
        assert person1.email != person2.email
        assert person1.phone != person2.phone
        assert person1.address != person2.address
        assert person1.birthdate != person2.birthdate
        assert person1.academic_title != person2.academic_title

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_person_generator_dataset(self, dataset):
        person_service = PersonService(dataset=dataset)
        person = person_service.generate()
        self._test_single_person(person)

    def test_not_supported_dataset(self):
        dataset = "XX"
        with pytest.raises(ValueError):
            person_service = PersonService(dataset=dataset)
