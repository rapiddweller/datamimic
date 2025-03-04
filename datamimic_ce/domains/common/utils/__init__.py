# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Common utility functions and classes for the datamimic_ce package."""

from datamimic_ce.domains.common.utils.class_util import (
    create_dynamic_class,
    create_instance,
    create_instance_by_name,
    create_registered_instance,
    get_class,
    get_class_by_attribute,
    get_registered_classes,
    get_subclasses,
    register_class_factory,
)
from datamimic_ce.domains.common.utils.random_utils import (
    random_bool,
    random_element_with_exclusions,
    random_float_in_range,
    random_int_in_range,
    random_subset,
    shuffle_list,
    weighted_choice,
)

__all__ = [
    # Random utilities
    "weighted_choice",
    "random_subset",
    "random_bool",
    "random_int_in_range",
    "random_float_in_range",
    "random_element_with_exclusions",
    "shuffle_list",
    # Class factory utilities
    "create_instance",
    "get_class",
    "get_subclasses",
    "create_instance_by_name",
    "register_class_factory",
    "get_registered_classes",
    "create_registered_instance",
    "get_class_by_attribute",
    "create_dynamic_class",
]
