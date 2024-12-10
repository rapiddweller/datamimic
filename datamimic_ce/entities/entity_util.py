# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Callable


class FieldGenerator:
    """
    A class to generate and cache a value using a provided function.

    Attributes:
        _is_generated (bool): Indicates if the value has been generated.
        _value (Any): The generated value.
        _gen_fn (Callable): The function used to generate the value.
    """

    def __init__(self, generate_fn: Callable):
        """
        Initialize the FieldGenerator with a generation function.

        Args:
            generate_fn (Callable): The function to generate the value.
        """
        self._is_generated = False
        self._value = None
        self._gen_fn = generate_fn

    def get(self, *args):
        """
        Get the generated value, generating it if necessary.

        Args:
            *args: Arguments to pass to the generation function.

        Returns:
            Any: The generated value.
        """
        if not self._is_generated:
            self._value = self._gen_fn(*args)
            self._is_generated = True
        return self._value

    def reset(self):
        """
        Reset the generated value, allowing it to be generated again.
        """
        self._is_generated = False
        self._value = None


class EntityUtil:
    """
    Utility class for creating field generators.
    """

    @staticmethod
    def create_field_generator_dict(generator_fn_dict: dict) -> dict:
        """
        Create a dictionary of FieldGenerators from a dictionary of generation functions.

        Args:
            generator_fn_dict (Dict): A dictionary where keys are field names and values are generation functions.

        Returns:
            Dict: A dictionary where keys are field names and values are FieldGenerators.
        """
        field_generator = {}
        for key, val in generator_fn_dict.items():
            field_generator[key] = FieldGenerator(val)
        return field_generator
