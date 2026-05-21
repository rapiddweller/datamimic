# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datetime import datetime, timedelta
from random import Random

from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import ClockAnchoredDomainGenerator


class BirthdateGenerator(ClockAnchoredDomainGenerator):
    """
    Purpose: generate a random birthdate between min_age and max_age.

    Use case (config):
        - Generate random birthdate (default age = 1 - 100).
        Example: birthdate_generator = BirthdateGenerator()
        - Generate specified birthdate with age (set: min = max = age).
        Example: birthdate_generator = BirthdateGenerator(20, 20)
        - Generate birthdate from min and max age.
        Example: birthdate_generator = BirthdateGenerator(20, 60)

    Attributes:
        min_age (int): minimum age value (inclusively).
        max_age (int): maximum age value (inclusively).
    """

    def __init__(
        self,
        min_age: int = 1,
        max_age: int = 100,
        rng: Random | None = None,
        reference_now: datetime | None = None,
    ) -> None:
        """
        Parameters:
            min_age (int): minimum age value (inclusively).
            max_age (int): maximum age value (inclusively).
            rng: Optional seeded random instance for deterministic output.
            reference_now: Optional fixed datetime to use as "today". Defaults to the
                resolved clock — the deterministic anchor when seeded, else live UTC.

        Throws:
            ValueError: if min_age is higher than max_age
        """
        super().__init__(rng=rng, reference_now=reference_now)
        if min_age > max_age:
            raise ValueError("max_age must higher than or equals min_age")
        today = self._reference_now
        # if today is 29-02 of leap year, to avoid error, change it to 28-02
        if today.month == 2 and today.day == 29:
            today = datetime(today.year, 2, 28)
        self._min_birthdate = datetime(today.year - max_age - 1, today.month, today.day) + timedelta(days=1)
        self._max_birthdate = datetime(today.year - min_age, today.month, today.day)
        # Derive a dedicated RNG for date sampling so seeded runs stay reproducible without cross-coupling streams.
        date_rng = self._derive_rng()
        self._date_generator = DateTimeGenerator(
            min=str(self._min_birthdate),
            max=str(self._max_birthdate),
            random=True,
            rng=date_rng,
        )

    def generate(self) -> datetime:
        """
        generate random birthday between min and max age (calculated from today)

        Returns:
            datetime: generated date
        """
        result = self._date_generator.generate()
        if not isinstance(result, datetime):
            raise ValueError("BirthdateGenerator must return a datetime object")
        return result

    def reset(self) -> None:
        pass

    def convert_birthdate_to_age(self, birth_date: datetime, reference_now: datetime | None = None) -> int:
        """
        age are calculated from given birthday and today
        (today value depends on system time and change over time, not fixed).

        Args:
            birth_date: The birthdate to calculate age from.
            reference_now: Optional fixed datetime to use as "today". Defaults to the generator anchor.

        Returns:
            age (int): calculated age (hour, minute, second, microsecond in datetime object equal 0 as default)
        """
        today = reference_now if reference_now is not None else self._reference_now
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
