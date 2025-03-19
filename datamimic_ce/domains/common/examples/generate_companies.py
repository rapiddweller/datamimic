from datamimic_ce.domains.common.services.company_service import CompanyService


def generate_companies():
    company_service = CompanyService()
    companies = company_service.generate_batch(10)
    for company in companies:
        print(company.to_dict())


if __name__ == "__main__":
    generate_companies()
