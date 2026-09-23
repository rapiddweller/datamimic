from datamimic_ce.engine.dsl.api import EntityValue
from datamimic_ce.engine.io.clients.entity_serialization import stringify_entity_value


class EntityLike(EntityValue):
    def to_dict(self) -> dict[str, object]:
        return {"name": "Ada", "active": True}


def test_stringify_entity_value_uses_explicit_to_dict_protocol() -> None:
    assert stringify_entity_value(EntityLike()) == "{'name': 'Ada', 'active': True}"


def test_stringify_entity_value_leaves_other_values_unchanged() -> None:
    value = {"name": "Ada"}

    assert stringify_entity_value(value) is value


def test_stringify_entity_value_does_not_convert_unrelated_to_dict_objects() -> None:
    class Unrelated:
        def to_dict(self) -> dict[str, object]:
            return {"name": "Ada"}

    value = Unrelated()

    assert stringify_entity_value(value) is value
