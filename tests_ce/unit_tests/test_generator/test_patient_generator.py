# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.

from __future__ import annotations

import random
from collections import Counter

from datamimic_ce.domains.healthcare.generators import patient_generator
from datamimic_ce.domains.healthcare.generators.patient_generator import (
    PatientGenerator
)

class TestPatientGeneratorEmergencyContact:
    def setup_method(self) -> None:
        PatientGenerator._emergency_relationship_cache.clear()

    def test_emergency_relationships_respect_csv_weights(self, tmp_path, monkeypatch):
        dataset = "US"
        # Intercept emergency relationships file load and provide controlled weights
        from datamimic_ce.utils import file_util as _fu
        orig_read = _fu.FileUtil.read_wgt_file

        def _fake_read_wgt_file(file_path, delimiter=",", encoding="utf-8"):
            from pathlib import Path as _P
            name = _P(file_path).name
            if name == f"emergency_relationships_{dataset}.csv":
                # Parent:Friend = 3:1 → 0.75/0.25
                return ["Parent", "Friend"], [0.75, 0.25]
            return orig_read(file_path, delimiter=delimiter, encoding=encoding)

        monkeypatch.setattr(_fu.FileUtil, "read_wgt_file", staticmethod(_fake_read_wgt_file))

        generator = PatientGenerator(dataset=dataset, rng=random.Random(12345))
        monkeypatch.setattr(generator._given_name_generator, "generate", lambda: "Given")
        monkeypatch.setattr(generator._family_name_generator, "generate", lambda: "Family")
        monkeypatch.setattr(generator._phone_number_generator, "generate", lambda: "555-0100")

        relationships = [
            generator.get_emergency_contact("Doe")["relationship"]
            for _ in range(200)
        ]

        counts = Counter(relationships)
        total = counts["Parent"] + counts["Friend"]
        parent_ratio = counts["Parent"] / total

        assert counts.keys() <= {"Parent", "Friend"}
        assert 0.7 <= parent_ratio <= 0.85
