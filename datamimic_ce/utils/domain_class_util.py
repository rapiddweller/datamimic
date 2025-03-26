# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Compatibility module for the ClassFactoryUtil class.

This module provides backward compatibility with the old ClassFactoryUtil class.
"""

import importlib
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class DomainClassUtil:
    """
    Utility class for creating instances of classes in the domain package.

    """

    @staticmethod
    def create_instance(class_path: str, **kwargs: Any) -> Any:
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
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        class_obj = getattr(module, class_name)
        return class_obj(**kwargs)

    @staticmethod
    def get_class(class_path: str) -> type:
        """Get a class by its fully qualified path.

        Args:
            class_path: The fully qualified path to the class (e.g., 'package.module.ClassName').

        Returns:
            The class object.

        Raises:
            ImportError: If the module cannot be imported.
            AttributeError: If the class does not exist in the module.
        """
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @staticmethod
    def get_subclasses(base_class: type[T], include_abstract: bool = False) -> list[type[T]]:
        """Get all subclasses of a base class.

        Args:
            base_class: The base class to find subclasses of.
            include_abstract: Whether to include abstract classes in the result.

        Returns:
            A list of subclasses.
        """
        all_subclasses = []
        for subclass in base_class.__subclasses__():
            if include_abstract or not inspect.isabstract(subclass):
                all_subclasses.append(subclass)
            all_subclasses.extend(DomainClassUtil.get_subclasses(subclass, include_abstract))
        return all_subclasses

    @staticmethod
    def create_instance_by_name(class_dict: dict[str, type[T]], name: str, **kwargs: Any) -> T:
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
        if name not in class_dict:
            raise KeyError(
                f"Class name '{name}' not found in class dictionary. Available options: {list(class_dict.keys())}"
            )

        return class_dict[name](**kwargs)

    @staticmethod
    def get_class_by_attribute(classes: list[type], attribute_name: str, attribute_value: Any) -> type | None:
        """Find a class by checking if it has an attribute with a specific value.

        Args:
            classes: List of classes to search through.
            attribute_name: The name of the attribute to check.
            attribute_value: The value the attribute should have.

        Returns:
            The matching class, or None if no match is found.
        """
        for cls in classes:
            if hasattr(cls, attribute_name) and getattr(cls, attribute_name) == attribute_value:
                return cls
        return None

    @staticmethod
    def create_dynamic_class(name: str, bases: tuple = (object,), attributes: dict[str, Any] | None = None) -> type:
        """Create a new class dynamically.

        Args:
            name: The name of the new class.
            bases: A tuple of base classes.
            attributes: A dictionary of attributes to add to the class.

        Returns:
            The newly created class.
        """
        if attributes is None:
            attributes = {}

        return type(name, bases, attributes)

    @staticmethod
    def register_class_factory(base_class: type[T]) -> Callable[[type[T]], type[T]]:
        """A decorator to register a class with a factory.

        Args:
            base_class: The base class that the factory is for.

        Returns:
            A decorator function that registers the class.
        """
        if not hasattr(base_class, "_registered_classes"):
            base_class._registered_classes = {}  # type: ignore

        def decorator(cls: type[T]) -> type[T]:
            base_class._registered_classes[cls.__name__] = cls  # type: ignore
            return cls

        return decorator

    @staticmethod
    def get_registered_classes(base_class: type[T]) -> dict[str, type[T]]:
        """Get all classes registered with a base class.

        Args:
            base_class: The base class to get registered classes for.

        Returns:
            A dictionary mapping class names to class types.
        """
        if not hasattr(base_class, "_registered_classes"):
            base_class._registered_classes = {}  # type: ignore

        return base_class._registered_classes  # type: ignore

    @staticmethod
    def create_registered_instance(base_class: type[T], name: str, **kwargs: Any) -> T:
        """Create an instance of a registered class.

        Args:
            base_class: The base class that the factory is for.
            name: The name of the class to instantiate.
            **kwargs: Keyword arguments to pass to the class constructor.

        Returns:
            An instance of the specified class.

        Raises:
            KeyError: If the name is not found in the registered classes.
        """
        registered_classes = DomainClassUtil.get_registered_classes(base_class)
        return DomainClassUtil.create_instance_by_name(registered_classes, name, **kwargs)
