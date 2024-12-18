# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod
from datetime import datetime


class BaseDataGenerationUtil(ABC):
    """
    Abstract base class for data generation utilities.

    This class defines a set of abstract static methods that must be implemented
    by any subclass. These methods are intended to provide various data generation
    functionalities.
    """

    @staticmethod
    @abstractmethod
    def generate_random_value_based_on_type(
        data_type: str | None = None,
    ) -> str | int | bool | float:
        """
        Generate a random value based on the specified data type.

        Args:
            data_type (Optional[str]): The type of data to generate. Can be 'str', 'int', 'bool', or 'float'.

        Returns:
            Union[str, int, bool, float]: The generated random value.
        """

    @staticmethod
    @abstractmethod
    def rnd_str_from_regex(pattern: str) -> str:
        """
        Generate a random string based on the provided regex pattern.

        Args:
            pattern (str): The regex pattern to generate the string from.

        Returns:
            str: The generated random string.
        """

    @staticmethod
    @abstractmethod
    def convert_string_to_datetime(value: str, in_date_format: str) -> datetime:
        """
        Convert a string to a datetime object based on the provided date format.

        Args:
            value (str): The string to convert.
            in_date_format (str): The format of the input date string.

        Returns:
            datetime: The converted datetime object.
        """

    @staticmethod
    @abstractmethod
    def convert_datetime_to_string(value: datetime, out_date_format: str) -> str:
        """
        Convert a datetime object to a string based on the provided date format.

        Args:
            value (datetime): The datetime object to convert.
            out_date_format (str): The format of the output date string.

        Returns:
            str: The converted date string.
        """

    @staticmethod
    @abstractmethod
    def generate_credit_card_number(locale: str) -> str:
        """
        Generate a random credit card number for the specified locale.

        Args:
            locale (str): The locale for which to generate the credit card number.

        Returns:
            str: The generated credit card number.
        """

    @staticmethod
    @abstractmethod
    def generate_card_holder(locale: str) -> str:
        """
        Generate a random card holder name for the specified locale.

        Args:
            locale (str): The locale for which to generate the card holder name.

        Returns:
            str: The generated card holder name.
        """

    @staticmethod
    @abstractmethod
    def generate_cvc_number() -> str:
        """
        Generate a random CVC number.

        Returns:
            str: The generated CVC number.
        """

    @staticmethod
    @abstractmethod
    def generate_expiration_date(locale: str) -> str:
        """
        Generate a random expiration date for the specified locale.

        Args:
            locale (str): The locale for which to generate the expiration date.

        Returns:
            str: The generated expiration date.
        """

    @staticmethod
    @abstractmethod
    def rnd_int(min_val: int, max_val: int) -> int:
        """
        Generate a random integer between the specified minimum and maximum values.

        Args:
            min_val (int): The minimum value.
            max_val (int): The maximum value.

        Returns:
            int: The generated random integer.
        """

    @staticmethod
    @abstractmethod
    def rnd_str(
        char_set: str,
        min_val: int,
        max_val: int,
        unique: bool,
        prefix: str,
        suffix: str,
    ) -> str:
        """
        Generate a random string based on the specified parameters.

        Args:
            char_set (str): The set of characters to use for generating the string.
            min_val (int): The minimum length of the string.
            max_val (int): The maximum length of the string.
            unique (bool): Whether the string should be unique.
            prefix (str): The prefix to add to the generated string.
            suffix (str): The suffix to add to the generated string.

        Returns:
            str: The generated random string.
        """
