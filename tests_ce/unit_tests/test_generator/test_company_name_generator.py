# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from datamimic_ce.generators.company_name_generator import CompanyNameGenerator


def test_company_name_generator():
    for _ in range(10):
        company_name = CompanyNameGenerator().generate()
        assert isinstance(company_name, str)
