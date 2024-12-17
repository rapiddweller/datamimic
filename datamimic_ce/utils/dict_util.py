# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy

from datamimic_ce.constants.convention_constants import NAME_SEPARATOR


def dict_nested_update(dictionary, key_path, value):
    """
    Update field of dictionary using key path
    :param dictionary:
    :param key_path:
    :param value:
    :return:
    """
    keys = key_path.split(NAME_SEPARATOR)
    current_dict = dictionary

    for k in keys[:-1]:
        if k not in current_dict:
            current_dict[k] = {}
        current_dict = current_dict[k]

    current_dict[keys[-1]] = value


def sanitize_dict(input_dict: dict) -> dict:
    """
    Replace sensitive information with asterisks
    :param input_dict:
    :return:
    """
    output_dict = copy.deepcopy(input_dict)
    for key, value in output_dict.items():
        if isinstance(value, dict):
            output_dict[key] = sanitize_dict(value)
        elif isinstance(value, str) and ("password" in key.lower() or "token" in key.lower()):
            output_dict[key] = "********"
    return output_dict
