from datamimic_ce.errors.catalog import invalid_locale_text
from datamimic_ce.errors.codes import ErrorCode


def invalid_locale_message(locale: str) -> str:
    return f"[{ErrorCode.INVALID_LOCALE.value}] {invalid_locale_text(locale)}"
