# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# """
# Base entity class for all domain entities.

# This module provides a base class with common functionality for all domain entities.
# """

# from abc import ABC, abstractmethod
# from typing import Any, ClassVar, TypeVar

# T = TypeVar("T")  # Define a type variable for generic typing


# class BaseEntity(ABC):
#     """Base class for all domain entities.

#     This class provides common functionality for all domain entities, including
#     initialization with locale and dataset, and abstract methods for resetting
#     and converting to dictionary.
#     """

#     # Class-level cache for shared data
#     _DATA_CACHE: ClassVar[dict[str, Any]] = {}

#     def __init__(self, locale: str = "en", dataset: str | None = None):
#         """Initialize the base entity.

#         Args:
#             locale: The locale to use for generating data.
#             dataset: The dataset to use for generating data.
#         """
#         self._locale = locale  # Preserve the full locale string
#         self._dataset = dataset

#     @abstractmethod
#     def reset(self) -> None:
#         """Reset all field generators, causing new values to be generated on the next access."""
#         pass

#     @abstractmethod
#     def to_dict(self) -> dict[str, Any]:
#         """Convert the entity to a dictionary containing all properties.

#         Returns:
#             A dictionary containing all properties of the entity.
#         """
#         pass

#     def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
#         """Generate a batch of entities.

#         Args:
#             count: The number of entities to generate.

#         Returns:
#             A list of dictionaries containing the generated entities.
#         """
#         result = []
#         for _ in range(count):
#             # Get the entity as a dictionary
#             entity_dict = self.to_dict()
#             result.append(entity_dict)
#             # Reset the entity for the next iteration
#             self.reset()
#         return result
