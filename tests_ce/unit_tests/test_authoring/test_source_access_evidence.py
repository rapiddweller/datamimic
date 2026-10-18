"""Build assurance reports actual IO requests, without source locations."""

from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import (
    BuildRequestV4,
    DecompileDocumentRequest,
    ReadyBuild,
    ReferenceRequest,
    ReferenceTopic,
)


def test_file_access_is_produced_by_real_bounded_run_and_does_not_leak_between_builds(tmp_path: Path) -> None:
    (tmp_path / "private-source.csv").write_text("id|label\n1|one\n2|two\n3|three\n")
    application = create_authoring_application(workspace_root=tmp_path)
    decompiled = application.decompile_document(
        DecompileDocumentRequest(
            xml='<setup rngSeed="7"><generate name="rows" source="private-source.csv" distribution="ordered">'
            '<key name="id" script="int(this.id)"/></generate></setup>'
        )
    )
    assert decompiled.outcome == "ready"
    result = application.build(BuildRequestV4(document=decompiled.document))
    assert isinstance(result, ReadyBuild), result
    assert result.evidence[0].count == 3
    assert [item.model_dump() for item in result.assurance.source_accesses] == [
        {"source_type": "file_csv", "requests": 1}
    ]
    starter = application.reference(ReferenceRequest(topic=ReferenceTopic.ASSEMBLY, name="starter")).entries[0]
    next_result = application.build(starter.starter)
    assert isinstance(next_result, ReadyBuild), next_result
    assert next_result.assurance.source_accesses == ()


def test_memstore_readback_reports_one_runtime_request(tmp_path: Path) -> None:
    application = create_authoring_application(workspace_root=tmp_path)
    example = application.reference(ReferenceRequest(topic=ReferenceTopic.EXAMPLES, name="memstore")).entries[0]
    result = application.build(example.request)
    assert isinstance(result, ReadyBuild), result
    assert [item.model_dump() for item in result.assurance.source_accesses] == [
        {"source_type": "memstore", "requests": 1}
    ]


def test_source_observation_scope_restores_nested_and_failed_reads(tmp_path: Path) -> None:
    import pytest

    from datamimic_ce.engine.io.api import GenerateFileSourceRequest, SourceAccessCapture, read_generate_file_source

    (tmp_path / "source.csv").write_text("id\n1\n")
    request = GenerateFileSourceRequest("source.csv", tmp_path, "rows", "|", False, None, None, 0, "rows")
    with SourceAccessCapture() as outer:
        read_generate_file_source(request)
        with SourceAccessCapture() as inner:
            read_generate_file_source(request)
            read_generate_file_source(request)
        read_generate_file_source(request)
    assert outer.snapshot() == (("file_csv", 2),)
    assert inner.snapshot() == (("file_csv", 2),)
    read_generate_file_source(request)
    assert outer.snapshot() == (("file_csv", 2),)
    with pytest.raises(FileNotFoundError), SourceAccessCapture() as failed:
        read_generate_file_source(
            GenerateFileSourceRequest("missing.csv", tmp_path, "rows", "|", False, None, None, 0, "rows")
        )
    assert failed.snapshot() == (("file_csv", 1),)
    with SourceAccessCapture() as clean:
        read_generate_file_source(request)
    assert clean.snapshot() == (("file_csv", 1),)
