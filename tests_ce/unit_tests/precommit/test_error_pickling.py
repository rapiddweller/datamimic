# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import pickle

import pytest

import datamimic_ce.errors as package_errors
from datamimic_ce.errors import DomainError, DomainErrorCode, ErrorCode, InvalidLocaleError
from datamimic_ce.errors.base import PICKLE_RESTORERS, UserRuntimeError
from datamimic_ce.errors.base import DomainError as BaseDomainError
from datamimic_ce.errors.base import InvalidLocaleError as BaseInvalidLocaleError
from datamimic_ce.errors.codes import DomainErrorCode as CodesDomainErrorCode
from datamimic_ce.errors.codes import ErrorCode as CodesErrorCode
from datamimic_ce.errors.factory import invalid_locale_error


def test_package_error_exports_keep_their_defining_objects() -> None:
    assert set(package_errors.__all__) >= {
        "DomainError",
        "DomainErrorCode",
        "ErrorCode",
        "InvalidLocaleError",
        "invalid_locale_error",
    }
    assert package_errors.DomainError is BaseDomainError
    assert package_errors.InvalidLocaleError is BaseInvalidLocaleError
    assert package_errors.DomainErrorCode is CodesDomainErrorCode
    assert package_errors.ErrorCode is CodesErrorCode
    assert package_errors.invalid_locale_error is invalid_locale_error


def test_domain_error_round_trip_keeps_message_text() -> None:
    error = DomainError(
        code=DomainErrorCode.INVALID_REQUEST,
        message="invalid input",
        hint="fix input",
        path="/field",
        request_hash="request-hash",
        details={"issue": "bad value"},
    )

    restored = pickle.loads(pickle.dumps(error))

    assert type(restored) is DomainError
    assert str(restored) == "invalid input"
    assert restored.to_dict() == error.to_dict()


@pytest.mark.parametrize(
    ("message", "expected_text"),
    [
        ("invalid input", "invalid input"),  # valid: a non-empty message is the text
        ("", "DomainError"),  # empty: the class name stands in, so the log line is never blank
    ],
)
def test_domain_error_str_is_message_or_class_name(message: str, expected_text: str) -> None:
    error = DomainError(
        code=DomainErrorCode.INVALID_REQUEST,
        message=message,
        hint=None,
        path="/field",
        request_hash="request-hash",
    )

    assert str(error) == expected_text
    assert f"failed: {error}" == f"failed: {expected_text}"
    restored = pickle.loads(pickle.dumps(error))
    assert str(restored) == expected_text
    assert restored.message == message


def test_invalid_locale_error_round_trip_keeps_typed_fields_and_message() -> None:
    error = InvalidLocaleError(
        code=ErrorCode.INVALID_LOCALE,
        message="[E002] Locale 'xx_XX' is not supported.",
        hint="Choose a supported locale.",
        path="/locale",
        request_hash="request-hash",
        locale="xx_XX",
    )

    restored = pickle.loads(pickle.dumps(error))

    assert type(restored) is InvalidLocaleError
    assert str(restored) == str(error)
    assert restored.locale == error.locale
    assert restored.to_dict() == error.to_dict()


def test_every_error_reduces_to_a_published_restorer() -> None:
    # The bounded child reads pickled errors against a list of allowed globals that comes from PICKLE_RESTORERS.
    # A restorer that is missing there would turn a real error into a refused pickle.
    request = {"code": DomainErrorCode.INVALID_REQUEST, "message": "m", "hint": None, "path": "/p", "request_hash": "h"}
    errors = [DomainError(**request), InvalidLocaleError(**request, details=None, locale="xx"), UserRuntimeError("m")]

    assert {error.__reduce__()[0] for error in errors} == set(PICKLE_RESTORERS)
