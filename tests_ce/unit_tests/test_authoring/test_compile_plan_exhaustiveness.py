"""Fail-closed dispatch contracts for compiler-owned acceptance facts."""

import pytest

from datamimic_ce.authoring.contracts import (
    ExactCountAcceptancePlan,
    FieldIntentKind,
    GeneratedProductCompilePlan,
    LeafFieldPlan,
    _validate_acceptance_facts,
)


class FutureExactCountAcceptancePlan(ExactCountAcceptancePlan):
    """Represents a future exact-type addition missing from the validator registry."""


def test_acceptance_fact_dispatch_fails_when_exact_type_has_no_validator() -> None:
    field = LeafFieldPlan(name="id", kind=FieldIntentKind.INCREMENT)
    product = GeneratedProductCompilePlan(name="items", fields=[field], static_count=1)
    acceptance = FutureExactCountAcceptancePlan(product="items", exact_count=1)

    with pytest.raises(TypeError, match="no acceptance validator registered for FutureExactCountAcceptancePlan"):
        _validate_acceptance_facts(
            [acceptance],  # type: ignore[list-item] - deliberately outside the registered union
            {"items": product},
            {"items": {"id": field}},
            set(),
        )
