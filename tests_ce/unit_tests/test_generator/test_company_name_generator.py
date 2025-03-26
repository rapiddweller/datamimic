# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator


def test_company_name_generator():
    for _ in range(10):
        company_name = CompanyNameGenerator().generate()
        assert isinstance(company_name, str)
