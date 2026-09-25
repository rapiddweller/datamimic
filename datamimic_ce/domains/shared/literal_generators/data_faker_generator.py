# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from faker import Faker

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.engine.dsl.api import UnsupportedMethod


class DataFakerGenerator(BaseLiteralGenerator):
    """
    This is an implement of Python Faker
    Generate fake data, base on Faker library
    """

    def __init__(
        self,
        method: str,
        locale: str | None = "en_US",
        *args,
        rng: random.Random | None = None,
        seed: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(rng=rng)
        # validation support methods
        if method in UnsupportedMethod._value2member_map_ or method.startswith("_"):
            raise ValueError(f"Faker method '{method}' is not supported")
        self._faker = Faker(locale)
        if seed is not None:
            self._faker.seed_instance(seed)
        elif rng is not None:
            # seed_instance is Faker's official seeding API; anchor it to a token
            # drawn from the caller's rng so output replays under the shared seed.
            self._faker.seed_instance(rng.getrandbits(63))
        self._method = method
        self._locale = locale
        self._args = args
        self._kwargs = kwargs

    def generate(self) -> object:
        try:
            formatter = self._faker.get_formatter(self._method)
        except AttributeError as exc:
            raise ValueError(f"Wrong Faker method: {self._method} does not exist") from exc
        if not callable(formatter):
            raise ValueError(f"Wrong Faker method: {self._method} does not exist")
        return formatter(*self._args, **self._kwargs)
