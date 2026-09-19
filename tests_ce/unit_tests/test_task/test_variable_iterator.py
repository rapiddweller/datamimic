# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""VariableIterator (the <variable storage="iterator"> proxy): position-indexed dict-key
lookup, cyclic/non-cyclic, case-insensitive fallback, and error paths not exercised by the
DSL-level matrix in tests_ce/external_service_tests/test_variable_storage/ (which only ever
reads fields that exist)."""

import pytest

from datamimic_ce.tasks.variable_iterator import VariableIterator


class _Row:
    """Non-dict row object, to exercise the getattr/hasattr fallback branch."""

    def __init__(self, value):
        self.field = value


class TestVariableIterator:
    def test_cyclic_wraps(self):
        vi = VariableIterator([{"id": 1}, {"id": 2}, {"id": 3}], cyclic=True, position=4)
        assert vi.id == 2

    def test_non_cyclic_in_bounds_returns_row(self):
        vi = VariableIterator([{"id": 1}, {"id": 2}], cyclic=False, position=1)
        assert vi.id == 2

    def test_non_cyclic_exhausts_to_none(self):
        vi = VariableIterator([{"id": 1}, {"id": 2}], cyclic=False, position=5)
        assert vi.id is None

    def test_empty_pool_returns_none(self):
        vi = VariableIterator([], cyclic=True, position=0)
        assert vi.id is None

    def test_case_insensitive_fallback(self):
        vi = VariableIterator([{"ID": 9}], cyclic=True, position=0)
        assert vi.id == 9

    def test_dict_row_missing_field_raises(self):
        vi = VariableIterator([{"id": 1}], cyclic=True, position=0)
        with pytest.raises(AttributeError, match="no field 'missing'"):
            _ = vi.missing

    def test_non_dict_row_attribute_access(self):
        vi = VariableIterator([_Row("hello")], cyclic=True, position=0)
        assert vi.field == "hello"

    def test_non_dict_row_missing_attribute_raises(self):
        vi = VariableIterator([_Row("hello")], cyclic=True, position=0)
        with pytest.raises(AttributeError, match="no attribute 'missing'"):
            _ = vi.missing

    def test_private_attribute_lookup_raises(self):
        vi = VariableIterator([{"id": 1}], cyclic=True, position=0)
        with pytest.raises(AttributeError):
            _ = vi._nonexistent

    def test_get_mirrors_attribute_access(self):
        vi = VariableIterator([{"id": 7}], cyclic=True, position=0)
        assert vi.get("id") == 7

    def test_repr(self):
        vi = VariableIterator([{"id": 1}, {"id": 2}], cyclic=True, position=3)
        text = repr(vi)
        assert "position=3" in text
        assert "cyclic=True" in text
        assert "pool_size=2" in text
