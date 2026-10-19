from pathlib import PurePosixPath


def test_public_validator_retains_raw_rule_advisories_without_workspace_writes(tmp_path):
    from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext

    workspace = AuthoringWorkspaceContext(tmp_path, PurePosixPath("draft.xml"))
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        '<setup><generate name="rows" count="2"><key name="id" constant="1"/></generate></setup>'
    )
    assert result.ok
    assert any(item.code == "DM303" and item.severity != "error" for item in result.diagnostics)
    assert all(item.path[:2] == ("descriptor", "draft.xml") for item in result.diagnostics)
    assert list(tmp_path.iterdir()) == []


def test_raw_rule_projection_never_echoes_secret_attribute_values(tmp_path):
    from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext

    workspace = AuthoringWorkspaceContext(tmp_path)
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        '<setup><generate name="rows" count="2" password="private-token"><key name="id" constant="1"/></generate></setup>'
    )
    assert not result.ok
    assert "private-token" not in result.model_dump_json()
    assert str(tmp_path) not in result.model_dump_json()


def test_internal_credential_classification_uses_typed_fields_only() -> None:
    from datamimic_ce.authoring.adapters.engine_check import _is_pure_credential_error
    from datamimic_ce.errors import ParserValidationError

    error = ParserValidationError(
        "private-token: make sure all required attributes are provided - host: Field required"
    )
    assert not _is_pure_credential_error(error)
    error.validation_errors = ({"loc": ("host",), "type": "missing", "msg": "anything"},)
    assert _is_pure_credential_error(error)
    error.validation_errors += ({"loc": ("dbms",), "type": "missing", "msg": "anything"},)
    assert not _is_pure_credential_error(error)
    error.validation_errors = ({"loc": ("password",), "type": "string_type", "msg": "anything"},)
    assert not _is_pure_credential_error(error)
    assert not _is_pure_credential_error(ValueError("- host: Field required"))
