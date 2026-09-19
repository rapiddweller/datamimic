# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any


class VariableIterator:
    """Proxy for <variable storage="iterator">: attribute access (`row.field`) resolves from a
    fixed global row POSITION rather than advancing a Python iterator, so repeated reads within
    one generated row's scripts are idempotent (same row, same values) while the next generated
    row (a new VariableIterator, position+1) sees the next pool entry. cyclic wraps
    (position % len(data)); non-cyclic exhausts (every attribute access on a past-the-end
    position returns None, matching DATAMIMIC EE's exhaustion contract).

    Deliberately simpler than DATAMIMIC EE's equivalent: no multi-variable declaration-order
    start_offset reservation (ponytail: a narrow EE nicety for several storage="iterator"
    variables sharing one pool in one <generate>; add if a real script needs cross-variable
    correlation - see datamimic_ce/tasks/variable_task.py for how `position` is derived from
    pagination.skip + a per-task row counter).
    """

    def __init__(self, data: list[Any], cyclic: bool, position: int):
        self._data = data
        self._cyclic = cyclic
        self._position = position

    def _current_row(self) -> Any:
        if not self._data:
            return None
        if self._cyclic:
            return self._data[self._position % len(self._data)]
        if self._position >= len(self._data):
            return None
        return self._data[self._position]

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        row = self._current_row()
        if row is None:
            return None
        if isinstance(row, dict):
            if name in row:
                return row[name]
            fold = name.casefold()
            for key in row:
                if isinstance(key, str) and key.casefold() == fold:
                    return row[key]
            raise AttributeError(f"row at position {self._position} has no field '{name}': {row}")
        if hasattr(row, name):
            return getattr(row, name)
        raise AttributeError(f"row at position {self._position} has no attribute '{name}': {row}")

    def get(self, name: str) -> Any:
        return getattr(self, name)

    def __repr__(self) -> str:
        return f"VariableIterator(position={self._position}, cyclic={self._cyclic}, pool_size={len(self._data)})"
