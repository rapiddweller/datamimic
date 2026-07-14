# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Unit tests for the declarative constraint vocabulary and executor.

Tests cover:
- Constraint semantics (presence/absence, truthiness gates, lint_only skipping)
- Executor behavior per constraint kind
- Message preservation and defaults
- Callable values resolution
- JSON schema injection via constraints_schema_extra
"""

import pytest
from pydantic import BaseModel, ConfigDict

from datamimic_ce.model.constraints import (
    AllOrNone,
    AllowedValuesWhen,
    Forbids,
    ForbidsWhenValue,
    MutuallyExclusive,
    MutuallyExclusiveWhen,
    RequiredOneOf,
    Requires,
    RequiresWhenValue,
    ValidValues,
    constraints_schema_extra,
)
from datamimic_ce.model.model_util import ModelUtil


class TestRequiredOneOf:
    """RequiredOneOf constraint: at least one of the attrs must be present."""

    def test_present_single_attr_succeeds(self):
        """When one attr is present, check succeeds."""
        fact = RequiredOneOf(attrs=frozenset({"a", "b", "c"}))
        result = ModelUtil.check_constraints({"a": "val"}, (fact,))
        assert result == {"a": "val"}

    def test_present_multiple_attrs_succeeds(self):
        """When multiple attrs are present, check succeeds."""
        fact = RequiredOneOf(attrs=frozenset({"a", "b", "c"}))
        result = ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))
        assert result == {"a": "val", "b": "val2"}

    def test_no_attrs_present_fails(self):
        """When no attrs are present, check fails."""
        fact = RequiredOneOf(attrs=frozenset({"a", "b", "c"}))
        with pytest.raises(ValueError, match="must define one of"):
            ModelUtil.check_constraints({}, (fact,))

    def test_custom_message_used(self):
        """When message is set, it overrides the default."""
        fact = RequiredOneOf(attrs=frozenset({"a", "b"}), message="custom error")
        with pytest.raises(ValueError, match="custom error"):
            ModelUtil.check_constraints({}, (fact,))

    def test_default_message_sorts_attrs(self):
        """Default message sorts attrs for deterministic output."""
        fact = RequiredOneOf(attrs=frozenset({"c", "a", "b"}))
        with pytest.raises(ValueError, match="a, b, c"):
            ModelUtil.check_constraints({}, (fact,))

    def test_lint_only_skipped(self):
        """When lint_only=True, constraint is skipped."""
        fact = RequiredOneOf(attrs=frozenset({"a", "b"}), lint_only=True)
        # Would fail if not skipped, but doesn't because it's lint_only
        result = ModelUtil.check_constraints({}, (fact,))
        assert result == {}


class TestMutuallyExclusive:
    """MutuallyExclusive constraint: at most one of the attrs may be present."""

    def test_no_attrs_present_succeeds(self):
        """When no attrs are present, check succeeds."""
        fact = MutuallyExclusive(attrs=frozenset({"a", "b", "c"}))
        result = ModelUtil.check_constraints({}, (fact,))
        assert result == {}

    def test_single_attr_present_succeeds(self):
        """When exactly one attr is present, check succeeds."""
        fact = MutuallyExclusive(attrs=frozenset({"a", "b", "c"}))
        result = ModelUtil.check_constraints({"a": "val"}, (fact,))
        assert result == {"a": "val"}

    def test_two_attrs_present_fails(self):
        """When two or more attrs are present, check fails."""
        fact = MutuallyExclusive(attrs=frozenset({"a", "b", "c"}))
        with pytest.raises(ValueError, match="at most one"):
            ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))

    def test_custom_message_used(self):
        """When message is set, it overrides the default."""
        fact = MutuallyExclusive(attrs=frozenset({"a", "b"}), message="pick one only")
        with pytest.raises(ValueError, match="pick one only"):
            ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))

    def test_lint_only_skipped(self):
        """When lint_only=True, constraint is skipped."""
        fact = MutuallyExclusive(attrs=frozenset({"a", "b"}), lint_only=True)
        # Would fail if not skipped
        result = ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))
        assert result == {"a": "val", "b": "val2"}


class TestModeGatedConstraints:
    def test_mutually_exclusive_when_only_applies_with_gate(self):
        fact = MutuallyExclusiveWhen("source", frozenset(("type", "selector")))
        assert ModelUtil.check_constraints({"type": "x", "selector": "y"}, (fact,))
        with pytest.raises(ValueError, match="at most one"):
            ModelUtil.check_constraints({"source": "s", "type": "x", "selector": "y"}, (fact,))

    def test_requires_when_value_honors_unless(self):
        fact = RequiresWhenValue(
            "type",
            frozenset(("list",)),
            frozenset(("count",)),
            unless=frozenset(("source",)),
        )
        with pytest.raises(ValueError, match="at least one"):
            ModelUtil.check_constraints({"type": "list"}, (fact,))
        assert ModelUtil.check_constraints({"type": "list", "source": "rows.csv"}, (fact,))

    def test_forbids_when_value_only_applies_to_selected_mode(self):
        fact = ForbidsWhenValue("type", frozenset(("literal",)), frozenset(("count", "script")))
        assert ModelUtil.check_constraints({"type": "string", "count": "2"}, (fact,))
        with pytest.raises(ValueError, match="none of"):
            ModelUtil.check_constraints({"type": "literal", "count": "2"}, (fact,))


class TestRequires:
    """Requires constraint: if attr is present, at least one of needs must be present."""

    def test_attr_absent_succeeds(self):
        """When gating attr is absent, check succeeds regardless of needs."""
        fact = Requires(attr="a", needs=frozenset({"b", "c"}))
        result = ModelUtil.check_constraints({}, (fact,))
        assert result == {}

    def test_attr_present_needs_present_succeeds(self):
        """When gating attr and at least one need are present, check succeeds."""
        fact = Requires(attr="a", needs=frozenset({"b", "c"}))
        result = ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))
        assert result == {"a": "val", "b": "val2"}

    def test_attr_present_needs_absent_fails(self):
        """When gating attr is present but no needs are present, check fails."""
        fact = Requires(attr="a", needs=frozenset({"b", "c"}))
        with pytest.raises(ValueError, match="at least one of"):
            ModelUtil.check_constraints({"a": "val"}, (fact,))

    def test_when_true_false_presence_gate(self):
        """when_true=False gates on presence only (default)."""
        fact = Requires(attr="a", needs=frozenset({"b"}), when_true=False)
        # a="false" is present, so gate is true -> check needs
        with pytest.raises(ValueError, match="at least one of"):
            ModelUtil.check_constraints({"a": "false"}, (fact,))

    def test_when_true_truthy_gate(self):
        """when_true=True gates on truthiness of the attr value."""
        fact = Requires(attr="a", needs=frozenset({"b"}), when_true=True)
        # a="false" is present but not truthy, so gate is false -> no check
        result = ModelUtil.check_constraints({"a": "false"}, (fact,))
        assert result == {"a": "false"}

    def test_when_true_truthy_gate_with_yes(self):
        """when_true=True with truthy value gates on the check."""
        fact = Requires(attr="a", needs=frozenset({"b"}), when_true=True)
        # a="yes" is truthy, so gate is true -> check needs
        with pytest.raises(ValueError, match="at least one of"):
            ModelUtil.check_constraints({"a": "yes"}, (fact,))

    def test_custom_message_used(self):
        """When message is set, it overrides the default."""
        fact = Requires(attr="a", needs=frozenset({"b"}), message="b is required with a")
        with pytest.raises(ValueError, match="b is required with a"):
            ModelUtil.check_constraints({"a": "val"}, (fact,))

    def test_lint_only_skipped(self):
        """When lint_only=True, constraint is skipped."""
        fact = Requires(attr="a", needs=frozenset({"b"}), lint_only=True)
        result = ModelUtil.check_constraints({"a": "val"}, (fact,))
        assert result == {"a": "val"}


class TestAllOrNone:
    """AllOrNone constraint: either all attrs are present or none are."""

    def test_all_present_succeeds(self):
        """When all attrs are present, check succeeds."""
        fact = AllOrNone(attrs=frozenset({"a", "b", "c"}))
        result = ModelUtil.check_constraints({"a": "1", "b": "2", "c": "3"}, (fact,))
        assert result == {"a": "1", "b": "2", "c": "3"}

    def test_none_present_succeeds(self):
        """When no attrs are present, check succeeds."""
        fact = AllOrNone(attrs=frozenset({"a", "b", "c"}))
        result = ModelUtil.check_constraints({}, (fact,))
        assert result == {}

    def test_some_present_fails(self):
        """When only some attrs are present, check fails."""
        fact = AllOrNone(attrs=frozenset({"a", "b", "c"}))
        with pytest.raises(ValueError, match="either all"):
            ModelUtil.check_constraints({"a": "1", "b": "2"}, (fact,))

    def test_custom_message_used(self):
        """When message is set, it overrides the default."""
        fact = AllOrNone(attrs=frozenset({"a", "b"}), message="all or nothing")
        with pytest.raises(ValueError, match="all or nothing"):
            ModelUtil.check_constraints({"a": "1"}, (fact,))

    def test_lint_only_skipped(self):
        """When lint_only=True, constraint is skipped."""
        fact = AllOrNone(attrs=frozenset({"a", "b"}), lint_only=True)
        result = ModelUtil.check_constraints({"a": "1"}, (fact,))
        assert result == {"a": "1"}


class TestForbids:
    """Forbids constraint: if attr is present, none of excludes may be present."""

    def test_attr_absent_succeeds(self):
        """When gating attr is absent, check succeeds regardless of excludes."""
        fact = Forbids(attr="a", excludes=frozenset({"b", "c"}))
        result = ModelUtil.check_constraints({"b": "val"}, (fact,))
        assert result == {"b": "val"}

    def test_attr_present_excludes_absent_succeeds(self):
        """When gating attr is present but excludes are absent, check succeeds."""
        fact = Forbids(attr="a", excludes=frozenset({"b", "c"}))
        result = ModelUtil.check_constraints({"a": "val"}, (fact,))
        assert result == {"a": "val"}

    def test_attr_present_excludes_present_fails(self):
        """When gating attr and any exclude are both present, check fails."""
        fact = Forbids(attr="a", excludes=frozenset({"b", "c"}))
        with pytest.raises(ValueError, match="none of"):
            ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))

    def test_when_true_false_presence_gate(self):
        """when_true=False gates on presence only (default)."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), when_true=False)
        # a="false" is present, so gate is true -> check excludes
        with pytest.raises(ValueError, match="none of"):
            ModelUtil.check_constraints({"a": "false", "b": "val"}, (fact,))

    def test_when_true_truthy_gate(self):
        """when_true=True gates on truthiness of the attr value."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), when_true=True)
        # a="false" is present but not truthy, so gate is false -> no check
        result = ModelUtil.check_constraints({"a": "false", "b": "val"}, (fact,))
        assert result == {"a": "false", "b": "val"}

    def test_when_true_truthy_gate_with_yes(self):
        """when_true=True with truthy value gates on the check."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), when_true=True)
        # a="yes" is truthy, so gate is true -> check excludes
        with pytest.raises(ValueError, match="none of"):
            ModelUtil.check_constraints({"a": "yes", "b": "val"}, (fact,))

    def test_custom_message_used(self):
        """When message is set, it overrides the default."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), message="b not allowed with a")
        with pytest.raises(ValueError, match="b not allowed with a"):
            ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))

    def test_lint_only_skipped(self):
        """When lint_only=True, constraint is skipped."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), lint_only=True)
        result = ModelUtil.check_constraints({"a": "val", "b": "val2"}, (fact,))
        assert result == {"a": "val", "b": "val2"}

    def test_excludes_when_true_both_present_fails(self):
        """When excludes_when_true=True, excluded attr must be truthy for violation."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), when_true=True, excludes_when_true=True)
        # Both a and b are truthy, so violation
        with pytest.raises(ValueError, match="none of"):
            ModelUtil.check_constraints({"a": "true", "b": "true"}, (fact,))

    def test_excludes_when_true_excluded_falsy_succeeds(self):
        """When excludes_when_true=True and excluded attr is falsy, check succeeds."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), when_true=True, excludes_when_true=True)
        # a is truthy but b is falsy, so no violation
        result = ModelUtil.check_constraints({"a": "true", "b": "false"}, (fact,))
        assert result == {"a": "true", "b": "false"}

    def test_excludes_when_true_excluded_absent_succeeds(self):
        """When excludes_when_true=True and excluded attr is absent, check succeeds."""
        fact = Forbids(attr="a", excludes=frozenset({"b"}), when_true=True, excludes_when_true=True)
        # a is truthy but b is absent, so no violation
        result = ModelUtil.check_constraints({"a": "true"}, (fact,))
        assert result == {"a": "true"}


