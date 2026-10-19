"""Reviewed Python uses normal execution; bounded rejection remains evidence."""

import json
import os
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.requests import BuildRequestV4, CompileDocumentRequest, DecompileDocumentRequest

# Count module loading without making the tested selection function stateful.
_HELPER = """from pathlib import Path
with Path("loads.txt").open("a", encoding="utf-8") as stream:
    stream.write("load\\n")

def select_person(candidates: list[tuple[int, bool]]) -> int:
    for person_id, eligible in candidates:
        if eligible:
            return person_id
    raise ValueError("No eligible candidate")
"""


@pytest.mark.parametrize("mode", ["uri", "inline"])
@pytest.mark.parametrize("has_candidate", [True, False], ids=["eligible", "no_candidate"])
def test_reviewed_python_keeps_bounded_rejection_and_actual_runtime_evidence(tmp_path, mode, has_candidate):
    script = tmp_path / "script/select.py"
    script.parent.mkdir()
    script.write_text(_HELPER, encoding="utf-8")
    execute = (
        '<execute type="python" uri="script/select.py"/>'
        if mode == "uri"
        else f'<execute type="python">{escape(_HELPER)}</execute>'
    )
    candidates = "[(1, False), (2, True)]" if has_candidate else "[(1, False), (2, False)]"
    application = create_authoring_application(tmp_path)
    decoded = application.decompile_document(
        DecompileDocumentRequest(
            xml=f'<setup rngSeed="17">{execute}'
            '<generate name="selected" count="1" target="JSON" exportUri="selection">'
            f'<key name="person_id" type="int" script="select_person({candidates})"/>'
            "</generate></setup>"
        )
    )
    assert decoded.outcome == "ready", decoded
    compiled = application.compile_document(CompileDocumentRequest(document=decoded.document))
    assert compiled.outcome == "ready", compiled
    restored = application.decompile_document(DecompileDocumentRequest(xml=compiled.artifact.compiled_xml))
    assert restored.outcome == "ready" and restored.document == compiled.artifact.document
    bounded = application.build(BuildRequestV4(document=restored.document))
    assert bounded.outcome == "rejected", bounded
    assert any(item.code is AuthoringRuleId.UNSUPPORTED_BOUNDED_OPERATION for item in bounded.diagnostics)
    assert not (tmp_path / "loads.txt").exists()

    (tmp_path / "model.xml").write_text(compiled.artifact.compiled_xml, encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    for run in range(2):
        result = subprocess.run(
            [sys.executable, "-m", "datamimic_ce.interfaces.cli", "run", "model.xml"],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        assert result.returncode == (0 if has_candidate else 1), result.stdout + result.stderr
        assert (tmp_path / "loads.txt").read_text(encoding="utf-8").splitlines() == ["load"] * (run + 1)
        outputs = list((tmp_path / "output/selection").glob("*.json"))
        if has_candidate:
            assert len(outputs) == run + 1
            assert all(json.loads(path.read_text(encoding="utf-8")) == [{"person_id": 2}] for path in outputs)
        else:
            assert outputs == []
