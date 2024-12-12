# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.generators.boolean_generator import BooleanGenerator


class TestBooleanGenerator:
    def test_default_probability(self):
        boolean_generator = BooleanGenerator()
        true_count = sum(boolean_generator.generate() for _ in range(10000))
        false_count = 10000 - true_count

        assert abs(true_count - false_count) < 500

    def test_custom_probability_true(self):
        prob_true = 0.7
        boolean_generator = BooleanGenerator(prob_true=prob_true)
        assert boolean_generator.prob_true == 0.7

        true_count = sum(boolean_generator.generate() for _ in range(10000))

        assert prob_true + 0.05 >= true_count / 10000 >= prob_true - 0.05

    def test_custom_probability_false(self):
        prob_true = 0.3
        prob_false = 1 - prob_true
        boolean_generator = BooleanGenerator(prob_true=prob_true)
        assert boolean_generator.prob_true == 0.3

        false_count = sum(not boolean_generator.generate() for _ in range(10000))

        assert prob_false + 0.05 >= false_count / 10000 >= prob_false - 0.05

    def test_invalid_probability_smaller_than_zero(self):
        prob_true = -1
        try:
            BooleanGenerator(prob_true=prob_true)
            assert False
        except ValueError as error:
            assert (
                f"Probability prob_true of BooleanGenerator must be in [0.0, 1.0] range, "
                f"but got invalid value {prob_true}."
            ) == str(error)

    def test_invalid_probability_larger_than_one(self):
        prob_true = 2
        try:
            BooleanGenerator(prob_true=prob_true)
            assert False
        except ValueError as error:
            assert (
                f"Probability prob_true of BooleanGenerator must be in [0.0, 1.0] range, "
                f"but got invalid value {prob_true}."
            ) == str(error)

    def test_probability_edge_cases(self):
        generator_false = BooleanGenerator(prob_true=0.0)
        generator_true = BooleanGenerator(prob_true=1.0)

        assert generator_false.generate() is False
        assert generator_true.generate() is True
