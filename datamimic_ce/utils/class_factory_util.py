# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Compatibility module for the ClassFactoryUtil class.

This module provides backward compatibility with the old ClassFactoryUtil class.
"""

from typing import Any, TypeVar

from datamimic_ce.domains.common.utils.class_factory_util import (
    create_dynamic_class,
    create_instance,
    create_instance_by_name,
    get_class,
    get_class_by_attribute,
    get_subclasses,
)

T = TypeVar("T")


class ClassFactoryUtil:
    """
    Compatibility class for the old ClassFactoryUtil class.

    This class provides backward compatibility with the old ClassFactoryUtil class.
    It delegates to the new utility functions in datamimic_ce.domains.common.utils.class_factory_util.
    """

    def create_instance(self, class_path: str, **kwargs: Any) -> Any:
        """Create an instance of a class specified by its fully qualified path.

        Args:
            class_path: The fully qualified path to the class (e.g., 'package.module.ClassName').
            **kwargs: Keyword arguments to pass to the class constructor.

        Returns:
            An instance of the specified class.

        Raises:
            ImportError: If the module cannot be imported.
            AttributeError: If the class does not exist in the module.
        """
        return create_instance(class_path, **kwargs)

    def get_class(self, class_path: str) -> type:
        """Get a class by its fully qualified path.

        Args:
            class_path: The fully qualified path to the class (e.g., 'package.module.ClassName').

        Returns:
            The class object.

        Raises:
            ImportError: If the module cannot be imported.
            AttributeError: If the class does not exist in the module.
        """
        return get_class(class_path)

    def get_subclasses(self, base_class: type[T], include_abstract: bool = False) -> list[type[T]]:
        """Get all subclasses of a base class.

        Args:
            base_class: The base class to find subclasses of.
            include_abstract: Whether to include abstract classes in the result.

        Returns:
            A list of subclasses.
        """
        return get_subclasses(base_class, include_abstract)

    def create_instance_by_name(self, class_dict: dict[str, type[T]], name: str, **kwargs: Any) -> T:
        """Create an instance of a class from a dictionary of classes, using a name key.

        Args:
            class_dict: A dictionary mapping names to class types.
            name: The name of the class to instantiate.
            **kwargs: Keyword arguments to pass to the class constructor.

        Returns:
            An instance of the specified class.

        Raises:
            KeyError: If the name is not found in the class dictionary.
        """
        return create_instance_by_name(class_dict, name, **kwargs)

    def get_class_by_attribute(self, classes: list[type], attribute_name: str, attribute_value: Any) -> type | None:
        """Find a class by checking if it has an attribute with a specific value.

        Args:
            classes: List of classes to search through.
            attribute_name: The name of the attribute to check.
            attribute_value: The value the attribute should have.

        Returns:
            The matching class, or None if no match is found.
        """
        return get_class_by_attribute(classes, attribute_name, attribute_value)

    def create_dynamic_class(
        self, name: str, bases: tuple = (object,), attributes: dict[str, Any] | None = None
    ) -> type:
        """Create a new class dynamically.

        Args:
            name: The name of the new class.
            bases: A tuple of base classes.
            attributes: A dictionary of attributes to add to the class.

        Returns:
            The newly created class.
        """
        return create_dynamic_class(name, bases, attributes)
