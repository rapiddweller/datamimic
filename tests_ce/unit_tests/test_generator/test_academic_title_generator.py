# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from numpy import nan

from datamimic_ce.generators.academic_title_generator import AcademicTitleGenerator


class TestAcademicTitleGenerator:
    _dataset = "US"

    _us_results = ['',
                   "Bachelor",
                   "Master",
                   "PhD",
                   "Asst. Prof.",
                   "Assoc. Prof.",
                   "Postdoc",
                   "Prof.",
                   "Distinguished Prof.",
                   "Endowed Prof.",
                   "Emeritus Prof.",
                   ]

    _default_result = ['',
                       "Bachelor",
                       "Master",
                       "PhD",
                       "Assistant Prof.",
                       "Associate Prof.",
                       "Prof.",
                       ]

    def test_academic_title(self):
        for _ in range(100):
            academic_title_generator = AcademicTitleGenerator(dataset=self._dataset)
            result = academic_title_generator.generate()
            assert result is not nan, "Must not be nan (panda empty value)"
            assert result in self._us_results

    def test_init_default(self):
        for _ in range(100):
            academic_title_generator = AcademicTitleGenerator()
            assert academic_title_generator._quota == 0.5
            assert set(academic_title_generator._values).issubset(set(self._default_result))
            result = academic_title_generator.generate()
            assert result is not nan, "Must not be nan (panda empty value)"
            assert result in self._default_result

    def test_specify_quota(self):
        generator = AcademicTitleGenerator(quota=0.7)
        assert generator._quota == 0.7

    def test_invalid_quota(self):
        generator_1 = AcademicTitleGenerator(quota=2)
        assert generator_1._quota == 0.5
        generator_2 = AcademicTitleGenerator(quota=-2)
        assert generator_2._quota == 0.5
        generator_3 = AcademicTitleGenerator(quota=None)
        assert generator_3._quota == 0.5

    def test_invalid_dataset(self, caplog):
        with caplog.at_level('INFO'):
            academic_title_generator = AcademicTitleGenerator(dataset="SV")
        assert "Academic title for dataset SV is not supported, change to default Academic title" in caplog.text
        assert academic_title_generator._quota == 0.5
        assert set(academic_title_generator._values).issubset(set(self._default_result))
        result = academic_title_generator.generate()
        assert result is not nan, "Must not be nan (panda empty value)"
        assert result in self._default_result
