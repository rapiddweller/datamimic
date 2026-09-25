"""Pin XML diagnostics and the CE 5.0 shared locale error contract."""

import pytest

from datamimic_ce.authoring.adapters.linter import lint_source
from datamimic_ce.domains.facade import generate_domain
from datamimic_ce.domains.shared.services.address_api import AddressRequest
from datamimic_ce.domains.shared.services.address_api import generate as generate_address
from datamimic_ce.errors import ErrorCode, InvalidLocaleError
from datamimic_ce.errors.base import DomainError


def test_valid_setup_has_no_parser_diagnostic() -> None:
    result = lint_source('<setup rngSeed="7"><generate name="items" count="1"/></setup>')

    assert result.ok
    assert result.diagnostics == []


def test_malformed_xml_keeps_authoring_code() -> None:
    result = lint_source("<setup><generate></setup>")

    assert not result.ok
    assert [diagnostic.rule for diagnostic in result.diagnostics] == ["DM001"]


def test_address_locale_error_uses_shared_error_contract() -> None:
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
    with pytest.raises(InvalidLocaleError) as caught:
        generate_domain(request)

    error = caught.value
    assert isinstance(error, ValueError)
    assert error.code is ErrorCode.INVALID_LOCALE
    assert error.locale == "xx_XX"
    assert error.path == "/locale"
    assert error.request_hash
    assert str(error) == "[E002] Locale 'xx_XX' is not supported. Use a valid locale like 'en_US'."
    assert error.to_dict()["code"] == "E002"
    assert error.to_dict()["hint"]


@pytest.mark.parametrize("locale", ["", "not-a-locale"])
def test_facade_rejects_malformed_locale_as_schema_error(locale: str) -> None:
    request = {
        "domain": "address",
        "version": "v1",
        "count": 1,
        "seed": 0,
        "locale": locale,
        "clock": "2025-01-01T00:00:00Z",
    }

    with pytest.raises(DomainError) as caught:
        generate_domain(request)

    assert type(caught.value) is DomainError
    assert caught.value.code == "schema_validation_failed"
    assert caught.value.path == "/locale"
    assert caught.value.to_dict()["code"] == "schema_validation_failed"


def test_unsupported_version_is_not_reported_as_invalid_locale() -> None:
    with pytest.raises(ValueError) as caught:
        generate_address(AddressRequest(version="v2"))

    assert type(caught.value) is ValueError
    assert not isinstance(caught.value, InvalidLocaleError)


def test_locale_error_uses_enum_code_and_complete_public_dict() -> None:
    with pytest.raises(InvalidLocaleError) as caught:
        generate_address(AddressRequest(locale="fr_FR", request_hash="request-1"))

    error = caught.value
    assert error.code is ErrorCode.INVALID_LOCALE
    assert error.locale == "fr_FR"
    assert error.to_dict() == {
        "code": "E002",
        "message": "[E002] Locale 'fr_FR' is not supported. Use a valid locale like 'en_US'.",
        "path": "/locale",
        "request_hash": "request-1",
        "hint": "Choose a locale mapping to dataset codes: DE, US, VN",
    }
