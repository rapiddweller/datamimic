# generate cities

from datamimic_ce.domains.common.generators.city_generator import CityGenerator


def generate_cities():
    city_generator = CityGenerator()
    cities = city_generator.generate_batch(10)
    for city in cities:
        print(city.to_dict())

if __name__ == "__main__":
    generate_cities()
