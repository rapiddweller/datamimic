from datamimic_ce.engine.dsl.contracts import EntityValue


def stringify_entity_value(value: object) -> object:
    if isinstance(value, EntityValue):
        return str(value.to_dict())
    return value
