# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The stable product identity emitted by CE capture exporters."""

from .constants.convention_constants import NAME_SEPARATOR


def capture_product_name(full_name: str) -> str:
    return full_name.split(NAME_SEPARATOR, 1)[-1].strip() if NAME_SEPARATOR in full_name else full_name
