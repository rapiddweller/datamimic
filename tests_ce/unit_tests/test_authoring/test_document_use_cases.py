"""Public phases and hashes prove compilation, never execution."""

from hashlib import sha256
from pathlib import PurePosixPath

from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.application.schema import contract_schemas
from datamimic_ce.authoring.application.use_cases import CompileDocumentUseCase, DecompileDocumentUseCase
from datamimic_ce.authoring.domain.diagnostics import AuthoringCodecDiagnosticCode, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, DmJsonNodeV1
from datamimic_ce.authoring.domain.requests import CompileDocumentRequest, DecompileDocumentRequest

_DESCRIPTOR_PATH = PurePosixPath("model.xml")


def validator(tmp_path, path=_DESCRIPTOR_PATH):
    return CeDescriptorValidator(AuthoringWorkspaceContext(tmp_path, path), profile_loader=lambda *_: {})


def test_compile_decompile_hashes_preserve_canonical_semantics(tmp_path):
    codec = CeDmJsonCodec()
    check = validator(tmp_path)
    xml = '<setup rngSeed="7"><generate name="rows" count="2"><key name="id" constant="1"/></generate></setup>'
    compiled = CompileDocumentUseCase(codec, check).execute(CompileDocumentRequest(document=codec.decompile(xml)))
    assert compiled.outcome == "ready"
    artifact = compiled.artifact
    assert artifact.xml_sha256 == sha256(artifact.compiled_xml.encode()).hexdigest()
    assert artifact.ce_version
    restored = DecompileDocumentUseCase(codec, check).execute(DecompileDocumentRequest(xml=xml))
    assert restored.outcome == "ready"
    assert restored.document == artifact.document
    assert restored.semantic_sha256 == artifact.semantic_sha256
    assert restored.canonical_xml_sha256 == artifact.xml_sha256
    assert restored.source_xml_sha256 != restored.canonical_xml_sha256
    assert list(tmp_path.iterdir()) == []


def test_compile_codec_failure_and_parser_failure_have_distinct_phases(tmp_path):
    usecase = CompileDocumentUseCase(CeDmJsonCodec(), validator(tmp_path))
    unknown = DmJsonDocumentV1(root=DmJsonNodeV1(kind="setup", children=(DmJsonNodeV1(kind="unknown"),)))
    rejected = usecase.execute(CompileDocumentRequest(document=unknown))
    assert rejected.phase == DiagnosticPhase.COMPILE
    assert rejected.diagnostics[0].code == AuthoringCodecDiagnosticCode.COMPILE_INVALID
    assert rejected.diagnostics[0].path == ("root", "children", 0, "kind")
    missing = CeDmJsonCodec().decompile('<setup><generate count="2"/></setup>')
    invalid = usecase.execute(CompileDocumentRequest(document=missing))
    assert invalid.phase == DiagnosticPhase.XML
    assert any(item.ce_error is not None for item in invalid.diagnostics)


def test_decompile_rejects_parser_valid_unrepresentable_comments(tmp_path):
    result = DecompileDocumentUseCase(CeDmJsonCodec(), validator(tmp_path)).execute(
        DecompileDocumentRequest(xml='<setup><!--a--><!--b--><generate name="rows" count="2"/></setup>')
    )
    assert result.outcome == "rejected"
    assert result.phase == DiagnosticPhase.DECOMPILE
    assert result.diagnostics[0].code == AuthoringCodecDiagnosticCode.DECOMPILE_UNSUPPORTED
    assert result.diagnostics[0].remediation


def test_compile_passes_bound_logical_descriptor_path(tmp_path):
    path = PurePosixPath("nested/input.xml")
    usecase = CompileDocumentUseCase(CeDmJsonCodec(), validator(tmp_path, path))
    document = CeDmJsonCodec().decompile("<setup/>")
    assert usecase.execute(CompileDocumentRequest(document=document, descriptor_path=path)).outcome == "ready"
    assert usecase.execute(CompileDocumentRequest(document=document)).phase == DiagnosticPhase.XML


def test_all_document_schemas_use_closed_live_variants():
    schemas = contract_schemas(CeDmJsonCodec())
    projected = (
        schemas.dm_json_document_v1,
        schemas.dm_json_node_v1,
        schemas.compile_document_request,
        schemas.compile_document_result,
        schemas.decompile_document_result,
    )
    for schema in projected:
        variants = schema["$defs"]["DmJsonNodeV1"]
        assert variants["discriminator"]["propertyName"] == "kind"
        assert "setup" in variants["discriminator"]["mapping"]
        assert "kafka" not in variants["discriminator"]["mapping"]
        assert "root" not in schema.get("required", []) or schema["properties"]["root"]["$ref"].endswith("_SETUP")
    # A Build proves project files, so neither its request nor its results carry a DM JSON document.
    for schema in (schemas.build_request_v5, schemas.ready_build, schemas.rejected_build, schemas.build_result):
        assert "DmJsonNodeV1" not in schema.get("$defs", {})


def test_public_compile_and_build_property_diagnostics_omit_input_values(tmp_path):
    from datamimic_ce.authoring import create_authoring_application
    from tests_ce.authoring_project import build_project

    application = create_authoring_application(workspace_root=tmp_path)
    secret = "SENSITIVE_SENTINEL=/private/host/credential"
    document = DmJsonDocumentV1(root=DmJsonNodeV1(kind="setup", properties={"num_process": secret}))
    compiled = application.compile_document(CompileDocumentRequest(document=document))
    assert compiled.outcome == "rejected"
    assert compiled.phase is DiagnosticPhase.COMPILE
    diagnostic = compiled.diagnostics[0]
    assert diagnostic.path == ("root", "properties", "num_process")
    assert diagnostic.expected["validation_error_types"]
    # Build reads the persisted entry, so the same value is refused by the XML parser instead of the codec.
    built = build_project(tmp_path, f'<setup numProcess="{secret}"/>')
    assert built.outcome == "rejected"
    assert built.phase is DiagnosticPhase.XML
    # The named rule comes first; the parser refusal still names the attribute.
    [parser] = [item for item in built.diagnostics if item.ce_error is not None]
    assert parser.path == ("descriptor", "datamimic.xml", "setup", "numProcess")
    for result, finding in ((compiled, diagnostic), (built, parser)):
        assert secret not in result.model_dump_json()
        assert "input_value" not in result.model_dump_json()
        assert finding.actual is None
        assert finding.remediation
