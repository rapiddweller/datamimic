# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from __future__ import annotations  # Enable forward declarations

import calendar
import collections
import copy
import datetime
import functools
import itertools
import json
import math
import os
import random
import re
import statistics
import types
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import requests
from faker import Faker

if TYPE_CHECKING:
    from datamimic_ce.contexts.setup_context import SetupContext

# Create a safe evaluation environment
SAFE_GLOBALS = {
    "math": math,
    "random": random,
    "datetime": datetime,
    "uuid": uuid,
    "json": json,
    "os": os,
    "pd": pd,
    "np": np,
    "re": re,
    "calendar": calendar,
    "itertools": itertools,
    "functools": functools,
    "collections": collections,
    "statistics": statistics,
    "requests": requests,
    "fake": Faker(),
    "len": len,
    "range": range,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "sum": sum,
    "abs": abs,
    "max": max,
    "min": min,
    "round": round,
    "sorted": sorted,
    "map": map,
    "filter": filter,
    "reduce": functools.reduce,
    "all": all,
    "any": any,
    "bin": bin,
    "hex": hex,
    "oct": oct,
    "type": type,
    "hashlib": __import__("hashlib"),
    "base64": __import__("base64"),  # pair a binary payload with its b64/hex form in the DSL
    # Empty dict (not None) still blocks every builtin, but an unresolvable name now raises a
    # proper NameError carrying the identifier instead of TypeError('NoneType' not subscriptable)
    # — evaluate_python_expression turns that into an error saying WHICH name is missing.
    "__builtins__": {},
}

# The number-one authoring trap: bare record-local names only resolve at the top level.
# Appended to undefined-name errors so the failure itself teaches the scope rule.
_SCOPE_GUIDANCE = (
    "record-local names need this. inside nested <generate>/<nestedKey>; "
    "use parent./root. for enclosing records"
)

# List of special functions that define in SAFE_GLOBALS
SPECIAL_FUNCTION = {
    Faker,
}


