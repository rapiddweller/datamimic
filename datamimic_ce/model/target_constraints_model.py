# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pydantic import BaseModel


class TargetConstraintsModel(BaseModel):
    """
    Model representing target constraints that are applied after data generation,
    just before exporting or finalizing the output. Target constraints provide an
    additional validation or transformation layer to ensure that the synthetic data
    meets specific business or export requirements.

    Example:
        <targetConstraints>
            <rule if="credit_limit >= 25000" then="approval_status = 'Approved'" />
            <rule if="credit_limit < 25000" then="approval_status = 'Review'" />
            <rule if="credit_limit <= 5000 and interest_rate >= 0.12" then="approval_status = 'Denied'" />
        </targetConstraints>
    """

    pass
