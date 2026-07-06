# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

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
