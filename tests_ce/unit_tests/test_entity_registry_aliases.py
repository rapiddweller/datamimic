from types import SimpleNamespace

import pytest

from datamimic_ce.domains.common.services.person_service import PersonService
from datamimic_ce.domains.domain_core.entity_registry import get_entity_service_class
from datamimic_ce.engine.runtime.tasks.variable_task import VariableTask


def test_dotted_service_alias_resolves_through_entity_registry():
    alias = "common.services.person_service.PersonService"
    assert get_entity_service_class(alias) is PersonService


def test_unregistered_dotted_alias_is_rejected():
    assert get_entity_service_class("unrelated.module.PersonService") is None


def test_unknown_dotted_entity_is_rejected():
    context = SimpleNamespace(root=SimpleNamespace(demographic_context=None, derive_seeded_rng=lambda: None))
    statement = SimpleNamespace(
        age_min=None,
        age_max=None,
        conditions_include=None,
        conditions_exclude=None,
        rng_seed=None,
    )

    with pytest.raises(ValueError, match="not supported in the domain architecture"):
        VariableTask._get_entity_generator(context, "common.models.UnknownEntity", "en", "US", 1, statement)
