# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



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
