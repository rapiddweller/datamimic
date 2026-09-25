from datamimic_ce.errors.base import InvalidLocaleError
from datamimic_ce.errors.codes import ErrorCode
from datamimic_ce.errors.formatters import invalid_locale_message


def invalid_locale_error(locale: str, *, hint: str, path: str, request_hash: str) -> InvalidLocaleError:
    return InvalidLocaleError(
        code=ErrorCode.INVALID_LOCALE,
        message=invalid_locale_message(locale),
        hint=hint,
        path=path,
        request_hash=request_hash,
        locale=locale,
    )
