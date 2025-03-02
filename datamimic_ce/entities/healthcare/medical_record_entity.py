# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Medical Record Entity.

This module is a wrapper for the medical_record_entity package.
"""

from datamimic_ce.entities.healthcare.medical_record_entity.core import MedicalRecordEntity
from datamimic_ce.entities.healthcare.medical_record_entity.data_loader import MedicalRecordDataLoader

__all__ = ["MedicalRecordEntity", "MedicalRecordDataLoader"]
