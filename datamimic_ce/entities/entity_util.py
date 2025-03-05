# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")  # Define a type variable for generic typing


class FieldGenerator(Generic[T]):
    """
    A class to generate field values with caching and reset capabilities.

    This class wraps a generator function and provides methods to get and reset generated values.
    """

    def __init__(self, generator_fn: Callable[..., T]):
        """
        Initialize the FieldGenerator with a generator function.

        Args:
            generator_fn: A function that generates field values when called
        """
        self._generator_fn = generator_fn
        self._cached_value: T | None = None
        self._cached = False

    def get(self, *args, **kwargs) -> T | None:
        """
        Get the generated value, either from cache or by calling the generator function.

        Args:
            *args: Positional arguments to pass to the generator function
            **kwargs: Keyword arguments to pass to the generator function

        Returns:
            The generated value
        """
        if not self._cached:
            self._cached_value = self._generator_fn(*args, **kwargs)
            self._cached = True
        return self._cached_value  # Return the cached value, which might be None

    def reset(self):
        """
        Reset the cached value so that the next get() call will generate a new value.
        """
        self._cached = False
        self._cached_value = None

    def force_regenerate(self, *args, **kwargs) -> T | None:
        """
        Force regeneration of the value even if it's cached.

        Args:
            *args: Positional arguments to pass to the generator function
            **kwargs: Keyword arguments to pass to the generator function

        Returns:
            The newly generated value
        """
        self._cached = False
        return self.get(*args, **kwargs)


class EntityUtil:
    """
    Utility class for entity-related operations.

    This class provides static methods to handle entity field generation and management.
    """

    @staticmethod
    def create_field_generator_dict(generator_fn_dict: dict[str, Callable[..., Any]]) -> dict[str, FieldGenerator]:
        """
        Create a dictionary of FieldGenerator instances from a dictionary of generator functions.

        Args:
            generator_fn_dict: A dictionary mapping field names to generator functions

        Returns:
            A dictionary mapping field names to FieldGenerator instances
        """
        field_generator_dict = {}
        for key, generator_fn in generator_fn_dict.items():
            field_generator_dict[key] = FieldGenerator(generator_fn)
        return field_generator_dict

    @staticmethod
    def batch_generate_fields(
        field_generators: dict[str, FieldGenerator], field_names: list[str], count: int = 100
    ) -> list[dict[str, Any]]:
        """
        Generate a batch of field values efficiently.

        This method generates multiple sets of fields in one go, which is more
        efficient than generating them one by one.

        Args:
            field_generators: Dictionary of field generators
            field_names: List of field names to generate
            count: Number of sets to generate

        Returns:
            List of dictionaries containing generated field values
        """
        results = []

        for _ in range(count):
            # Generate a new set of field values
            field_values = {}
            for field_name in field_names:
                if field_name in field_generators:
                    field_values[field_name] = field_generators[field_name].force_regenerate()

            results.append(field_values)

        return results