class TestValidValues:
    """ValidValues constraint: attr value must be in the valid set."""

    def test_attr_absent_succeeds(self):
        """When attr is absent, check succeeds (optional attribute)."""
        fact = ValidValues(attr="a", values=frozenset({"x", "y", "z"}))
        result = ModelUtil.check_constraints({}, (fact,))
        assert result == {}

    def test_valid_value_succeeds(self):
        """When attr value is in the valid set, check succeeds."""
        fact = ValidValues(attr="a", values=frozenset({"x", "y", "z"}))
        result = ModelUtil.check_constraints({"a": "x"}, (fact,))
        assert result == {"a": "x"}

    def test_invalid_value_fails(self):
        """When attr value is not in the valid set, check fails."""
        fact = ValidValues(attr="a", values=frozenset({"x", "y", "z"}))
        with pytest.raises(ValueError, match="must be one of"):
            ModelUtil.check_constraints({"a": "invalid"}, (fact,))

    def test_callable_values_evaluated(self):
        """When values is a callable, it is evaluated at check time."""
        def dynamic_values():
            return {"dynamic1", "dynamic2"}

        fact = ValidValues(attr="a", values=dynamic_values)
        result = ModelUtil.check_constraints({"a": "dynamic1"}, (fact,))
        assert result == {"a": "dynamic1"}

    def test_callable_values_invalid_fails(self):
        """When callable-evaluated values don't match, check fails."""
        def dynamic_values():
            return {"dynamic1", "dynamic2"}

        fact = ValidValues(attr="a", values=dynamic_values)
        with pytest.raises(ValueError, match="must be one of"):
            ModelUtil.check_constraints({"a": "invalid"}, (fact,))

    def test_custom_message_used(self):
        """When message is set, it overrides the default."""
        fact = ValidValues(attr="a", values=frozenset({"x", "y"}), message="bad choice")
        with pytest.raises(ValueError, match="bad choice"):
            ModelUtil.check_constraints({"a": "z"}, (fact,))

    def test_lint_only_skipped(self):
        """When lint_only=True, constraint is skipped."""
        fact = ValidValues(attr="a", values=frozenset({"x", "y"}), lint_only=True)
        result = ModelUtil.check_constraints({"a": "z"}, (fact,))
        assert result == {"a": "z"}

    def test_default_message_sorts_values(self):
        """Default message sorts valid values for deterministic output."""
        fact = ValidValues(attr="a", values=frozenset({"z", "x", "y"}))
        with pytest.raises(ValueError, match="x, y, z"):
            ModelUtil.check_constraints({"a": "w"}, (fact,))


