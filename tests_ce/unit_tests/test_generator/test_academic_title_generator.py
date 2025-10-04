# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from numpy import nan

from datamimic_ce.domains.common.literal_generators.academic_title_generator import AcademicTitleGenerator


class TestAcademicTitleGenerator:
    _dataset = "US"

    _us_results = [
        "",
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

    _default_result = _us_results

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
        with caplog.at_level("INFO"):
            academic_title_generator = AcademicTitleGenerator(dataset="SV")
        # Expect dataset_path fallback warning
        assert "falling back to US dataset" in caplog.text
        assert academic_title_generator._quota == 0.5
        assert set(academic_title_generator._values).issubset(set(self._us_results))
        result = academic_title_generator.generate()
        assert result is not nan, "Must not be nan (panda empty value)"
        assert result in self._us_results
