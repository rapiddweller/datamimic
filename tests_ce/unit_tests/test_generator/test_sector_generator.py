# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.generators.sector_generator import SectorGenerator


def test_sector_generator_support_locale():
    support_locales = {"en", "de"}
    for support_locale in support_locales:
        sector = SectorGenerator(locale=support_locale).generate()
        assert isinstance(sector, str)


def test_sector_generator_unsupport_locale():
    unsupport_locale = "az"
    sector = SectorGenerator(locale=unsupport_locale).generate()
    assert isinstance(sector, str)
