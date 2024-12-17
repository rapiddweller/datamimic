# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod


class BaseClassFactoryUtil(ABC):
    """
    Abstract base class for utility classes that provide various functionalities.

    This class defines a set of abstract static methods that must be implemented
    by any subclass. These methods are intended to return specific utility classes
    or generators used in the application.
    """

    @staticmethod
    @abstractmethod
    def get_task_util_cls():
        """
        Abstract method to get the task utility class.

        Returns:
            The task utility class.
        """

    @staticmethod
    @abstractmethod
    def get_data_generation_util():
        """
        Abstract method to get the data generation utility.

        Returns:
            The data generation utility.
        """

    @staticmethod
    @abstractmethod
    def get_datetime_generator():
        """
        Abstract method to get the datetime generator.

        Returns:
            The datetime generator.
        """

    @staticmethod
    @abstractmethod
    def get_integer_generator():
        """
        Abstract method to get the integer generator.

        Returns:
            The integer generator.
        """

    @staticmethod
    @abstractmethod
    def get_string_generator():
        """
        Abstract method to get the string generator.

        Returns:
            The string generator.
        """

    @staticmethod
    @abstractmethod
    def get_exporter_util():
        """
        Abstract method to get the exporter utility.

        Returns:
            The exporter utility.
        """

    @staticmethod
    @abstractmethod
    def get_parser_util_cls():
        """
        Abstract method to get the parser utility class.

        Returns:
            The parser utility class.
        """

    @staticmethod
    @abstractmethod
    def get_datasource_util_cls():
        """
        Abstract method to get the datasource utility class.

        Returns:
            The datasource utility class.
        """

    @staticmethod
    @abstractmethod
    def get_setup_logger_func():
        """
        Abstract method to get the setup logger function.

        Returns:
            The setup logger function.
        """

    @staticmethod
    @abstractmethod
    def get_app_settings():
        """
        Abstract method to get the app settings.

        Returns:
            The app settings.
        """
