"""The bounded XML limit is a structured application result in both editions."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.requests import BuildRequestV4, CompileDocumentRequest, RunRequest
from datamimic_ce.interfaces.cli.authoring import app


def oversized_document() -> DmJsonDocumentV1:
    return DmJsonDocumentV1.model_validate(
        {
            "root": {
                "kind": "setup",
                "properties": {"rng_seed": 7},
                "children": [
                    {
                        "kind": "generate",
                        "properties": {"name": "rows", "count": 1},
                        "children": [
                            {
                                "kind": "key",
                                "properties": {"name": "text", "constant": "x" * 1_000_000},
                            }
                        ],
                    }
                ],
            },
        }
    )


def application(root: Path):
    return create_authoring_application(workspace_root=root)


def test_build_rejects_oversized_compiler_output_without_echoing_the_document(tmp_path: Path) -> None:
    authoring = application(tmp_path)
    document = oversized_document()
    compiled = authoring.compile_document(CompileDocumentRequest(document=document))
    assert compiled.outcome == "ready"
    result = authoring.build(BuildRequestV4(document=document))
    assert result.outcome == "rejected"
    assert result.phase.value == "policy"
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "limit"
    assert diagnostic.path == ("xml",)
    assert diagnostic.expected == 1_000_000
    assert diagnostic.actual == len(compiled.artifact.compiled_xml)
    assert diagnostic.remediation
    assert "x" * 200 not in result.model_dump_json()


@pytest.mark.parametrize("dry", [True, False])
def test_raw_xml_limit_is_a_structured_failure(tmp_path: Path, dry: bool) -> None:
    authoring = application(tmp_path)
    compiled = authoring.compile_document(CompileDocumentRequest(document=oversized_document()))
    assert compiled.outcome == "ready"
    request = RunRequest(xml=compiled.artifact.compiled_xml)
    result = authoring.dry_run(request) if dry else authoring.run(request)
    assert not result.ok
    assert result.diagnostics[0].code == "limit"
    assert result.diagnostics[0].path == ("xml",)
    assert "x" * 200 not in result.model_dump_json()


def test_cli_build_returns_rejected_json_for_oversized_xml(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    payload = {"document": oversized_document().model_dump(mode="json")}
    result = CliRunner().invoke(app, ["build", "-"], input=json.dumps(payload))
    assert result.exit_code == 1
    rejection = json.loads(result.stdout)
    assert rejection["outcome"] == "rejected"
    assert rejection["diagnostics"][0]["code"] == "limit"
    assert "x" * 200 not in result.stdout
