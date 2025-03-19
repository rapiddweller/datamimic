from datamimic_ce.domains.common.services.country_service import CountryService


def generate_countries():
    country_service = CountryService()
    countries = country_service.generate_batch(10)
    for country in countries:
        print(country.to_dict())


if __name__ == "__main__":
    generate_countries()
