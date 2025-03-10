# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC
from typing import Any, ClassVar


class BaseDomainGenerator(ABC):
    """
    Base class for all domain generators.
    """
    _LOADED_DATA_CACHE: ClassVar[dict[str, Any]] = {}

    # Regional fallbacks for countries
    _REGIONAL_FALLBACKS: dict[str, tuple[str, ...]] = {
        # Western Europe fallbacks
        "DE": ("AT", "CH", "LU"),  # German-speaking
        "FR": ("BE", "CH", "LU", "MC"),  # French-speaking
        "IT": ("CH", "SM", "VA"),  # Italian-speaking
        "NL": ("BE", "LU"),  # Dutch-speaking
        # Nordic fallbacks
        "SE": ("NO", "DK", "FI"),  # Scandinavian
        "NO": ("SE", "DK", "FI"),
        "DK": ("NO", "SE", "DE"),
        "FI": ("SE", "EE"),
        # Eastern Europe fallbacks
        "PL": ("CZ", "SK", "DE"),
        "CZ": ("SK", "PL", "AT"),
        "SK": ("CZ", "PL", "HU"),
        "HU": ("SK", "RO", "AT"),
        # Balkan fallbacks
        "BA": ("HR", "RS", "SI"),  # Bosnia fallbacks
        "HR": ("SI", "BA", "AT"),
        "RS": ("BA", "BG", "RO"),
        # English-speaking fallbacks
        "US": ("CA", "GB", "AU"),
        "GB": ("IE", "US", "CA"),
        "CA": ("US", "GB"),
        "AU": ("NZ", "GB", "US"),
        "NZ": ("AU", "GB", "US"),
    }

