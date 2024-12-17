# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from enum import Enum


class UnsupportedMethod(Enum):
    SEED = "seed"
    SEED_INSTANCE = "seed_instance"
    SEED_LOCALE = "seed_locale"
    PROVIDER = "provider"
    GET_PROVIDERS = "get_providers"
    ADD_PROVIDER = "add_provider"
    BYTES = "bytes"
