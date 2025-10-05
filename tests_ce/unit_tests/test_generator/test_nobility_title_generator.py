# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.

from __future__ import annotations

from random import Random

from datamimic_ce.domains.common.literal_generators.nobility_title_generator import NobilityTitleGenerator


def test_other_gender_returns_string_when_quota_hits() -> None:
    generator = NobilityTitleGenerator(dataset="US", noble_quota=1.0, rng=Random(1337))
    # WHY: Ensure non-binary genders still receive a string title when quota triggers.
    title = generator.generate_with_gender("other")

    assert isinstance(title, str)
    assert title != ""
