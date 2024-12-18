# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class StringGenerator:
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
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
        self._class_factory_util = class_factory_util.get_data_generation_util()

    def generate(self) -> str:
        # Handle mode random
        return self._class_factory_util.rnd_str(
            char_set=self._char_set,
            min_val=self._min_len,
            max_val=self._max_len,
            unique=self.unique,
            prefix=self.prefix,
            suffix=self.suffix,
        )