class TestAllowedValuesWhen:
    """AllowedValuesWhen constraint: when a gate attr is present/truthy, attr if PRESENT must be in allowed set."""

    def test_gate_attr_absent_succeeds(self):
        """When gate attr is absent, check succeeds regardless of attr value."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x", "y"}), when_attr="gate")
        result = ModelUtil.check_constraints({"a": "z"}, (fact,))
        assert result == {"a": "z"}

    def test_attr_absent_succeeds(self):
        """When attr is absent, check succeeds even if gate is present."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x", "y"}), when_attr="gate")
        result = ModelUtil.check_constraints({"gate": "value"}, (fact,))
        assert result == {"gate": "value"}

    def test_both_present_valid_succeeds(self):
        """When both gate and attr are present, and attr is in allowed, check succeeds."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x", "y"}), when_attr="gate")
        result = ModelUtil.check_constraints({"gate": "value", "a": "x"}, (fact,))
        assert result == {"gate": "value", "a": "x"}

    def test_both_present_invalid_fails(self):
        """When both gate and attr are present, and attr is not in allowed, check fails."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x", "y"}), when_attr="gate")
        with pytest.raises(ValueError, match="must be one of"):
            ModelUtil.check_constraints({"gate": "value", "a": "z"}, (fact,))

    def test_when_true_false_presence_gate(self):
        """when_true=False gates on presence only (default)."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x"}), when_attr="gate", when_true=False)
        # gate="false" is present, so gate is true -> check a
        with pytest.raises(ValueError, match="must be one of"):
            ModelUtil.check_constraints({"gate": "false", "a": "z"}, (fact,))

    def test_when_true_truthy_gate(self):
        """when_true=True gates on truthiness of the gate attr value."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x"}), when_attr="gate", when_true=True)
        # gate="false" is present but not truthy, so gate is false -> no check
        result = ModelUtil.check_constraints({"gate": "false", "a": "z"}, (fact,))
        assert result == {"gate": "false", "a": "z"}

    def test_when_true_truthy_gate_with_yes(self):
        """when_true=True with truthy gate value triggers the check."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x"}), when_attr="gate", when_true=True)
        # gate="yes" is truthy, so gate is true -> check a
        with pytest.raises(ValueError, match="must be one of"):
            ModelUtil.check_constraints({"gate": "yes", "a": "z"}, (fact,))

    def test_callable_allowed_evaluated(self):
        """When allowed is a callable, it is evaluated at check time."""
        def dynamic_allowed():
            return {"dynamic1", "dynamic2"}

        fact = AllowedValuesWhen(attr="a", allowed=dynamic_allowed, when_attr="gate")
        result = ModelUtil.check_constraints({"gate": "value", "a": "dynamic1"}, (fact,))
        assert result == {"gate": "value", "a": "dynamic1"}

    def test_callable_allowed_invalid_fails(self):
        """When callable-evaluated allowed doesn't match, check fails."""
        def dynamic_allowed():
            return {"dynamic1", "dynamic2"}

        fact = AllowedValuesWhen(attr="a", allowed=dynamic_allowed, when_attr="gate")
        with pytest.raises(ValueError, match="must be one of"):
            ModelUtil.check_constraints({"gate": "value", "a": "invalid"}, (fact,))

    def test_custom_message_used(self):
        """When message is set, it overrides the default."""
        fact = AllowedValuesWhen(
            attr="a", allowed=frozenset({"x"}), when_attr="gate", message="a must be x when gate is set"
        )
        with pytest.raises(ValueError, match="a must be x when gate is set"):
            ModelUtil.check_constraints({"gate": "value", "a": "z"}, (fact,))

    def test_custom_message_renders_actual_value(self):
        fact = AllowedValuesWhen(
            attr="distribution",
            allowed=frozenset({"random"}),
            when_attr="unique",
            message="not '{actual_value}'",
        )
        with pytest.raises(ValueError, match="not 'ordered'"):
            ModelUtil.check_constraints(
                {"unique": "true", "distribution": "ordered"},
                (fact,),
            )

    def test_lint_only_skipped(self):
        """When lint_only=True, constraint is skipped."""
        fact = AllowedValuesWhen(attr="a", allowed=frozenset({"x"}), when_attr="gate", lint_only=True)
        result = ModelUtil.check_constraints({"gate": "value", "a": "z"}, (fact,))
        assert result == {"gate": "value", "a": "z"}


