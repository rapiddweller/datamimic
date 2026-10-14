import json
import os
from pathlib import Path

import pytest

from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator
from datamimic_ce.engine.dsl.api import GenerateStatement
from datamimic_ce.engine.runtime.api import run
from datamimic_ce.engine.runtime.contracts import RunRequest


def test_root_sibling_and_nested_includes_share_ids_and_preserve_child_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(PatientGenerator, "generate_patient_id_candidate", lambda self: "PAT-00000000")
    generate = (
        '<generate name="patients" count="1"><variable name="patient" entity="Patient" rngSeed="23"/>'
        '<key name="patient_id" script="patient.patient_id"/>'
        '<key name="cached_id" script="patient.patient_id"/>'
        '<generate name="links" count="2"><key name="patient_id" script="parent.patient_id"/></generate>'
        '</generate>'
    )
    (tmp_path / "part.xml").write_text(f"<setup>{generate}</setup>", encoding="utf-8")
    (tmp_path / "nested.xml").write_text(
        '<setup><include uri="part.xml"/><include uri="part.xml"/></setup>', encoding="utf-8"
    )
    descriptor = tmp_path / "main.xml"
    descriptor.write_text(
        f'<setup rngSeed="17">{generate}<include uri="part.xml"/><include uri="part.xml"/>'
        f'<include uri="nested.xml"/>{generate}</setup>',
        encoding="utf-8",
    )
    request = RunRequest(descriptor_path=descriptor, test_mode=True)

    first = run(request).captured
    second = run(request).captured

    expected = [f"PAT-{index:08X}" for index in range(6)]
    assert [row["patient_id"] for row in first["patients"]] == expected
    assert [row["cached_id"] for row in first["patients"]] == expected
    assert [row["patient_id"] for row in first["links"]] == [value for value in expected for _ in range(2)]
    assert second == first  # A separate run resets allocation and replays the same seed.


@pytest.mark.parametrize("workers", [1, 2])
@pytest.mark.parametrize("dynamic", [False, True])
def test_per_parent_include_ids_use_one_native_process_and_shared_allocation(
    tmp_path: Path, workers: int, dynamic: bool
) -> None:
    # Reconstructing the same seeded service in each include forces the same first candidate.
    trace = tmp_path / "trace.jsonl"
    (tmp_path / "helpers.py").write_text(
        "def record(identifier, parent_id, path):\n"
        "    import json, os\n"
        "    with open(path, 'a', encoding='utf-8') as stream:\n"
        "        row = {'patient_id': identifier, 'parent_id': parent_id, 'pid': os.getpid()}\n"
        "        stream.write(json.dumps(row) + '\\n')\n"
        "    return identifier\n",
        encoding="utf-8",
    )
    (tmp_path / "part.xml").write_text(
        '<setup><generate name="patients" count="1"><variable name="patient" entity="Patient" rngSeed="23"/>'
        '<key name="patient_id" script="record(patient.patient_id, parent_id, trace_path)"/></generate></setup>',
        encoding="utf-8",
    )
    uri = "{include_path}" if dynamic else "part.xml"
    descriptor = tmp_path / "main.xml"
    descriptor.write_text(
        f'<setup multiprocessing="True" numProcess="{workers}"><execute type="python" uri="helpers.py"/>'
        f'<generate name="parents" count="4" pageSize="1" numProcess="{workers}">'
        '<key name="include_path" constant="part.xml"/>'
        '<key name="parent_id" type="int" generator="IncrementGenerator"/>'
        f'<include uri="{uri}"/><key name="pid" type="int" script="os.getpid()"/></generate></setup>',
        encoding="utf-8",
    )

    planned = []
    result = run(RunRequest(
        descriptor_path=descriptor,
        platform_props={"trace_path": str(trace)},
        test_mode=True,
        statement_transformer=lambda setup: planned.extend(
            stmt for stmt in setup.sub_statements if isinstance(stmt, GenerateStatement)
        ),
    ))
    events = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]

    assert len(result.captured["parents"]) == len(events) == 4
    assert len(planned) == 1 and planned[0].num_process == 1
    assert {row["pid"] for row in result.captured["parents"]} == {os.getpid()}
    assert {event["pid"] for event in events} == {os.getpid()}
    assert [event["parent_id"] for event in events] == [row["parent_id"] for row in result.captured["parents"]]
    assert [event["parent_id"] for event in events] == [1, 2, 3, 4]
    assert [event["patient_id"] for event in events] == [
        "PAT-B468E07E", "PAT-B468E07F", "PAT-B468E080", "PAT-B468E081"
    ]
