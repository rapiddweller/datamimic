# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod


class ConnectionConfig(ABC):
    """
    Abstract base class for connection configurations.

    This class serves as a base class for different types of connection configurations.
    It inherits from Python's built-in ABC (Abstract Base Class) module,
    which allows the creation of abstract base classes.
    """

    @abstractmethod
    def check_connection_config(self):
        """
        Check the connection configuration.

        This method should be implemented by subclasses to check the connection configuration.
        """

    @abstractmethod
    def get_connection_config(self):
        """
        Returns the connection configuration.

        This method should be implemented by subclasses to return the connection configuration.
        """
