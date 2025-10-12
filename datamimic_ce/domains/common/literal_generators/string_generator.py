# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import re
import string

import exrex  # type: ignore

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator


class StringGenerator(BaseLiteralGenerator):
    def __init__(
        self,
        min_len: int | None = None,
        max_len: int | None = None,
        char_set: str | None = None,
        unique: bool = False,
        prefix: str | None = None,
        suffix: str | None = None,
    ):
        self._char_set = (
            char_set
            if char_set and len(char_set) > 0
            else "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        )
        self.unique = unique
        self.prefix = prefix or ""
        self.suffix = suffix or ""
        # Set default values for min_len and max_len if not provided
        if min_len is None and max_len is None:
            self._min_len = 1
            self._max_len = 10
        elif min_len is None and max_len is not None:
            self._min_len = max_len // 2  # min_len is half of max_len if not provided
            self._max_len = max_len
        elif max_len is None and min_len is not None:
            self._max_len = min_len * 2  # max_len is twice the min_len if not provided
            self._min_len = min_len
        else:
            self._min_len = min_len if min_len is not None else 1
            self._max_len = max_len if max_len is not None else 10

        # Ensure min_len <= max_len
        if self._min_len > self._max_len:
            raise ValueError(
                f"Failed when init StringGenerator because min_len({self._min_len}) > max_len({self._max_len})"
            )

        # Validate unique constraint
        if self.unique and len(self._char_set) < self._max_len:
            raise ValueError(
                f"Cannot generate unique string with length {self._max_len} "
                f"from character set of size {len(self._char_set)}"
            )
        self._rng: random.Random = random.Random()

    def generate(self) -> str:
        try:
            # regex
            if any(c in self._char_set for c in ".^$*+?{}[]|()"):
                compiled_regex = re.compile(self._char_set)
                char_set_list = list(set(compiled_regex.findall(string.printable)))
            else:
                # simple character
                char_set_list = list(set(self._char_set))
        except re.error:
            char_set_list = list(set(self._char_set))

        # If unique, ensure each character only appears once
        if self.unique:
            length = self._rng.randint(self._min_len, self._max_len)
            if len(char_set_list) < length:
                raise ValueError("Character set is too small to generate a unique string of this length.")
            result = self._rng.sample(char_set_list, length)  # random.sample ensures uniqueness
        else:
            length = self._rng.randint(self._min_len, self._max_len)
            result = [self._rng.choice(char_set_list) for _ in range(length)]

        return self.prefix + "".join(result) + self.suffix

    @staticmethod
    def rnd_str_from_regex(pattern: str) -> str:
        pattern = r"" + pattern
        result = exrex.getone(pattern, 1)
        if result is None:
            raise ValueError(f"Cannot generate string from regex pattern: {pattern}")
        return result
