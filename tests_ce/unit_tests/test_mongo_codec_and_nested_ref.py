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


class TestMongoShellToJson:
    """Migrated legacy mongo selectors use shell syntax (bareword keys, $-operators, single quotes)."""

    def test_find_with_bareword_projection(self):
        import json

        q = "find: 'db_product', filter: {}, projection: {_id: 0, ean_code: 1, price: 1}"
        r = json.loads(MongoDBClient._shell_to_json(q))
        assert r["find"] == "db_product"
        assert r["projection"] == {"_id": 0, "ean_code": 1, "price": 1}

    def test_aggregate_pipeline_with_unquoted_project_and_trailing_cursor(self):
        import json

        q = (
            "'aggregate': 'db_order_item', pipeline: ["
            "{'$match': {'order_id': {'$eq': 1000}}}, "
            "{'$group': {'_id': 1000, 'sum': {'$sum': '$total_price'}}}, "
            "{$project: {_id: 0, sum: 1}}], cursor: {} "
        )
        r = json.loads(MongoDBClient._shell_to_json(q))
        assert r["aggregate"] == "db_order_item"
        assert len(r["pipeline"]) == 3
        assert r["pipeline"][2] == {"$project": {"_id": 0, "sum": 1}}
        # a field-reference value keeps its $ and is not mangled into a key
        assert r["pipeline"][1]["$group"]["sum"]["$sum"] == "$total_price"

    def test_already_quoted_keys_untouched(self):
        import json

        r = json.loads(MongoDBClient._shell_to_json("find: 'c', filter: {'x': 1}, projection: {'y': 1}"))
        assert r["filter"] == {"x": 1} and r["projection"] == {"y": 1}


class TestMongoReferenceSortKey:
    """Reference row order must stay numeric, not lexicographic ("10" before "2")."""

    def test_multi_digit_ints_sort_numerically(self):
        rows = [(10,), (2,), (1,), (11,), (3,)]
        assert sorted(rows, key=lambda row: tuple(MongoDBClient._sort_key(v) for v in row)) == [
            (1,),
            (2,),
            (3,),
            (10,),
            (11,),
        ]

    def test_none_sorts_last(self):
        rows = [(5,), (None,), (1,)]
        assert sorted(rows, key=lambda row: tuple(MongoDBClient._sort_key(v) for v in row)) == [(1,), (5,), (None,)]


class TestMongoQueryTypeDetection:
    """The command key may be bareword OR quoted across migrated legacy selectors."""

    def test_bareword_find(self):
        assert MongoDBClient._check_query_type("find: 'c', filter: {}") == "find"

    def test_quoted_aggregate(self):
        # the shop-mongodb update selector single-quotes the key: 'aggregate': ...
        q = "'aggregate': 'db_order_item', pipeline: [{'$match': {}}]"
        assert MongoDBClient._check_query_type(q) == "aggregate"

    def test_double_quoted_find(self):
        assert MongoDBClient._check_query_type('"find": "c", filter: {}') == "find"

    def test_unknown_command_rejected(self):
        import pytest

        with pytest.raises(ValueError, match="only support"):
            MongoDBClient._check_query_type("delete: 'c'")

    def test_nested_field_named_find_is_not_the_command(self):
        # a real parse only looks at depth-0 keys; a substring-count regex would see two 'find's
        q = "aggregate: 'c', pipeline: [{'$project': {find: 1}}]"
        assert MongoDBClient._check_query_type(q) == "aggregate"


class TestMongoTopLevelKeys:
    """A single depth-aware pass over the selector replaces three independent regexes
    (type sniffing, duplicate-key counting) that each separately guessed at quote style."""

    def test_bareword_keys(self):
        assert MongoDBClient._top_level_keys("find: 'c', filter: {}, projection: {}") == [
            "find",
            "filter",
            "projection",
        ]

    def test_single_and_double_quoted_keys(self):
        assert MongoDBClient._top_level_keys("'find': 'c', \"filter\": {}") == ["find", "filter"]

    def test_nested_keys_are_not_top_level(self):
        # 'find' and 'filter' inside the pipeline value must not count as top-level keys
        q = "aggregate: 'c', pipeline: [{'$match': {'find': 1, 'filter': 2}}]"
        assert MongoDBClient._top_level_keys(q) == ["aggregate", "pipeline"]

    def test_duplicate_top_level_key_regardless_of_quote_style(self):
        assert MongoDBClient._top_level_keys("find: 'a', 'find': 'b', filter: {}") == ["find", "find", "filter"]

    def test_colon_and_comma_inside_quoted_value_are_not_structural(self):
        # a string value containing ':' and ',' must not be mistaken for a key boundary
        q = "find: 'c', filter: {'name': 'a, b: c'}, projection: {}"
        assert MongoDBClient._top_level_keys(q) == ["find", "filter", "projection"]

    def test_bracket_pipeline_value_does_not_leak_keys(self):
        assert MongoDBClient._top_level_keys("aggregate: 'c', pipeline: [], cursor: {}") == [
            "aggregate",
            "pipeline",
            "cursor",
        ]
