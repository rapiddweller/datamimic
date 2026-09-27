"""Serialization shared by exporters and Runtime's per-page export path."""


def convert_xml_dict_to_json_dict(xml_dict: dict[str, object]) -> object:
    """Convert XML dictionaries with ``#text`` and ``@attribute`` keys to rows."""
    if "#text" in xml_dict:
        return xml_dict["#text"]

    result: dict[str, object] = {}
    for key, value in xml_dict.items():
        if key.startswith("@"):
            continue
        if isinstance(value, dict):
            result[key] = convert_xml_dict_to_json_dict(value)
        elif isinstance(value, list):
            result[key] = [convert_xml_dict_to_json_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result
