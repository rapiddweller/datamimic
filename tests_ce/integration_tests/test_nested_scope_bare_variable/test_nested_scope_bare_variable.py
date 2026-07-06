# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.factory.datamimic_test_factory import DataMimicTestFactory

_dir = Path(__file__).resolve().parent


def test_bare_variable_resolves_in_nested_generate():
    """A sibling <variable> feeds a <key> script by BARE name at any nesting depth (regression:
    a nested scope's own variable was only reachable as <scope>.<var>, not bare)."""
    outer = DataMimicTestFactory(_dir / "nested_scope.xml", "outer").create()
    for row in outer["inner"]:
        assert row["salutation"], "bare sibling variable did not resolve in nested scope"
        assert row["outer_tag_family"], "bare ancestor variable did not resolve"
        assert row["qualified"], "qualified nested path did not resolve"


def test_bare_variable_does_not_shadow_ancestor_across_depths():
    """A scope's own bare variable resolution must not flip which ancestor value a deeper scope
    sees: 'leaf' has no own 'v', so bare 'v' still resolves to the OUTERMOST declaration
    ('outer_val'), not the nearer 'mid' one - a name collision between scopes at different depths
    can't silently change what an unrelated bare reference means."""
    collision = DataMimicTestFactory(_dir / "nested_scope.xml", "collision").create()
    assert collision["mid"][0]["leaf"][0]["bare_v"] == "outer_val"


def test_bare_variable_does_not_reach_up_past_self():
    """A leaf script referencing a bare name that only a non-self ancestor declares ('mid', declared
    two scopes up) must still fail loud with the scope-rule guidance, not silently resolve - the
    same as before this fix, just scoped to the self-only bare resolution it adds."""
    engine = DataMimicTest(_dir, "nested_scope_reach_up.xml", capture_test_result=True)
    with pytest.raises(ValueError, match="not defined in this scope"):
        engine.test_with_timer()


def test_own_bare_variable_does_not_override_ancestor_of_same_name():
    """A scope's own bare variable fills gaps, it never overrides a name the ancestor already
    provides bare (regression: tests_ce/functional_tests/test_sqlite's `id + simple_user.id`
    silently collapsed onto the SAME id for every row once the nested scope's own 'id' started
    winning bare resolution)."""
    result = DataMimicTestFactory(_dir / "nested_scope.xml", "self_vs_ancestor").create()
    child = result["child"][0]
    assert child["bare_id"] == "outer_id"
    assert child["qualified_id"] == "child_id"
