# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domains.common.literal_generators.department_name_generator import DepartmentNameGenerator


def test_department_name_generator_support_locale():
    support_locales = ("en", "de")
    for support_locale in support_locales:
        department = DepartmentNameGenerator(locale=support_locale).generate()
        assert isinstance(department, str)


def test_department_name_generator_unsupported_locale_falls_back_to_en():
    department = DepartmentNameGenerator(locale="fr").generate()
    assert department in DepartmentNameGenerator(locale="en")._department_data
