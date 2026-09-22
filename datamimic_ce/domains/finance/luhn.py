# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


def luhn_check_digit(payload: str) -> str:
    """Return the Luhn (ISO/IEC 7812-1, mod 10) check digit for ``payload``.

    Single source of truth for card check-digit generation: ``payload + check``
    passes Luhn validation. Doubling starts at the rightmost payload digit, since
    once the check digit is appended that digit sits at the second-from-right
    position (the first doubled position).
    """
    total = 0
    for i, ch in enumerate(reversed(payload)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - (total % 10)) % 10)
