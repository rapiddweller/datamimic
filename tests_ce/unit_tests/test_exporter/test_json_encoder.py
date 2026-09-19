# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The JSON exporter must serialize every first-class engine value type. A descriptor
that lints and dry-runs clean must not crash on the real export (<key type="decimal">
with target="JSON" did exactly that before the Decimal branch existed)."""

import json
from datetime import date, datetime
from decimal import Decimal

from datamimic_ce.exporters.json_exporter import DateTimeEncoder


def test_encoder_handles_engine_value_types() -> None:
    row = {
        "balance": Decimal("228956.4"),
        "opened": date(2025, 3, 1),
        "booked_at": datetime(2025, 3, 1, 9, 30),
        "payload": b"\x01\x02",
    }
    out = json.loads(json.dumps(row, cls=DateTimeEncoder))
    assert out["balance"] == 228956.4
    assert out["opened"] == "2025-03-01"
    assert out["booked_at"] == "2025-03-01T09:30:00"
    assert out["payload"]  # base64 text
