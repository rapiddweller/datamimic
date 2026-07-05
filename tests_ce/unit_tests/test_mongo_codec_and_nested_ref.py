# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from decimal import Decimal

from bson.decimal128 import Decimal128

from datamimic_ce.clients.mongodb_client import MongoDBClient


class TestMongoDecimalCodec:
    """decimal.Decimal round-trips through mongo as the native Decimal128 (not a lossy float)."""

    def test_encode_decimal_to_decimal128(self):
        out = MongoDBClient._to_bson({"price": Decimal("60.09"), "qty": 3})
        assert isinstance(out["price"], Decimal128)
        assert out["price"].to_decimal() == Decimal("60.09")
        assert out["qty"] == 3  # non-decimal untouched

    def test_encode_is_recursive(self):
        out = MongoDBClient._to_bson({"a": [{"b": Decimal("1.5")}], "c": {"d": Decimal("2.0")}})
        assert isinstance(out["a"][0]["b"], Decimal128)
        assert isinstance(out["c"]["d"], Decimal128)

    def test_decode_decimal128_to_decimal(self):
        out = MongoDBClient._from_bson({"price": Decimal128("60.09"), "name": "x"})
        assert out["price"] == Decimal("60.09")
        assert isinstance(out["price"], Decimal)
        assert out["name"] == "x"

    def test_roundtrip_supports_arithmetic(self):
        # the shop demo does product.price * qty on a value read back from mongo
        stored = MongoDBClient._to_bson({"price": Decimal("2.50")})
        read = MongoDBClient._from_bson(stored)
        assert read["price"] * 4 == Decimal("10.00")


class TestMongoNestedReferencePath:
    """A dotted reference sourceKey descends into nested documents; lists unwind."""

    _DOC = {
        "id": 1000,
        "db_customer": [{"id": 1000, "db_address": [{"id": 7, "city": "Amory"}]}],
    }

    def test_plain_field(self):
        assert list(MongoDBClient._values_at_path(self._DOC, ["id"])) == [1000]

    def test_nested_single_level(self):
        assert list(MongoDBClient._values_at_path(self._DOC, ["db_customer", "id"])) == [1000]

    def test_nested_two_levels(self):
        assert list(MongoDBClient._values_at_path(self._DOC, ["db_customer", "db_address", "id"])) == [7]

    def test_list_unwinds_one_value_each(self):
        doc = {"a": [{"b": 1}, {"b": 2}, {"c": 3}]}
        assert list(MongoDBClient._values_at_path(doc, ["a", "b"])) == [1, 2]

    def test_missing_path_yields_nothing(self):
        assert list(MongoDBClient._values_at_path(self._DOC, ["nope", "id"])) == []
