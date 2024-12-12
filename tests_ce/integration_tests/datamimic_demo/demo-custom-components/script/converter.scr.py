# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.converter.converter import Converter

class UpperCaseConverter(Converter):
    def convert(self, value: str) -> str:
        return value.upper()


class MaskEmailConverter(Converter):
    def convert(self, value: str) -> str:
        local_part, domain = value.split("@")
        masked_local = local_part[0] + "*" * (len(local_part) - 1)
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
            "withdrawal": "WITHDRAWAL",
        }
        return transaction_types.get(value.lower(), "OTHER")
