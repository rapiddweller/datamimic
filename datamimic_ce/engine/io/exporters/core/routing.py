# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

import ast
from collections.abc import Mapping

from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import META_TARGET_ENTITY, META_TYPE
from datamimic_ce.engine.dsl.vocabulary.enums.operation_enums import ExportOperation
from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.clients.operations import is_mongodb_client


def resolve_target_entity(target_entity: str | None, type_: str | None, name: str) -> str:
    """Resolve output entity: targetEntity, type, then name."""
    return target_entity or type_ or name


def resolve_target_entity_from_metadata(name: str, metadata: dict | None) -> str:
    """Resolve an output entity from exporter metadata."""
    md = metadata or {}
    return resolve_target_entity(md.get(META_TARGET_ENTITY), md.get(META_TYPE), name)


def has_mongodb_upsert_target(targets: set[str], clients: Mapping[str, Client]) -> bool:
    for target in targets:
        if "." in target:
            consumer, operation = target.split(".", 1)
            if operation == ExportOperation.UPSERT.value and is_mongodb_client(clients.get(consumer)):
                return True
    return False


def parse_function_string(function_string: str) -> list[dict]:
    parsed_functions: list[dict] = []
    if function_string.strip() == "" or all(char in ", " for char in function_string):
        return parsed_functions

    try:
        module = ast.parse(f"[{function_string}]", mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Error parsing function string: {e}") from e

    if not isinstance(module.body, ast.List):
        raise ValueError("Function string is not a valid list of function calls.")

    for element in module.body.elts:
        if isinstance(element, ast.Call):
            if isinstance(element.func, ast.Name):
                function_name = element.func.id
            elif isinstance(element.func, ast.Attribute):
                parts = []
                current_func: ast.expr = element.func
                while isinstance(current_func, ast.Attribute):
                    parts.append(current_func.attr)
                    current_func = current_func.value
                if isinstance(current_func, ast.Name):
                    parts.append(current_func.id)
                function_name = ".".join(reversed(parts))
            else:
                raise ValueError("Unsupported function type in function call.")

            params: dict = {}
            for keyword in element.keywords:
                key = keyword.arg
                try:
                    value = ast.literal_eval(keyword.value)
                except (ValueError, SyntaxError):
                    raise ValueError(f"Non-literal parameter found: {keyword.value}") from None
                params[key] = value

            parsed_functions.append({"function_name": function_name, "params": params})
        elif isinstance(element, ast.Attribute):
            parts = []
            current_attr: ast.expr = element
            while isinstance(current_attr, ast.Attribute):
                parts.append(current_attr.attr)
                current_attr = current_attr.value
            if isinstance(current_attr, ast.Name):
                parts.append(current_attr.id)
            function_name = ".".join(reversed(parts))
            parsed_functions.append({"function_name": function_name, "params": None})
        elif isinstance(element, ast.Name):
            parsed_functions.append({"function_name": element.id, "params": None})
        elif isinstance(element, ast.Constant):
            parsed_functions.append({"function_name": element.value, "params": None})
        else:
            try:
                value = ast.literal_eval(element)
                parsed_functions.append({"function_name": str(value), "params": None})
            except Exception:
                raise ValueError("Unsupported expression in function string.") from None

    return parsed_functions
