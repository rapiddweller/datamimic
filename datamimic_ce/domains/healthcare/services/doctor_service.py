# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor service.

This module provides a service for working with Doctor entities.
"""

import json
import os
from typing import Any, ClassVar

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.healthcare.generators.doctor_generator import DoctorGenerator
from datamimic_ce.domains.healthcare.models.doctor import Doctor
from datamimic_ce.logger import logger
from datamimic_ce.utils.domain_class_util import DomainClassUtil


class DoctorService(BaseDomainService[Doctor]):
    """Service for working with Doctor entities.

    This class provides methods for generating, exporting, and working with
    Doctor entities.
    """

    def __init__(self, dataset: str | None = None) -> None:
        super().__init__(DoctorGenerator(dataset=dataset), Doctor)
