# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Interfaces for domain-driven design components.

This module provides interfaces for generators, repositories, and services
to be implemented by domain-specific components.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T")  # Define a type variable for generic typing
E = TypeVar("E")  # Entity type variable


class Generator(Protocol, Generic[T]):
    """Interface for generators that produce values of type T."""

    @abstractmethod
    def generate(self, *args, **kwargs) -> T:
        """Generate a value of type T.

        Args:
            *args: Positional arguments for generation
            **kwargs: Keyword arguments for generation

        Returns:
            A generated value of type T
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the generator's internal state."""
        pass


class Repository(Protocol, Generic[E]):
    """Interface for repositories that manage entities of type E."""

    @abstractmethod
    def get(self, id: str) -> E | None:
        """Get an entity by ID.

        Args:
            id: The ID of the entity to retrieve

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, entity: E) -> None:
        """Save an entity.

        Args:
            entity: The entity to save
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete an entity by ID.

        Args:
            id: The ID of the entity to delete
        """
        pass

    @abstractmethod
    def list(self, **filters) -> list[E]:
        """List entities matching the given filters.

        Args:
            **filters: Filters to apply

        Returns:
            A list of matching entities
        """
        pass


class Service(ABC):
    """Base interface for domain services."""

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the service operation.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the service operation
        """
        pass


class DataLoader(Protocol):
    """Interface for data loaders."""

    @abstractmethod
    def get_data(self, data_type: str, country_code: str = "US") -> list[tuple[str, float]]:
        """Get data for a specific type and country code.

        Args:
            data_type: The type of data to retrieve
            country_code: The country code to use

        Returns:
            A list of tuples containing values and weights
        """
        pass
