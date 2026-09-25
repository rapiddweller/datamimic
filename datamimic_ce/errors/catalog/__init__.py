from datamimic_ce.errors.codes import ErrorCode

ERROR_TEMPLATES = {
    ErrorCode.INVALID_LOCALE: "Locale '{locale}' is not supported. Use a valid locale like 'en_US'.",
}

__all__ = ["ERROR_TEMPLATES", "ErrorCode"]
