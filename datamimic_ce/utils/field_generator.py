# # DATAMIMIC
# # Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# from collections.abc import Callable
# from typing import Any, TypeVar

# from datamimic_ce.entities.entity_util import FieldGenerator

# T = TypeVar("T")  # Define a type variable for generic typing


# class DictFieldGenerator(FieldGenerator[dict[str, Any]]):
#     """
#     A specialized FieldGenerator for generating dictionary field values.

#     This class extends the base FieldGenerator to work specifically with dictionary values.
#     """

#     def __init__(self, generator_fn: Callable[..., dict[str, Any]]):
#         """
#         Initialize the DictFieldGenerator with a generator function.

#         Args:
#             generator_fn: A function that generates dictionary values when called
#         """
#         super().__init__(generator_fn)


# class StringFieldGenerator(FieldGenerator[str]):
#     """
#     A specialized FieldGenerator for generating string field values.

#     This class extends the base FieldGenerator to work specifically with string values.
#     """

#     def __init__(self, generator_fn: Callable[..., str]):
#         """
#         Initialize the StringFieldGenerator with a generator function.

#         Args:
#             generator_fn: A function that generates string values when called
#         """
#         super().__init__(generator_fn)
