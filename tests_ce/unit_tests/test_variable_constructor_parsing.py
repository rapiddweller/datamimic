from __future__ import annotations

from pathlib import Path
from random import Random

import pytest

from datamimic_ce.domains.api import IdentifierRegistry
from datamimic_ce.domains.finance.services.bank_account_service import BankAccountService
from datamimic_ce.domains.healthcare.services.patient_service import PatientService
from datamimic_ce.domains.shared.demographics.config import DemographicConfig
from datamimic_ce.domains.shared.services.person_service import PersonService
from datamimic_ce.engine.dsl.api import Statement
from datamimic_ce.engine.dsl.model.values.variables.variable_model import VariableModel
from datamimic_ce.engine.dsl.statements.values.variables.variable_statement import VariableStatement
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.tasks.values.construction.entity import create_entity_generator
from datamimic_ce.engine.runtime.tasks.values.construction.entity_constructor import parse_constructor_string


def test_constructor_arguments_keep_literal_types_and_string_fallback():
    assert parse_constructor_string("Person(code='0012', count=3, mode=fast)") == (
        "Person",
        {"code": "0012", "count": 3, "mode": "fast"},
    )


def _context() -> SetupContext:
    return SetupContext(
        memstore_manager=None,
        task_id="constructor-test",
        test_mode=True,
        test_result_exporter=None,
        default_separator=",",
        default_locale="en_US",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=None,
        default_variable_prefix="",
        default_variable_suffix="",
        default_line_separator=None,
    )


def _statement(**overrides: object) -> VariableStatement:
    values = {
        "name": "entity",
        "entity": "Person",
        "ageMin": None,
        "ageMax": None,
        "conditionsInclude": None,
        "conditionsExclude": None,
        "rngSeed": None,
    }
    values.update(overrides)
    return VariableStatement(VariableModel(**values), Statement(None, None))


@pytest.mark.parametrize(
    ("entity", "service_type"),
    (("Person", PersonService), ("Patient", PatientService), ("BankAccount", BankAccountService)),
)
def test_dynamic_entity_constructor_resolves_builtin_service(entity: str, service_type: type[object]) -> None:
    service = create_entity_generator(_context(), entity, "US", _statement())

    assert isinstance(service, service_type)


def test_dynamic_entity_constructor_preserves_explicit_invalid_kwargs() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument 'invalid'"):
        create_entity_generator(_context(), "Person(invalid=1)", "US", _statement())


def test_dynamic_entity_constructor_injects_only_signature_supported_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    received: dict[str, object] = {}

    class DatasetOnlyService:
        def __init__(self, dataset: str | None = None) -> None:
            received["dataset"] = dataset

        def set_identifier_registry(self, registry: IdentifierRegistry) -> None:  # noqa: ARG002
            return None

    from datamimic_ce import domains

    monkeypatch.setattr(domains.api, "get_entity_service_factory", lambda _: DatasetOnlyService)
    service = create_entity_generator(
        _context(),
        "DatasetOnly",
        "US",
        _statement(ageMin=30, ageMax=35, conditionsInclude="I10", rngSeed=7),
    )

    assert isinstance(service, DatasetOnlyService)
    assert received == {"dataset": "US"}


def test_dynamic_entity_constructor_injects_supported_rng_and_demographics(monkeypatch: pytest.MonkeyPatch) -> None:
    received: dict[str, object] = {}

    class OverrideAwareService:
        def __init__(self, dataset: str | None, demographic_config: object, rng: object) -> None:
            received.update(dataset=dataset, demographic_config=demographic_config, rng=rng)

        def set_identifier_registry(self, registry: IdentifierRegistry) -> None:  # noqa: ARG002
            return None

    from datamimic_ce import domains

    monkeypatch.setattr(domains.api, "get_entity_service_factory", lambda _: OverrideAwareService)
    service = create_entity_generator(
        _context(),
        "OverrideAware",
        "US",
        _statement(ageMin=30, ageMax=35, conditionsInclude="I10", conditionsExclude="E11", rngSeed=7),
    )

    assert isinstance(service, OverrideAwareService)
    assert received["dataset"] == "US"
    config = received["demographic_config"]
    assert isinstance(config, DemographicConfig)
    assert config.age_min == 30
    assert config.age_max == 35
    assert config.normalized_includes() == frozenset({"I10"})
    assert config.normalized_excludes() == frozenset({"E11"})
    rng = received["rng"]
    assert isinstance(rng, Random)
    assert rng.randint(0, 100) == 41
