# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""A '.fcw' source is a real, engine-supported data file (fixed-width columns) - DM402
(UnknownSource) must not flag it as unknown, the same way it doesn't flag .csv/.json/.xlsx."""

from pathlib import Path

from datamimic_ce.authoring import lint_descriptor


def test_fcw_source_is_not_flagged_as_unknown(tmp_path: Path) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(
        '<setup><generate name="p" source="products.fcw" count="1" target="ConsoleExporter"/></setup>'
    )
    result = lint_descriptor(descriptor)
    rules = {diag.rule for diag in result.diagnostics}
    assert "DM402" not in rules
