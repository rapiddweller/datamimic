# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from dataclasses import dataclass

from datamimic_ce.model.reference_model import ReferenceModel
from datamimic_ce.statements.statement import Statement


@dataclass(frozen=True)
class ReferenceField:
    """One source-column -> target-field mapping in a (composite) reference."""

    target: str
    source_key: str


class ReferenceStatement(Statement):
    def __init__(self, model: ReferenceModel, fields: list[ReferenceField], parent_stmt: Statement | None = None):
        # Pass the parent so full_name is a path (e.g. "orders|slot"), unique per statement —
        # two same-named references in different <generate>s must not share a cache key.
        super().__init__(model.name, parent_stmt)
        self._source = model.source
        self._source_type = model.source_type
        self._unique = model.unique
        # Always >= 1: a legacy 'sourceKey' is normalised to a single field by the parser.
        self._fields = fields

    @property
    def source(self):
        return self._source

    @property
    def source_type(self):
        return self._source_type

    @property
    def source_key(self):
        # Legacy single-field accessor (first field's source column).
        return self._fields[0].source_key

    @property
    def unique(self):
        return self._unique

    @property
    def fields(self) -> list[ReferenceField]:
        return self._fields

    @property
    def source_keys(self) -> list[str]:
        return [field.source_key for field in self._fields]

    @property
    def targets(self) -> list[str]:
        return [field.target for field in self._fields]

    @property
    def is_composite(self) -> bool:
        return len(self._fields) > 1