class TestConstraintOrder:
    """Multiple constraints are checked in order; first violation raises."""

    def test_first_violation_raises(self):
        """When multiple constraints exist, the first violation raises."""
        constraints = (
            RequiredOneOf(attrs=frozenset({"a", "b"}), message="fact1"),
            MutuallyExclusive(attrs=frozenset({"c", "d"}), message="fact2"),
        )
        # b is present (fact1 ok), but both c and d are present (fact2 fails)
        with pytest.raises(ValueError, match="fact2"):
            ModelUtil.check_constraints({"b": "val", "c": "val", "d": "val"}, constraints)

    def test_multiple_constraints_success(self):
        """When all constraints pass, all are checked."""
        constraints = (
            RequiredOneOf(attrs=frozenset({"a", "b"})),
            MutuallyExclusive(attrs=frozenset({"c", "d"})),
        )
        result = ModelUtil.check_constraints({"a": "val1", "c": "val2"}, constraints)
        assert result == {"a": "val1", "c": "val2"}


class TestConstraintsSchemaExtra:
    """JSON schema injection via constraints_schema_extra callable."""

    def test_no_constraints_no_injection(self):
        """When model has no __constraints__, nothing is injected."""
        class NoConstraintsModel(BaseModel):
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(()))
            name: str

        schema = NoConstraintsModel.model_json_schema()
        assert "constraints" not in schema

    def test_constraints_injected(self):
        """When model has __constraints__, they are injected into schema."""
        class ConstrainedModel(BaseModel):
            name: str
            __constraints__ = (
                RequiredOneOf(attrs=frozenset({"a", "b"})),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = ConstrainedModel.model_json_schema()
        assert "constraints" in schema
        assert len(schema["constraints"]) == 1
        assert schema["constraints"][0]["kind"] == "required_one_of"
        assert set(schema["constraints"][0]["attrs"]) == {"a", "b"}

    def test_required_one_of_serialization(self):
        """RequiredOneOf is serialized correctly."""
        class Model(BaseModel):
            __constraints__ = (
                RequiredOneOf(attrs=frozenset({"x", "y", "z"})),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["kind"] == "required_one_of"
        assert fact["attrs"] == ["x", "y", "z"]  # sorted

    def test_mutually_exclusive_serialization(self):
        """MutuallyExclusive is serialized correctly."""
        class Model(BaseModel):
            __constraints__ = (
                MutuallyExclusive(attrs=frozenset({"a", "b"})),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["kind"] == "mutually_exclusive"
        assert fact["attrs"] == ["a", "b"]

    def test_requires_serialization(self):
        """Requires is serialized correctly with when_true field."""
        class Model(BaseModel):
            __constraints__ = (
                Requires(attr="a", needs=frozenset({"b", "c"}), when_true=True),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["kind"] == "requires"
        assert fact["attr"] == "a"
        assert fact["needs"] == ["b", "c"]  # sorted
        assert fact["when_true"] is True

    def test_forbids_serialization(self):
        """Forbids is serialized correctly with when_true field."""
        class Model(BaseModel):
            __constraints__ = (
                Forbids(attr="a", excludes=frozenset({"b", "c"}), when_true=False),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["kind"] == "forbids"
        assert fact["attr"] == "a"
        assert fact["excludes"] == ["b", "c"]  # sorted
        assert fact["when_true"] is False

    def test_valid_values_serialization(self):
        """ValidValues is serialized correctly with callable resolution."""
        class Model(BaseModel):
            __constraints__ = (
                ValidValues(attr="type", values=frozenset({"int", "string", "float"})),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["kind"] == "valid_values"
        assert fact["attr"] == "type"
        assert fact["values"] == ["float", "int", "string"]  # sorted

    def test_valid_values_callable_serialization(self):
        """ValidValues with callable is evaluated and sorted in schema."""
        def get_types():
            return {"z", "a", "m"}

        class Model(BaseModel):
            __constraints__ = (
                ValidValues(attr="type", values=get_types),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["values"] == ["a", "m", "z"]  # sorted, callable evaluated

    def test_lint_only_omitted_when_false(self):
        """lint_only is omitted from schema when False (default)."""
        class Model(BaseModel):
            __constraints__ = (
                RequiredOneOf(attrs=frozenset({"a"}), lint_only=False),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert "lint_only" not in fact

    def test_lint_only_included_when_true(self):
        """lint_only is included in schema when True."""
        class Model(BaseModel):
            __constraints__ = (
                RequiredOneOf(attrs=frozenset({"a"}), lint_only=True),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["lint_only"] is True

    def test_message_omitted_when_none(self):
        """message is omitted from schema when None (default)."""
        class Model(BaseModel):
            __constraints__ = (
                RequiredOneOf(attrs=frozenset({"a"})),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert "message" not in fact

    def test_message_included_when_set(self):
        """message is included in schema when set."""
        class Model(BaseModel):
            __constraints__ = (
                RequiredOneOf(attrs=frozenset({"a"}), message="custom error"),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["message"] == "custom error"

    def test_multiple_constraints_in_schema(self):
        """Multiple constraints are all injected in order."""
        class Model(BaseModel):
            __constraints__ = (
                RequiredOneOf(attrs=frozenset({"a", "b"})),
                MutuallyExclusive(attrs=frozenset({"c", "d"})),
                ValidValues(attr="type", values=frozenset({"x", "y"})),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        assert len(schema["constraints"]) == 3
        assert schema["constraints"][0]["kind"] == "required_one_of"
        assert schema["constraints"][1]["kind"] == "mutually_exclusive"
        assert schema["constraints"][2]["kind"] == "valid_values"

    def test_forbids_with_excludes_when_true_serialization(self):
        """Forbids with excludes_when_true is serialized correctly."""
        class Model(BaseModel):
            __constraints__ = (
                Forbids(attr="a", excludes=frozenset({"b", "c"}), when_true=True, excludes_when_true=True),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["kind"] == "forbids"
        assert fact["attr"] == "a"
        assert fact["excludes"] == ["b", "c"]  # sorted
        assert fact["when_true"] is True
        assert fact["excludes_when_true"] is True

    def test_forbids_excludes_when_true_false_not_serialized(self):
        """Forbids with excludes_when_true=False omits the field (default)."""
        class Model(BaseModel):
            __constraints__ = (
                Forbids(attr="a", excludes=frozenset({"b"}), excludes_when_true=False),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["excludes_when_true"] is False  # Always serialized for Forbids

    def test_allowed_values_when_serialization(self):
        """AllowedValuesWhen is serialized correctly."""
        class Model(BaseModel):
            __constraints__ = (
                AllowedValuesWhen(attr="dist", allowed=frozenset({"random"}), when_attr="unique", when_true=True),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["kind"] == "allowed_values_when"
        assert fact["attr"] == "dist"
        assert fact["allowed"] == ["random"]  # sorted
        assert fact["when_attr"] == "unique"
        assert fact["when_true"] is True

    def test_allowed_values_when_callable_serialization(self):
        """AllowedValuesWhen with callable allowed is evaluated and sorted in schema."""
        def get_allowed():
            return {"z", "a", "m"}

        class Model(BaseModel):
            __constraints__ = (
                AllowedValuesWhen(attr="dist", allowed=get_allowed, when_attr="unique"),
            )
            model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

        schema = Model.model_json_schema()
        fact = schema["constraints"][0]
        assert fact["allowed"] == ["a", "m", "z"]  # sorted, callable evaluated


class TestModelUniqueConstraintContracts:
    def test_key_forbids_any_explicit_numeric_distribution_with_unique(self) -> None:
        from datamimic_ce.model.key_model import KeyModel

        with pytest.raises(ValueError, match="unique.*cannot be combined.*distribution"):
            KeyModel(name="id", values="1,2", unique=True, distribution="shuffle")

        constraints = KeyModel.model_json_schema()["constraints"]
        assert any(
            fact["kind"] == "forbids"
            and fact["attr"] == "unique"
            and fact["excludes"] == ["distribution"]
            for fact in constraints
        )
        assert not any(
            fact["kind"] == "allowed_values_when"
            and fact["when_attr"] == "unique"
            for fact in constraints
        )

    def test_key_unique_rejects_weighted_source_during_model_validation(self) -> None:
        from datamimic_ce.model.key_model import KeyModel

        with pytest.raises(ValueError, match="unique.*key.*requires.*values"):
            KeyModel(name="segment", source="segments.wgt.csv", unique=True)

        constraints = KeyModel.model_json_schema()["constraints"]
        assert any(
            fact["kind"] == "requires"
            and fact["attr"] == "unique"
            and fact["needs"] == ["values"]
            for fact in constraints
        )

    def test_reference_declares_and_enforces_source_unique_constraints(self) -> None:
        from datamimic_ce.model.reference_model import ReferenceModel

        constraints = ReferenceModel.model_json_schema()["constraints"]
        assert any(
            fact["kind"] == "forbids"
            and fact["attr"] == "unique"
            and fact["excludes"] == ["cyclic"]
            for fact in constraints
        )
        assert any(
            fact["kind"] == "allowed_values_when"
            and fact["when_attr"] == "unique"
            and fact["allowed"] == ["random"]
            for fact in constraints
        )

        with pytest.raises(ValueError, match="not 'ordered'"):
            ReferenceModel(
                name="customer_id",
                source="db",
                sourceType="customer",
                unique=True,
                distribution="ordered",
            )
