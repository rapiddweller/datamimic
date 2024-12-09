# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



class UpperCaseConverter(Converter):
    def convert(self, value: str) -> str:
        return value.upper()


class MaskEmailConverter(Converter):
    def convert(self, value: str) -> str:
        local_part, domain = value.split('@')
        masked_local = local_part[0] + '*' * (len(local_part) - 1)
        return f"{masked_local}@{domain}"


class AnonymizeNameConverter(Converter):
    def convert(self, value: str) -> str:
        return "ANONYMOUS"


class CurrencyFormatterConverter(Converter):
    def convert(self, value: float) -> str:
        return f"${value:,.2f}"


class TransactionTypeConverter(Converter):
    def convert(self, value: str) -> str:
        transaction_types = {
            "purchase": "PURCHASE",
            "refund": "REFUND",
            "transfer": "TRANSFER",
            "withdrawal": "WITHDRAWAL"
        }
        return transaction_types.get(value.lower(), "OTHER")
