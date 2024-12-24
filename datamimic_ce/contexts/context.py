# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
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
from abc import ABC
from typing import TYPE_CHECKING

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
    "__builtins__": None,
}

# List of special functions that define in SAFE_GLOBALS
SPECIAL_FUNCTION = {
    Faker,
}


class Context(ABC):  # noqa: B024
    def __init__(self, root_context: SetupContext):  # noqa: F821
        self._root = root_context
        self._statement_start_times: dict[str, float] = {}

    @property
    def root(self) -> SetupContext:  # noqa: F821
        return self._root

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
        data_dict.update(self.get_content_variables_products(current_context))

        # Evaluate python expression, use dict of products and variables as local namespace
        # Convert namespace dict to dotable dict
        for key, value in data_dict.items():
            if isinstance(value, dict):
                data_dict[key] = DotableDict(value)

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
        except TypeError as e:
            raise ValueError(f"Failed while evaluate '{expr}': '{expr}' have undefined item or wrong structure") from e
        except Exception as e:
            raise ValueError(f"Failed while evaluate '{expr}': {str(e)}") from e

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
            while isinstance(current_context, GenIterContext):
                parent_context = current_context.parent

                if isinstance(parent_context, SetupContext):
                    # Add current variable & product of outermost context
                    data_dict = {
                        **parent_context.namespace,
                        **parent_context.global_variables,
                        **current_context.current_variables,
                        **current_context.current_product,
                        **data_dict,
                    }
                    break
                # Update current data_dict with current context variable & product
                data_dict = {
                    current_context.current_name: {
                        **current_context.current_variables,
                        **current_context.current_product,
                        **data_dict,
                    }
                }
                current_context = parent_context

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
