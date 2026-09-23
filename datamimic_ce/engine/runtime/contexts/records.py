from datamimic_ce.engine.dsl.api import NAME_SEPARATOR


def dict_nested_update(dictionary, key_path, value):
    """Update field of dictionary using key path."""
    keys = key_path.split(NAME_SEPARATOR)
    current_dict = dictionary

    for key in keys[:-1]:
        if key not in current_dict:
            current_dict[key] = {}
        current_dict = current_dict[key]

    current_dict[keys[-1]] = value
