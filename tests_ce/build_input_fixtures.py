# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.


def _entry(attributes: str, fields: str) -> str:
    return f'<setup rngSeed="7"><generate name="rows" {attributes}>{fields}</generate></setup>'


_GATES = {"smoke_export": True, "deterministic_replay": True}
