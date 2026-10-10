import pickle

import datamimic_ce.errors as package_errors
from datamimic_ce.errors import DomainError, DomainErrorCode, ErrorCode, InvalidLocaleError
from datamimic_ce.errors.base import DomainError as BaseDomainError
from datamimic_ce.errors.base import InvalidLocaleError as BaseInvalidLocaleError
from datamimic_ce.errors.codes import DomainErrorCode as CodesDomainErrorCode
from datamimic_ce.errors.codes import ErrorCode as CodesErrorCode
from datamimic_ce.errors.factory import invalid_locale_error


def test_package_error_exports_keep_their_defining_objects() -> None:
    assert package_errors.__all__ == [
        "DomainError",
        "DomainErrorCode",
        "ErrorCode",
        "InvalidLocaleError",
        "invalid_locale_error",
    ]
    assert package_errors.DomainError is BaseDomainError
    assert package_errors.InvalidLocaleError is BaseInvalidLocaleError
    assert package_errors.DomainErrorCode is CodesDomainErrorCode
    assert package_errors.ErrorCode is CodesErrorCode
    assert package_errors.invalid_locale_error is invalid_locale_error


def test_domain_error_round_trip_keeps_legacy_empty_string() -> None:
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
    assert str(restored) == ""
    assert restored.to_dict() == error.to_dict()


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
