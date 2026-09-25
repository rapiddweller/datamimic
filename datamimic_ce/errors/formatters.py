from datamimic_ce.errors.catalog import ERROR_TEMPLATES, ErrorCode


def invalid_locale_message(locale: str) -> str:
    return f"[{ErrorCode.INVALID_LOCALE.value}] {ERROR_TEMPLATES[ErrorCode.INVALID_LOCALE].format(locale=locale)}"
