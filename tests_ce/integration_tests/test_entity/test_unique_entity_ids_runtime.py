from __future__ import annotations

from pathlib import Path
from random import Random

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator


class _CollidingRandom(Random):
    def choice(self, seq):
        return seq[0]


def _run_entity_descriptor(tmp_path: Path, *, multiprocess: bool) -> list[dict[str, object]]:
    setup = '<setup multiprocessing="True" numProcess="2">' if multiprocess else '<setup multiprocessing="0">'
    descriptor = tmp_path / "patient_ids.xml"
    descriptor.write_text(
        f"""{setup}
  <generate name="patients" count="4" pageSize="2" target="">
    <variable name="patient" entity="Patient" rngSeed="23"/>
    <key name="patient_id" script="patient.patient_id"/>
  </generate>
</setup>
""",
        encoding="utf-8",
    )
    engine = DataMimicTest(test_dir=tmp_path, filename=descriptor.name, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["patients"]


@pytest.mark.parametrize("multiprocess", [False, True])
def test_entity_ids_stay_unique_across_pages_and_worker_topologies(
    tmp_path: Path, multiprocess: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_init = PatientGenerator.__init__

    def colliding_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._rng = _CollidingRandom()

    monkeypatch.setattr(PatientGenerator, "__init__", colliding_init)
    first = _run_entity_descriptor(tmp_path, multiprocess=multiprocess)
    second = _run_entity_descriptor(tmp_path, multiprocess=multiprocess)
    identifiers = [row["patient_id"] for row in first]

    assert identifiers == ["PAT-00000000", "PAT-00000001", "PAT-00000002", "PAT-00000003"]
    assert second == first
