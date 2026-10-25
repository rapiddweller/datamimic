# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re
from enum import StrEnum


class ExportOperation(StrEnum):
    """Client write operation selected by a target suffix (``clientId.<operation>``).

    A plain ``clientId`` target inserts. Parsed once at the target boundary
    (the IO exporter registry) so everything downstream dispatches on the
    enum instead of raw strings.
    """

    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"
    # Source-free, one-time destructive intents (BC-4.0-016): clear keeps the table or collection, drop removes it.
    CLEAR = "clear"
    DROP = "drop"

    @property
    def is_statement_operation(self) -> bool:
        """A source-free operation that runs once instead of consuming rows."""
        return self in (ExportOperation.CLEAR, ExportOperation.DROP)

    @classmethod
    def from_target(cls, target: str) -> tuple[str, "ExportOperation"] | None:
        """``("db", ExportOperation.CLEAR)`` for the target ``db.clear``; None for a plain or unknown-suffix target."""
        client, dot, suffix = target.partition(".")
        if not dot:
            return None
        try:
            return client, ExportOperation(suffix)
        except ValueError:
            return None

    @classmethod
    def for_rdbms(cls) -> tuple["ExportOperation", ...]:
        """What an RDBMS client accepts: everything except drop (use ``<execute>`` DDL for that)."""
        return (cls.UPDATE, cls.UPSERT, cls.DELETE, cls.CLEAR)

    @classmethod
    def for_mongodb(cls) -> tuple["ExportOperation", ...]:
        return (cls.UPDATE, cls.UPSERT, cls.DELETE, cls.CLEAR, cls.DROP)


def split_targets(target: str | None) -> list[str]:
    """The targets of a ``target=`` attribute: split on commas outside parentheses."""
    if not target:
        return []
    parts = [part.strip() for part in re.split(r",\s*(?![^(]*\))", target)]
    return [part for part in parts if part]


def names_statement_operation(target: str | None) -> bool:
    """Whether any target is a source-free ``clear`` or ``drop`` operation."""
    for part in split_targets(target):
        parsed = ExportOperation.from_target(part)
        if parsed is not None and parsed[1].is_statement_operation:
            return True
    return False
