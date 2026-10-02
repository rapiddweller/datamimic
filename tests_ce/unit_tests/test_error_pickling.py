import pickle

from datamimic_ce.errors import DomainError, DomainErrorCode, ErrorCode, InvalidLocaleError


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
