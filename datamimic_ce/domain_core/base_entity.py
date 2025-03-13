# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from abc import ABC, abstractmethod
from typing import Any


class BaseEntity(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary."""
        raise NotImplementedError("Subclasses must implement this method.") 
