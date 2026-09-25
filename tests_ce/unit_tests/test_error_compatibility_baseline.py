"""Keep the existing CE XML parser diagnostics stable during error migration."""

import pytest

from datamimic_ce.authoring.adapters.linter import lint_source
from datamimic_ce.domains.facade import generate_domain
from datamimic_ce.errors.base import DomainError


def test_valid_setup_has_no_parser_diagnostic() -> None:
    result = lint_source('<setup rngSeed="7"><generate name="items" count="1"/></setup>')

    assert result.ok
    assert result.diagnostics == []


def test_malformed_xml_keeps_authoring_code() -> None:
    result = lint_source("<setup><generate></setup>")

    assert not result.ok
    assert [diagnostic.rule for diagnostic in result.diagnostics] == ["DM001"]


def test_address_locale_error_baseline() -> None:
    request = {
        "domain": "address",
        "version": "v1",
        "count": 1,
        "seed": 0,
        "locale": "en_US",
        "clock": "2025-01-01T00:00:00Z",
    }
    assert generate_domain(request)["items"]

    request["locale"] = "xx_XX"
    with pytest.raises(DomainError) as caught:
        generate_domain(request)
    assert type(caught.value) is DomainError
    assert caught.value.code == "unsupported_locale"
    assert str(caught.value) == ""
    assert caught.value.path == "/locale"
