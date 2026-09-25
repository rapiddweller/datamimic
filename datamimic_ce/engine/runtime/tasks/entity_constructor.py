"""Parse the constructor form used by DSL domain entities."""

from ast import literal_eval


def _parse_constructor_string(constructor_string: str) -> tuple[str, dict[str, object]]:
    constructor_string = constructor_string.strip()
    opening = constructor_string.find("(")
    closing = constructor_string.rfind(")")

    if opening == -1:
        return constructor_string, {}

    entity_name = constructor_string[:opening].strip()
    parameters_string = constructor_string[opening + 1 : closing].strip() if closing != -1 else ""
    parameters: dict[str, object] = {}
    for parameter in parameters_string.split(","):
        if "=" in parameter:
            key_value = parameter.split("=")
            if len(key_value) == 2:
                key, value = key_value
                try:
                    parameters[key.strip()] = literal_eval(value.strip())
                except (ValueError, SyntaxError):
                    parameters[key.strip()] = value.strip()
    return entity_name, parameters
