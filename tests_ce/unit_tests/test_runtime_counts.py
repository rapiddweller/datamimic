import random
from unittest.mock import MagicMock

from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.runtime.contexts.context import Context
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
from datamimic_ce.engine.runtime.counts import get_int_count, resolve_count
from datamimic_ce.engine.runtime.sources.router import has_mongodb_upsert_target


def test_get_int_count_handles_missing_digits_and_expression() -> None:
    context = MagicMock(spec=Context)
    context.evaluate_python_expression.return_value = 12

    assert get_int_count(None, context) is None
    assert get_int_count("42", context) == 42
    assert get_int_count("{value * 3}", context) == 12
    context.evaluate_python_expression.assert_called_once_with("value * 3")


def test_resolve_count_preserves_explicit_and_bounded_counts() -> None:
    rng = random.Random(7)

    assert resolve_count(4, 8, 9, rng) == 4
    assert resolve_count(None, 8, 9, rng) in range(8, 10)
    assert resolve_count(None, None, 3, rng) in range(0, 4)
    assert resolve_count(None, 3, None, rng) in range(3, 9)
    assert resolve_count(None, None, None, rng) is None


def test_has_mongodb_upsert_target_requires_upsert_operation_and_mongo_client() -> None:
    context = MagicMock(spec=SetupContext)
    context.get_client_by_id.return_value = MagicMock(spec=MongoDBClient)

    assert has_mongodb_upsert_target({"mongodb.upsert"}, context)
    assert not has_mongodb_upsert_target({"mongodb.delete"}, context)
    context.get_client_by_id.return_value = object()
    assert not has_mongodb_upsert_target({"mongodb.upsert"}, context)
