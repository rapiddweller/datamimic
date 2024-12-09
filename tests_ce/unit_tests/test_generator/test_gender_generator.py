# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from datamimic_ce.generators.gender_generator import GenderGenerator


class TestGenderGenerator:
    def test_generate_with_female_quota(self):
        # Test cases for female_quota (0.5, 0.2, 1)
        female_quota_cases = [0.5, 0.2, 1]
        deviation = 0.02  # Assumption: deviation is 2% from target value

        for index, female_quota in enumerate(female_quota_cases):
            generator = GenderGenerator(female_quota=female_quota)
            count = sum(generator.generate() == "female" for _ in range(100_000))
            assert self.__is_between_target_fluctuation(
                count / 100_000, female_quota, deviation
            ), f"Test {index + 1} failed"

            # print(count / 100_000)

    def test_generate_other_quota(self):
        # Test cases for other_quota (0.5, 0.2, 1)
        other_quota_cases = [0.5, 0.2, 1]
        deviation = 0.02  # Assumption: deviation is 2% from target value

        for index, other_quota in enumerate(other_quota_cases):
            generator = GenderGenerator(other_gender_quota=other_quota)
            count = sum(generator.generate() == "other" for _ in range(100_000))
            assert self.__is_between_target_fluctuation(
                count / 100_000, other_quota, deviation
            ), f"Test {index + 1} failed"

    def test_generate_with_female_quota_and_other_quota(self):
        female_quota_cases = [0.5, 0.2, 1]
        other_quota_cases = [0.5, 0.2, 1]
        deviation = 0.02  # Assumption: deviation is 2% from target value
        times = 100_000

        for f_index, female_quota in enumerate(female_quota_cases):
            for o_index, other_quota in enumerate(other_quota_cases):
                generator = GenderGenerator(female_quota=female_quota, other_gender_quota=other_quota)
                count_female = 0
                count_male = 0
                count_other = 0
                for _ in range(times):
                    gender = generator.generate()
                    if gender == "female":
                        count_female += 1
                    elif gender == "male":
                        count_male += 1
                    elif gender == "other":
                        count_other += 1

                assert self.__is_between_target_fluctuation(
                    count_female / times, female_quota, deviation), f"Test female quota {f_index+1}-{o_index + 1} failed"

                other_true_quota = other_quota if (female_quota + other_quota <= 1) else (1 - female_quota)
                assert self.__is_between_target_fluctuation(
                    count_other / times, other_true_quota, deviation), f"Test other gender quota {f_index + 1}-{o_index + 1} failed"

                male_quota = 1 - female_quota - other_true_quota
                assert self.__is_between_target_fluctuation(
                    count_male / times, male_quota, deviation), f"Test male quota {f_index + 1}-{o_index + 1} failed"

    @staticmethod
    def __is_between_target_fluctuation(value: float, target: float, deviation: float) -> bool:
        below_target = max(target - deviation, 0)
        above_target = min(target + deviation, 1)
        if target == 0 or target == 1:
            below_target = above_target = target
        return below_target <= value <= above_target
