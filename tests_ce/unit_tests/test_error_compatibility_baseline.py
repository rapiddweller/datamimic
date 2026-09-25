"""Keep the existing CE XML parser diagnostics stable during error migration."""

from datamimic_ce.authoring.adapters.linter import lint_source


def test_valid_setup_has_no_parser_diagnostic() -> None:
    result = lint_source('<setup rngSeed="7"><generate name="items" count="1"/></setup>')

    assert result.ok
    assert result.diagnostics == []


def test_malformed_xml_keeps_authoring_code() -> None:
    result = lint_source("<setup><generate></setup>")

    assert not result.ok
    assert [diagnostic.rule for diagnostic in result.diagnostics] == ["DM001"]
