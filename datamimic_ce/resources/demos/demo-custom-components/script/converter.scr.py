from datamimic_ce.domains.api import Converter


class UpperCaseConverter(Converter):  # noqa: F821
    def convert(self, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("UpperCaseConverter expects a string")
        return value.upper()


class MaskEmailConverter(Converter):  # noqa: F821
    def convert(self, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("MaskEmailConverter expects a string")
        local_part, domain = value.split("@")
        masked_local = local_part[0] + "*" * (len(local_part) - 1)
        return f"{masked_local}@{domain}"


class AnonymizeNameConverter(Converter):  # noqa: F821
    def convert(self, value: object) -> str:
        return "ANONYMOUS"


class CurrencyFormatterConverter(Converter):  # noqa: F821
    def convert(self, value: object) -> str:
        return f"${format(value, ',.2f')}"


class TransactionTypeConverter(Converter):  # noqa: F821
    def convert(self, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("TransactionTypeConverter expects a string")
        transaction_types = {
            "purchase": "PURCHASE",
            "refund": "REFUND",
            "transfer": "TRANSFER",
            "withdrawal": "WITHDRAWAL",
        }
        return transaction_types.get(value.lower(), "OTHER")
