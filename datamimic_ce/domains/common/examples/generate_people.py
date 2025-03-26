from datamimic_ce.domains.common.services.person_service import PersonService


def generate_people(count: int = 10):
    person_service = PersonService()
    people = person_service.generate_batch(count)
    for person in people:
        print(person.to_dict())


if __name__ == "__main__":
    generate_people(10)
