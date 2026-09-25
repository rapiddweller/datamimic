# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import uuid
from random import Random

from datamimic_ce.domains.shared.literal_generators.uuid_generator import UUIDGenerator


def test_uuid_generator_replays_with_same_seed() -> None:
    assert UUIDGenerator(rng=Random(42)).generate() == UUIDGenerator(rng=Random(42)).generate()


def test_uuid_generator_changes_with_different_seed() -> None:
    assert UUIDGenerator(rng=Random(42)).generate() != UUIDGenerator(rng=Random(43)).generate()


def test_uuid_generator_emits_valid_uuid4() -> None:
    assert uuid.UUID(UUIDGenerator(rng=Random(42)).generate()).version == 4
