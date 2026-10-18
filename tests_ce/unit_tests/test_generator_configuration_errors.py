"""Deliberate generator policy failures retain safe owner facts."""

import pickle

import pytest

from datamimic_ce.errors import ErrorCode, GeneratorConfigError, IssueCode, generator_config_error


def test_constructor_reason_has_generator_identity_without_invented_element():
    error = generator_config_error(reason="BinaryGenerator lengths must be >= 0")
    assert type(error) is GeneratorConfigError
    assert error.code is ErrorCode.GENERATOR_CONFIG
    assert error.issue_code is None
    assert error.constructor_reason == "BinaryGenerator lengths must be >= 0"
    assert str(error) == "[E009] Invalid generator configuration: BinaryGenerator lengths must be >= 0."
    restored = pickle.loads(pickle.dumps(error))
    assert type(restored) is GeneratorConfigError
    assert restored.__dict__ == error.__dict__
    assert str(restored) == str(error)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"reason": ""},
        {"reason": "   "},
        {"reason": "safe", "extra": "invalid"},
        {"reason": "safe", "guidance": "invalid"},
        {"code": IssueCode.GENERATOR_CREATE_FAILED, "reason": "invalid"},
    ],
)
def test_constructor_reason_does_not_relax_catalog_parameter_validation(kwargs):
    with pytest.raises(ValueError):
        generator_config_error(**kwargs)


def test_catalog_constructor_fields_remain_required():
    with pytest.raises(ValueError, match="missing="):
        generator_config_error(code=IssueCode.GENERATOR_CREATE_FAILED, class_name="BinaryGenerator")


@pytest.mark.parametrize("reason", [42, "", "   ", "CONTRADICTORY_CONSTRUCTOR_REASON"])
def test_catalog_error_rejects_forged_constructor_reason_on_wire(reason):
    from datamimic_ce.authoring.adapters import dryrun

    error = generator_config_error(
        code=IssueCode.GENERATOR_CREATE_FAILED,
        class_name="BinaryGenerator",
        element_name="payload",
        descriptor="",
        error="TypeError",
    )
    error.constructor_reason = reason
    payload = pickle.dumps(dryrun._WorkerFailure(message="failure", fix_hint="repair", error=error))
    with pytest.raises(ValueError):
        dryrun._decode_worker_message(payload)


@pytest.mark.parametrize("reason", [42, "", "   "])
def test_constructor_error_rejects_invalid_reason_on_wire(reason):
    from datamimic_ce.authoring.adapters import dryrun

    error = generator_config_error(reason="safe constructor reason")
    error.constructor_reason = reason
    payload = pickle.dumps(dryrun._WorkerFailure(message="failure", fix_hint="repair", error=error))
    with pytest.raises(ValueError):
        dryrun._decode_worker_message(payload)


def test_constructor_error_rejects_wrong_identity_on_wire():
    from datamimic_ce.authoring.adapters import dryrun

    error = generator_config_error(reason="safe constructor reason")
    error.code = ErrorCode.TASK_CONFIG
    payload = pickle.dumps(dryrun._WorkerFailure(message="failure", fix_hint="repair", error=error))
    with pytest.raises(ValueError):
        dryrun._decode_worker_message(payload)


def test_datetime_weight_expression_preserves_seeded_entropy_policy(tmp_path):
    from datamimic_ce.engine.runtime.api import run
    from datamimic_ce.engine.runtime.contracts import RunRequest
    from datamimic_ce.errors import TaskConfigError

    path = tmp_path / "model.xml"
    path.write_text(
        '<setup rngSeed="7"><generate name="rows" count="1">'
        '<key name="value" generator="{declaration}"/></generate></setup>'
    )
    with pytest.raises(TaskConfigError, match="'os.urandom' draws entropy") as caught:
        run(
            RunRequest(
                descriptor_path=path,
                platform_props={"declaration": "DateTimeGenerator(hour_weights='[os.urandom(1)[0]] * 24')"},
                test_mode=True,
            )
        )
    assert caught.value.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert caught.value.__cause__ is None


def test_datetime_weight_native_failure_keeps_private_cause_and_safe_label(tmp_path):
    from datamimic_ce.engine.runtime.api import run
    from datamimic_ce.engine.runtime.contracts import RunRequest
    from datamimic_ce.errors import TaskConfigError

    sentinel = "AUDIT_DATETIME_PRIVATE_REASON_c13a"
    path = tmp_path / "model.xml"
    path.write_text(
        '<setup><generate name="rows" count="1"><key name="value" generator="{declaration}"/></generate></setup>'
    )
    declaration = f"""DateTimeGenerator(hour_weights="[int('{sentinel}')] * 24")"""
    with pytest.raises(TaskConfigError) as caught:
        run(RunRequest(descriptor_path=path, platform_props={"declaration": declaration}, test_mode=True))
    assert caught.value.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert "DateTimeGenerator.hour_weights" in str(caught.value)
    assert sentinel not in str(caught.value)
    assert type(caught.value.__cause__) is ValueError
    assert sentinel in str(caught.value.__cause__)


@pytest.mark.parametrize("descriptor_name", [None, "actual.xml"])
@pytest.mark.parametrize("cause", ["boom.", "upstream descriptor 'source' failed."])
def test_generator_create_factory_owns_descriptor_and_preserves_cause(descriptor_name, cause):
    from datamimic_ce.errors import IssueCode, generator_config_error
    from datamimic_ce.errors.context.descriptor_identity import descriptor_scope

    with descriptor_scope(None):
        error = generator_config_error(
            code=IssueCode.GENERATOR_CREATE_FAILED,
            descriptor_name=descriptor_name,
            class_name="DateTimeGenerator",
            element_name="created",
            descriptor=" in descriptor 'legacy.xml'",
            error=cause,
        )
    assert str(error) == (
        "[E009/I436] Invalid generator configuration: Cannot create generator 'DateTimeGenerator'"
        f" for element 'created' in descriptor '{descriptor_name or 'legacy.xml'}': {cause}"
    )
