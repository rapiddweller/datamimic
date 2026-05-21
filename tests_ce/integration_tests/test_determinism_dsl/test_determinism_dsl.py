# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DSL-expressed determinism contract.

The seeded-replay contract is described as a readable DATAMIMIC DSL model
(``all_entities_seeded.xml``): every registered domain entity is generated
with an ``rngSeed`` and a handful of scalar fields. Running the same model
twice must yield byte-identical output per ``<generate>`` block.

This replaces the Python service-replay gate with a model a reviewer can read
top-to-bottom. The XML doubles as living documentation of which entities the
DSL can drive by name.
"""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDeterminismDsl:
    _test_dir = Path(__file__).resolve().parent

    def _run(self, filename: str) -> dict:
        engine = DataMimicTest(test_dir=self._test_dir, filename=filename, capture_test_result=True)
        engine.test_with_timer()
        return engine.capture_result()

    def test_all_entities_replay_identically(self) -> None:
        first = self._run("all_entities_seeded.xml")
        second = self._run("all_entities_seeded.xml")

        assert first.keys() == second.keys(), "Same model must produce the same generate blocks"
        assert first, "Expected the model to produce at least one entity block"
        for block, rows in first.items():
            assert rows, f"Block '{block}' produced no rows"
            assert rows == second[block], f"Seeded block '{block}' must replay identically"
