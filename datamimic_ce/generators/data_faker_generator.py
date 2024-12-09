# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from typing import Any

from faker import Faker

from datamimic_ce.enums.faker_enums import UnsupportedMethod
from datamimic_ce.generators.generator import Generator


class DataFakerGenerator(Generator):
    """
    This is an implement of Python Faker
    Generate fake data, base on Faker library
    """

    def __init__(
        self,
        method: str,
        locale: str | None = "en_US",
        *args,
        **kwargs,
    ) -> None:
        # validation support methods
        if method in UnsupportedMethod._value2member_map_ or method.startswith("_"):
            raise ValueError(f"Faker method '{method}' is not supported")
        self._faker = Faker(locale)
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
