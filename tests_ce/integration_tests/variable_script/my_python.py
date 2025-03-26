# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


def random_age(min, max):
    # IMPORTANT: always put "import" in function scope (not global) to avoid pickle issue
    import random

    return random.randint(min, max)
