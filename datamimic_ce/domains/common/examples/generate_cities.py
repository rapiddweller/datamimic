# generate cities

from datamimic_ce.domains.common.services.city_service import CityService


def generate_cities():
    city_service = CityService()
    cities = city_service.generate_batch(10)
    for city in cities:
        print(city.to_dict())


if __name__ == "__main__":
    generate_cities()
