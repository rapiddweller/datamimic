from datamimic_ce.converter.converter import Converter


class UpperCaseConverter(Converter):  # noqa: F821
    def convert(self, value: str) -> str:
        return value.upper()


class MaskEmailConverter(Converter):  # noqa: F821
    def convert(self, value: str) -> str:
        local_part, domain = value.split("@")
        masked_local = local_part[0] + "*" * (len(local_part) - 1)
        return f"{masked_local}@{domain}"


class AnonymizeNameConverter(Converter):  # noqa: F821
    def convert(self, value: str) -> str:
        return "ANONYMOUS"


class CurrencyFormatterConverter(Converter):  # noqa: F821
    def convert(self, value: float) -> str:
        return f"${value:,.2f}"


class TransactionTypeConverter(Converter):  # noqa: F821
    def convert(self, value: str) -> str:
        transaction_types = {
            "purchase": "PURCHASE",
            "refund": "REFUND",
            "transfer": "TRANSFER",
            "withdrawal": "WITHDRAWAL",
        }
        return transaction_types.get(value.lower(), "OTHER")
