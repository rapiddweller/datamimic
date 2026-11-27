# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def build_executions(monkeypatch):
    """Record real executor calls without replacing the executor with a stub."""
    from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor

    original = CeBoundedExecutor.execute
    calls = []

    def recorded(executor, request):
        calls.append(request)
        return original(executor, request)

    monkeypatch.setattr(CeBoundedExecutor, "execute", recorded)
    return calls
