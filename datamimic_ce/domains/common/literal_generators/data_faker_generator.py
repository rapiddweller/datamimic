# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from typing import Any, Protocol, cast

from faker import Faker

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.enums.faker_enums import UnsupportedMethod


class _SupportsRandom(Protocol):
    random: random.Random


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
        **kwargs,
    ) -> None:
        # validation support methods
        if method in UnsupportedMethod._value2member_map_ or method.startswith("_"):
            raise ValueError(f"Faker method '{method}' is not supported")
        self._faker = Faker(locale)
        if rng is not None:
            # faker.Faker exposes a dynamic `random` attribute; cast to a protocol so mypy accepts the assignment.
            faker_with_random = cast(_SupportsRandom, self._faker)
            faker_with_random.random = rng
        self._method = method
        self._locale = locale
        self._args = args
        self._kwargs = kwargs

    def generate(self) -> Any:
        # check worked methods
        faker_method = getattr(self._faker, self._method, "method does not exist")
        if faker_method == "method does not exist" or not callable(faker_method):
            raise ValueError(f"Wrong Faker method: {self._method} does not exist")
        # generate data
        if self._args and self._kwargs:
            result = faker_method(*self._args, **self._kwargs)
        elif self._args:
            result = faker_method(*self._args)
        elif self._kwargs:
            result = faker_method(**self._kwargs)
        else:
            result = faker_method()
        return result
