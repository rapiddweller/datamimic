# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Tests for NestedKeyModel field validators, specifically sourceEntity validation."""

import pytest
from pydantic import ValidationError

from datamimic_ce.model.nested_key_model import NestedKeyModel


class TestNestedKeyModelSourceEntity:
    """Test NestedKeyModel.sourceEntity validation (_entity_not_blank validator)."""

    def test_valid_source_entity_is_accepted(self):
        """A valid non-blank sourceEntity value should be accepted."""
        model = NestedKeyModel(name="items", type="list", count="5", sourceEntity="orders")
        assert model.source_entity == "orders"

    def test_blank_source_entity_is_rejected(self):
        """An empty-string sourceEntity should be rejected with validation error."""
        with pytest.raises(ValidationError, match="sourceEntity must not be blank"):
            NestedKeyModel(name="items", type="list", count="5", sourceEntity="")

    def test_whitespace_only_source_entity_is_rejected(self):
        """A whitespace-only sourceEntity should be rejected."""
        with pytest.raises(ValidationError, match="sourceEntity must not be blank"):
            NestedKeyModel(name="items", type="list", count="5", sourceEntity="   ")

    def test_source_entity_whitespace_is_stripped(self):
        """Surrounding whitespace in sourceEntity should be stripped."""
        model = NestedKeyModel(name="items", type="list", count="5", sourceEntity="  orders  ")
        assert model.source_entity == "orders"

    def test_source_entity_with_internal_spaces_preserved(self):
        """Internal spaces in sourceEntity should be preserved during strip."""
        model = NestedKeyModel(name="items", type="list", count="5", sourceEntity="  order items  ")
        assert model.source_entity == "order items"

    def test_source_entity_with_forward_slash_is_rejected(self):
        """sourceEntity containing forward slash should be rejected as path-like."""
        with pytest.raises(ValidationError, match="sourceEntity must be a plain entity name, not a path"):
            NestedKeyModel(name="items", type="list", count="5", sourceEntity="public/orders")

    def test_source_entity_with_backslash_is_rejected(self):
        """sourceEntity containing backslash should be rejected as path-like."""
        with pytest.raises(ValidationError, match="sourceEntity must be a plain entity name, not a path"):
            NestedKeyModel(name="items", type="list", count="5", sourceEntity="public\\orders")

    def test_source_entity_with_double_dot_is_rejected(self):
        """sourceEntity containing .. should be rejected as path-traversal."""
        with pytest.raises(ValidationError, match="sourceEntity must be a plain entity name, not a path"):
            NestedKeyModel(name="items", type="list", count="5", sourceEntity="../orders")

    def test_source_entity_none_is_accepted(self):
        """sourceEntity=None (not specified) should be accepted and remain None."""
        model = NestedKeyModel(name="items", type="list", count="5")
        assert model.source_entity is None

    def test_source_entity_with_schema_qualified_name(self):
        """sourceEntity with schema-qualified name (schema.table) should be accepted."""
        model = NestedKeyModel(name="items", type="list", count="5", sourceEntity="public.orders")
        assert model.source_entity == "public.orders"
