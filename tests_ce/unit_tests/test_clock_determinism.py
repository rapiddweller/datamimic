# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Clock-anchoring contract for generators with date/time outputs.

The end-to-end byte-stability of these generators is already covered by
``tests_ce/architecture/test_service_replay_determinism.py``. This file
keeps one focused unit test per generator that explicitly asserts
``reference_now`` is the only knob controlling time-derived output —
useful for fast feedback when working on a specific generator.
"""

from __future__ import annotations

import random
from datetime import datetime

import pytest

from datamimic_ce.domains.common.literal_generators.birthdate_generator import BirthdateGenerator
from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator

SEED = 20260520
FIXED_NOW = datetime(2025, 6, 15, 12, 0, 0)
LATER_NOW = datetime(2030, 6, 15, 12, 0, 0)


@pytest.mark.parametrize(
    "generator_cls, method",
    [
        (BankAccountGenerator, "generate_created_date"),
        (TransactionGenerator, "generate_transaction_date"),
        (OrderGenerator, "generate_order_date"),
        (MedicalDeviceGenerator, "generate_manufacture_date"),
        (BirthdateGenerator, "generate"),
    ],
    ids=lambda x: x.__name__ if isinstance(x, type) else x,
)
def test_reference_now_is_the_only_time_knob(generator_cls: type, method: str) -> None:
    """Same seed + same reference_now → identical date.
    Same seed + different reference_now → diverges.
    """
    a = generator_cls(rng=random.Random(SEED), reference_now=FIXED_NOW)
    b = generator_cls(rng=random.Random(SEED), reference_now=FIXED_NOW)
    c = generator_cls(rng=random.Random(SEED), reference_now=LATER_NOW)

    assert getattr(a, method)() == getattr(b, method)()
    assert getattr(a, method)() != getattr(c, method)()
