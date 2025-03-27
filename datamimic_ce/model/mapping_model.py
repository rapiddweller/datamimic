# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pydantic import BaseModel


class MappingModel(BaseModel):
    """
    Model representing mapping rules that transform selected records during
    the synthetic data generation process. Mapping rules define explicit attribute
    modifications based on conditions after the initial filtering.

    Example:
        <mapping>
            <rule if="risk_profile == 'High'" then="interest_rate = 0.15"/>
            <rule if="risk_profile == 'Medium'" then="interest_rate = 0.10"/>
            <rule if="risk_profile == 'Low'" then="interest_rate = 0.05"/>
        </mapping>
    """

    pass