class Context(ABC):
    def __init__(self, root_context: SetupContext):  # noqa: F821
        self._root = root_context
        self._statement_start_times: dict[str, float] = {}

    @property
    def root(self) -> SetupContext:  # noqa: F821
        return self._root

    @property
    @abstractmethod
    def rng(self) -> Any:
        """The rng for randomness driven by this context (Random or random module)."""

    @property
    def statement_start_times(self) -> dict[str, float]:
        return self._statement_start_times

    @statement_start_times.setter
    def statement_start_times(self, value: dict[str, float]) -> None:
        self._statement_start_times = value

    def evaluate_python_expression(self, expr: str, local_namespace: dict | None = None):
        """
        Get reference from current variables and attributes
        :param local_namespace:
        :param expr:
        :return:
        """
        current_context = self
        # Init data_dict with local_namespace
        data_dict = {} if local_namespace is None else copy.deepcopy(local_namespace)

        # Update data_dict with root context's properties'
        if current_context.root.properties is not None:
            data_dict.update(current_context.root.properties)

        # Update data_dict with current context's variables and products
        content_tree = self.get_content_variables_products(current_context)
        data_dict.update(content_tree)

        # Evaluate python expression, use dict of products and variables as local namespace
        # Convert namespace dict to dotable dict
        for key, value in data_dict.items():
            if isinstance(value, dict):
                data_dict[key] = DotableDict(value)

        # Canonical scope aliases, mirroring DATAMIMIC EE (bound only when not already a user name):
        #  - `this`: the current content scope, so `this.field` == bare `field` (essential in nested
        #    scopes where a bare sibling name is wrapped under the scope name and does not resolve).
        #  - `parent`: the immediate parent generate/nestedKey scope.
        #  - `root`: the full merged content tree from the outermost scope down (root.<field> / root.<name>.<field>).
        if "this" not in data_dict:
            data_dict["this"] = DotableDict(self._current_scope())
        if "parent" not in data_dict:
            parent_scope = self._parent_scope()
            if parent_scope:
                data_dict["parent"] = DotableDict(parent_scope)
        if "root" not in data_dict:
            data_dict["root"] = DotableDict(dict(content_tree))

        # Evaluate expression
        try:
            result = eval(expr, SAFE_GLOBALS, data_dict)

            if isinstance(result, DotableDict):
                return result.to_dict()
            elif isinstance(result, list):
                return [ele.to_dict() if isinstance(ele, DotableDict) else ele for ele in result]
            # check result is not function, class or module
            elif callable(result) or isinstance(result, types.ModuleType):
                raise ValueError(f"'{expr}' is an callable function, not a valid type (string, integer, float,...)")
            elif type(result) in SPECIAL_FUNCTION:
                raise ValueError(
                    f"'{expr}' is {type(result).__name__} function, not a valid type (string, integer, float,...)"
                )
            else:
                return result
        except NameError as e:
            # Same exception TYPE as before (ValueError) — only the message improves:
            # name the missing identifier and teach the scope rule.
            missing = e.name if e.name is not None else str(e)
            raise ValueError(
                f"Failed while evaluate '{expr}': name '{missing}' is not defined in this scope; {_SCOPE_GUIDANCE}"
            ) from e
        except AttributeError as e:
            # DotableDict raises this for a missing field on this./parent./root. (str(e)
            # already names it: "Cannot find attribute 'x'"); native ones carry e.name.
            missing_attr = f"missing attribute '{e.name}'" if e.name is not None else str(e)
            raise ValueError(f"Failed while evaluate '{expr}': {missing_attr}; {_SCOPE_GUIDANCE}") from e
        except KeyError as e:
            missing_key = e.args[0] if e.args else str(e)
            raise ValueError(f"Failed while evaluate '{expr}': missing key {missing_key!r}") from e
        except TypeError as e:
            raise ValueError(f"Failed while evaluate '{expr}': '{expr}' have undefined item or wrong structure") from e
        except SyntaxError as e:
            # special case with expr have ':' (example xml tag: 'gc:CodeList')
            if ":" in expr:
                # encode ':' character
                colon_replacement = "__"
                expr = expr.replace(r"\:", "__")

                def process_after_dot(match):
                    # After the first dot, replace all : with __
                    part_after_dot = match.group(1)
                    return "." + re.sub(r"[:]", "__", part_after_dot)

                # Find the first dot and apply the transformation
                expr = re.sub(r"\.(.*)", process_after_dot, expr)

                def recursion_data_dict(recursion_dict):
                    updated_dict = {}
                    for recursion_key, recursion_value in recursion_dict.items():
                        if isinstance(recursion_value, dict):
                            recursion_value = recursion_data_dict(recursion_value)
                        if isinstance(recursion_value, DotableDict):
                            recursion_value = DotableDict(recursion_data_dict(recursion_value.to_dict()))
                        updated_dict[recursion_key.replace(":", colon_replacement)] = recursion_value
                    return updated_dict

                updated_data_dict = recursion_data_dict(data_dict)
                try:
                    result = eval(expr, SAFE_GLOBALS, updated_data_dict)
                    if isinstance(result, DotableDict):
                        return result.to_dict()
                    elif isinstance(result, list):
                        return [ele.to_dict() if isinstance(ele, DotableDict) else ele for ele in result]
                    # check result is not function, class or module
                    elif callable(result) or isinstance(result, types.ModuleType):
                        raise ValueError(
                            f"'{expr}' is an callable function, not a valid type (string, integer, float,...)"
                        )
                    elif type(result) in SPECIAL_FUNCTION:
                        raise ValueError(
                            f"'{expr}' is {type(result).__name__} "
                            f"function, not a valid type (string, integer, float,...)"
                        )
                    else:
                        return result
                except Exception as err:
                    # decode ':' character
                    expr = expr.replace(colon_replacement, ":")
                    raise ValueError(
                        f"Evaluation error for expression '{expr}': "
                        "The expression may contain undefined items, improper structure, "
                        "or case-sensitive issues (e.g., using 'true' instead of 'True'). "
                        "Please double-check that all parameters and type notations are correct and supported."
                    ) from err
            else:
                raise ValueError(
                    f"Evaluation error for expression '{expr}': "
                    "The expression may contain undefined elements, formatting errors, "
                    "or unsupported parameter names. Ensure that boolean values and all parameter names "
                    "(e.g., 'True' vs 'true') adhere to the required formats."
                ) from e
        except Exception as e:
            #  Keep error reporting consistent; avoid extra stdout noise from traceback.print_exc()
            raise ValueError(f"Failed while evaluate '{expr}': {str(e)}") from e

    def _current_scope(self) -> dict:
        """The current content scope for the ``this`` alias: ``this.field`` resolves to the same value as
        bare ``field``. In a generate/iterate that is the record's variables + products (products win on a
        name clash); at setup level it is the setup namespace + global variables."""
        from datamimic_ce.contexts.geniter_context import GenIterContext
        from datamimic_ce.contexts.setup_context import SetupContext

        if isinstance(self, GenIterContext):
            return {**self.current_variables, **self.current_product}
        if isinstance(self, SetupContext):
            return {**self.namespace, **self.global_variables}
        return {}

    def _parent_scope(self) -> dict:
        """The immediate parent scope for the ``parent`` alias: the parent generate/nestedKey's
        variables + products. Empty when there is no enclosing generate scope (top-level = setup parent)."""
        from datamimic_ce.contexts.geniter_context import GenIterContext

        if not isinstance(self, GenIterContext):
            return {}
        parent = self.parent
        if isinstance(parent, GenIterContext):
            return {**parent.current_variables, **parent.current_product}
        return {}

    @staticmethod
    def get_content_variables_products(current_context: Context) -> dict:
        # Init current product of root context
        from datamimic_ce.contexts.geniter_context import GenIterContext
        from datamimic_ce.contexts.setup_context import SetupContext

        data_dict: dict = {}
        # SetupContext evaluate script
        if isinstance(current_context, SetupContext):
            # Add current variable & product of outermost context
            data_dict = {
                **current_context.namespace,
                **current_context.global_variables,
                **data_dict,
            }
        # GenIterContext evaluate script
        else:
            # Nested wrapping tree: each scope holds its child scope under the child's name, so a
            # qualified path like `orders.line_items.product.field` resolves; the outermost scope's
            # own vars land at the top level and the setup namespace/globals merge in.
            self_context = current_context
            self_is_outermost = False
            while isinstance(current_context, GenIterContext):
                parent_context = current_context.parent
                if isinstance(parent_context, SetupContext):
                    data_dict = {
                        **parent_context.namespace,
                        **parent_context.global_variables,
                        **current_context.current_variables,
                        **current_context.current_product,
                        **data_dict,
                    }
                    self_is_outermost = current_context is self_context
                    break
                data_dict = {
                    current_context.current_name: {
                        **current_context.current_variables,
                        **current_context.current_product,
                        **data_dict,
                    }
                }
                current_context = parent_context
            # The scope evaluating THIS script also resolves its own variables/products by bare
            # name, not only nested under its own scope name (mirrors what `this.` already exposes -
            # a sibling <variable> feeding a <key> script in the same nested scope). Only self, not
            # every ancestor: an ancestor's bare name still needs this./parent./root., so a name
            # collision between scopes at different depths can't silently flip which value a bare
            # reference resolves to.
            if not self_is_outermost and isinstance(self_context, GenIterContext):
                data_dict = {**data_dict, **self_context.current_variables, **self_context.current_product}

        return data_dict


class DotableDict:
    """
    Dotable presentation of dict
    """

    def __init__(self, dictionary: dict):
        self._dictionary = dictionary

    def __getattr__(self, name):
        if name in self._dictionary:
            item = self._dictionary[name]
            if isinstance(item, dict):
                return DotableDict(item)
            elif isinstance(item, list):
                return [DotableDict(x) if isinstance(x, dict) else x for x in item]
            else:
                return item
        else:
            raise AttributeError(f"Cannot find attribute '{name}'")

    def get(self, name):
        return getattr(self, name)

    def to_dict(self):
        """
        Convert DotableDict to dict
        :return:
        """
        return self._dictionary

    def keys(self):
        return self._dictionary.keys()
