# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pydantic import BaseModel


class SourceConstraintsModel(BaseModel):
    """
    Model representing source constraints for filtering input source data
    before synthetic data generation. Source constraints define rules that
    determine which records should be included or assigned specific attributes
    before processing.

    Example:
        <sourceConstraints>
            <rule if="credit_score < 600" then="risk_profile == 'High'" />
            <rule if="credit_score >= 600 and credit_score < 750" then="risk_profile == 'Medium'" />
            <rule if="credit_score >= 750" then="risk_profile == 'Low'" />
        </sourceConstraints>
    """

    pass
