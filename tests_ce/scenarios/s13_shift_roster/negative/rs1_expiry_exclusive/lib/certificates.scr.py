# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""RS1: the status of a certification on one day, used by suitability and by output validation."""

import datetime  # the module, as scripts see it: a library name shadows the script global of the same name
from collections.abc import Mapping, Sequence
from enum import StrEnum

Row = Mapping[str, object]


class CertificateStatus(StrEnum):
    VALID = "valid"
    MISSING = "missing"
    NOT_YET_ISSUED = "not_yet_issued"
    NO_EXPIRY_DATE = "no_expiry_date"
    EXPIRED = "expired"


def _holding_status(holding: Row, day: datetime.date) -> CertificateStatus:
    issued_on = holding["issued_on"]
    expires_on = holding["expires_on"]
    if not isinstance(issued_on, datetime.date) or day < issued_on:
        return CertificateStatus.NOT_YET_ISSUED
    if not isinstance(expires_on, datetime.date):
        return CertificateStatus.NO_EXPIRY_DATE  # a missing expiry date is not unlimited validity
    return CertificateStatus.VALID if day < expires_on else CertificateStatus.EXPIRED  # the expiry date is valid


def certificate_status(holdings: Sequence[Row], staff_id: str, cert_code: str, day: datetime.date) -> str:
    """The status of the person's certification on ``day``; one valid holding is enough. A row holds the value."""
    statuses = [
        _holding_status(holding, day)
        for holding in holdings
        if holding["staff_id"] == staff_id and holding["cert_code"] == cert_code
    ]
    if CertificateStatus.VALID in statuses:
        return CertificateStatus.VALID.value
    return statuses[0].value if statuses else CertificateStatus.MISSING.value


def valid_certificates(holdings: Sequence[Row], staff_id: str, day: datetime.date) -> list[str]:
    """The certification codes the person holds validly on ``day`` (RS1, and the lead holders of RS4)."""
    codes = sorted({str(holding["cert_code"]) for holding in holdings if holding["staff_id"] == staff_id})
    return [code for code in codes if certificate_status(holdings, staff_id, code, day) == CertificateStatus.VALID]


def lead_holders(
    roster: Sequence[Row], holdings: Sequence[Row], slot_id: str, lead_cert: str, day: datetime.date
) -> int:
    """RS4: the number of staff in the slot who hold the lead certification validly on ``day``."""
    return sum(
        certificate_status(holdings, str(row["staff_id"]), lead_cert, day) == CertificateStatus.VALID
        for row in roster
        if row["slot_id"] == slot_id
    )
